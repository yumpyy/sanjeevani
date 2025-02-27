"use client"
import { useEffect, useState, useRef, useCallback } from "react";
import InteractiveAvatar from "@/components/InteractiveAvatar";
import { motion, AnimatePresence } from "framer-motion"; // Added for animations

const BASE_URL = "http://127.0.0.1:8000";

export default function Chatbot() {
  const avatarRef = useRef<any>(null);
  const [messages, setMessages] = useState<{ sender: string; text: string; spoken?: boolean }[]>([]);
  const [input, setInput] = useState<string>("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isComplete, setIsComplete] = useState<boolean>(false);
  const [age, setAge] = useState<number | null>(null);
  const [sex, setSex] = useState<string | null>(null);
  const [step, setStep] = useState<number>(0);
  const [imageData, setImageData] = useState<string>("");
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
  const [isMinimized, setIsMinimized] = useState<boolean>(false);
  const lastSpokenMessageIndex = useRef<number>(-1);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // start avatar session as soon as page is loaded
  useEffect(() => {
    const startAvatarSession = async () => {
      if (avatarRef.current) {
        // starting the avatar session with appropriate avatar id and language
        await avatarRef.current.startSession("73c84e2b886940099c5793b085150f2f", "en-US");
      }
    };

    startAvatarSession();

    return () => {
      if (avatarRef.current) {
        avatarRef.current.endSession();
      }
    };
  }, []); // empty dependency array ensures it runs only once on mount

  // auto-scroll to the latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const processResponse = useCallback(async (data: any) => {
    if (!avatarRef.current) {
      console.error("Avatar session not started.");
      return;
    }

    const messagesToAdd = [];

    if (data.diagnosis_complete) {
      const res = await fetch(`${BASE_URL}/diagnosis/${sessionId}/recommendation`);
      const recommendation = await res.json();

      messagesToAdd.push(
        { sender: "bot", text: recommendation.recommendation, spoken: false },
      );

      setIsComplete(true);
    } else {
      messagesToAdd.push({ sender: "bot", text: data.response, spoken: false });
    }

    setMessages((prev) => [...prev, ...messagesToAdd]);
  }, [sessionId]);

  const sendMessage = useCallback(async (message: string) => {
    setMessages((prev) => [...prev, { sender: "user", text: message }]);

    if (!sessionId) {
      // first request with age, sex, and symptoms
      const payload = { age: parseInt(age as string, 10), sex, symptoms: message, image_data: imageData };
      const res = await fetch(`${BASE_URL}/diagnosis/physician/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      setSessionId(data.session_id);
      processResponse(data);
    } else {
      // continuing the conversation
      const payload = { clarification_questions: { [messages.at(-1)?.text]: message } };
      const res = await fetch(`${BASE_URL}/diagnosis/${sessionId}/continue`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      processResponse(data);
    }
  }, [sessionId, age, sex, imageData, messages, processResponse]);

  // this useeffect will trigger every time a new message is added to the messages state
  useEffect(() => {
    const speakNextUnspokenMessage = async () => {
      if (isSpeaking || !avatarRef.current) return;
      
      // find the next unspoken bot message
      for (let i = lastSpokenMessageIndex.current + 1; i < messages.length; i++) {
        const msg = messages[i];
        if (msg.sender === "bot" && !msg.spoken) {
          setIsSpeaking(true);
          lastSpokenMessageIndex.current = i;
          
          // mark the message as spoken in the state
          setMessages(prev => {
            const updated = [...prev];
            updated[i] = { ...updated[i], spoken: true };
            return updated;
          });
          
          try {
            await avatarRef.current.speakText(msg.text);
          } catch (error) {
            console.error("Error speaking text:", error);
          } finally {
            setIsSpeaking(false);
          }
          
          break;
        }
      }
    };
    
    speakNextUnspokenMessage();
  }, [messages, isSpeaking]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      sendMessage(input);
      setInput("");
    }
  };

  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    const reader = new FileReader();
    reader.onloadend = () => setImageData(reader.result?.toString().split(",")[1] || "");
    if (file) reader.readAsDataURL(file);
  };

  const toggleMinimize = () => {
    setIsMinimized(!isMinimized);
  };

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Avatar Section */}
      <div className={`transition-all duration-300 ease-in-out ${isMinimized ? 'w-full' : 'w-3/4'} relative bg-black`}>
        <InteractiveAvatar ref={avatarRef} />
        
        {/* Minimize/Maximize Toggle */}
        <button 
          onClick={toggleMinimize}
          className="absolute top-4 right-4 z-10 bg-white bg-opacity-80 rounded-full p-2 shadow-md"
          aria-label={isMinimized ? "Show chat" : "Hide chat"}
        >
          <svg 
            xmlns="http://www.w3.org/2000/svg" 
            className="h-6 w-6" 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d={isMinimized ? 
                "M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" : 
                "M15 19l-7-7 7-7"} 
            />
          </svg>
        </button>
      </div>

      {/* Chat Section */}
      <AnimatePresence>
        {!isMinimized && (
          <motion.div 
            initial={{ opacity: 0, x: 100 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 100 }}
            transition={{ duration: 0.3 }}
            className="w-1/4 flex flex-col p-4 border-l bg-white shadow-lg"
          >
            <div className="flex justify-between items-center mb-4 pb-2 border-b">
              <h2 className="text-xl font-semibold text-gray-800">Medical Consultation</h2>
              <button 
                onClick={toggleMinimize}
                className="text-gray-500 hover:text-gray-700"
                aria-label="Minimize chat"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M4.293 15.707a1 1 0 010-1.414L10.586 8 4.293 1.707a1 1 0 011.414-1.414l7 7a1 1 0 010 1.414l-7 7a1 1 0 01-1.414 0z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
            
            <div className="flex-grow overflow-y-auto p-2 space-y-2 mb-4">
              {messages.map((msg, index) => (
                <motion.div 
                  key={index} 
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3 }}
                  className={`p-3 rounded-lg my-2 shadow-sm max-w-[85%] ${
                    msg.sender === "user" ? 
                      "bg-blue-100 ml-auto rounded-br-none" : 
                      "bg-gray-100 mr-auto rounded-bl-none"
                  }`}
                >
                  {msg.text}
                  {msg.sender === "bot" && msg.spoken && (
                    <div className="text-xs text-gray-500 mt-1">✓ Spoken</div>
                  )}
                </motion.div>
              ))}
              <div ref={messagesEndRef} />
              
              {isSpeaking && (
                <div className="py-2 px-3 bg-blue-50 text-blue-700 rounded-md text-sm">
                  Avatar is speaking...
                </div>
              )}
            </div>

            {/* Age and Sex Input - Step 0 */}
            {!sessionId && step === 0 && (
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="flex flex-col space-y-3 bg-gray-50 p-4 rounded-lg"
              >
                <h3 className="text-lg font-medium text-gray-700">Please provide your details</h3>
                
                <div className="space-y-1">
                  <label className="block text-sm font-medium text-gray-700">Age:</label>
                  <select 
                    onChange={(e) => setAge(parseInt(e.target.value, 10))} 
                    defaultValue=""
                    className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="" disabled>Select your age</option>
                    {[...Array(100).keys()].map((n) => (
                      <option key={n} value={n}>{n}</option>
                    ))}
                  </select>
                </div>
                
                <div className="space-y-1">
                  <label className="block text-sm font-medium text-gray-700">Sex:</label>
                  <select 
                    onChange={(e) => setSex(e.target.value)} 
                    defaultValue=""
                    className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="" disabled>Select your sex</option>
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                  </select>
                </div>
                
                <button 
                  onClick={() => setStep(1)}
                  disabled={age === null || sex === null}
                  className={`w-full py-2 rounded text-white font-medium transition ${
                    age !== null && sex !== null ?
                      'bg-blue-500 hover:bg-blue-600' :
                      'bg-gray-400 cursor-not-allowed'
                  }`}
                >
                  Next
                </button>
              </motion.div>
            )}

            {/* Chat Input - Step 1 */}
            {step === 1 && !isComplete && (
              <motion.form 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                onSubmit={handleSubmit} 
                className="flex space-x-2 mt-2"
              >
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  className="flex-grow border border-gray-300 p-2 rounded-l-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder={isSpeaking ? "Avatar is speaking..." : "Describe your symptoms..."}
                  disabled={isComplete || isSpeaking}
                />
                <button 
                  type="submit" 
                  className={`bg-blue-500 text-white px-4 py-2 rounded-r-lg ${
                    isComplete || isSpeaking || !input.trim() ? 
                      'opacity-50 cursor-not-allowed' : 
                      'hover:bg-blue-600'
                  }`}
                  disabled={isComplete || isSpeaking || !input.trim()}
                >
                  Send
                </button>
                <div className="relative">
                  <input 
                    type="file" 
                    onChange={handleImageUpload} 
                    accept="image/*" 
                    className="hidden" 
                    id="upload" 
                    disabled={isComplete || isSpeaking}
                  />
                  <label 
                    htmlFor="upload" 
                    className={`bg-gray-200 text-gray-700 p-2 rounded-lg cursor-pointer flex items-center justify-center shadow-sm hover:bg-gray-300 ${
                      isComplete || isSpeaking ? 'opacity-50 cursor-not-allowed' : ''
                    }`}
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                  </label>
                  {imageData && (
                    <div className="absolute -top-10 right-0 bg-white p-1 rounded shadow-md">
                      <div className="text-xs text-green-600">Image uploaded ✓</div>
                    </div>
                  )}
                </div>
              </motion.form>
            )}
            
            {/* Consultation Complete */}
            {isComplete && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="mt-4 p-4 bg-green-50 rounded-lg border border-green-200"
              >
                <h3 className="text-lg font-medium text-green-800">Consultation Complete</h3>
                <p className="text-green-600 mt-1">Thank you for using our medical consultation service.</p>
                <button 
                  onClick={() => {
                    setMessages([]);
                    setIsComplete(false);
                    setStep(0);
                    setSessionId(null);
                    setAge(null);
                    setSex(null);
                    setImageData("");
                    lastSpokenMessageIndex.current = -1;
                  }}
                  className="mt-3 bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 transition"
                >
                  Start New Consultation
                </button>
              </motion.div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Minimized Chat Button */}
      {isMinimized && (
        <motion.button
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0, opacity: 0 }}
          onClick={toggleMinimize}
          className="fixed bottom-6 right-6 bg-blue-500 text-white p-4 rounded-full shadow-lg z-10 hover:bg-blue-600 transition"
          aria-label="Open chat"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
        </motion.button>
      )}
    </div>
  );
}
