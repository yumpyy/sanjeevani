"use client"
import { useEffect, useState, useRef, useCallback } from "react";
import InteractiveAvatar from "../../../components/InteractiveAvatar";
import { motion, AnimatePresence } from "framer-motion";

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

  // Start avatar session as soon as page is loaded
  useEffect(() => {
    const startAvatarSession = async () => {
      if (avatarRef.current) {
        await avatarRef.current.startSession("73c84e2b886940099c5793b085150f2f", "en-US");
      }
    };

    startAvatarSession();

    return () => {
      if (avatarRef.current) {
        avatarRef.current.endSession();
      }
    };
  }, []);

  // Auto-scroll to the latest message
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
      // First request with age, sex, and symptoms
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
      // Continuing the conversation
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

  // Trigger speaking for new messages
  useEffect(() => {
    const speakNextUnspokenMessage = async () => {
      if (isSpeaking || !avatarRef.current) return;
      
      // Find the next unspoken bot message
      for (let i = lastSpokenMessageIndex.current + 1; i < messages.length; i++) {
        const msg = messages[i];
        if (msg.sender === "bot" && !msg.spoken) {
          setIsSpeaking(true);
          lastSpokenMessageIndex.current = i;
          
          // Mark the message as spoken in the state
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
    <div className="flex h-screen bg-gray-100 overflow-hidden">
      {/* Avatar Section */}
      <div className={`transition-all duration-500 ease-in-out ${isMinimized ? 'w-full' : 'w-full md:w-3/4'} relative bg-black`}>
        <InteractiveAvatar ref={avatarRef} />
        
        {/* Floating Chat Button */}
        {isMinimized && (
          <motion.button
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", stiffness: 260, damping: 20 }}
            onClick={toggleMinimize}
            className="fixed bottom-6 right-6 bg-blue-600 hover:bg-blue-700 text-white p-4 rounded-full shadow-xl z-50 transition-colors duration-300"
            aria-label="Open chat"
            style={{
              boxShadow: "0 10px 25px -5px rgba(59, 130, 246, 0.5), 0 8px 10px -6px rgba(59, 130, 246, 0.3)"
            }}
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
          </motion.button>
        )}
      </div>

      {/* Floating Translucent Chat Panel */}
      <AnimatePresence>
        {!isMinimized && (
          <motion.div 
            initial={{ opacity: 0, x: 100 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 100 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
            className="fixed md:absolute top-0 right-0 bottom-0 w-full md:w-1/3 lg:w-1/4 flex flex-col z-40"
            style={{
              background: "rgba(255, 255, 255, 0.85)",
              backdropFilter: "blur(10px)",
              WebkitBackdropFilter: "blur(10px)",
              boxShadow: "-10px 0 25px rgba(0, 0, 0, 0.1)"
            }}
          >
            <div className="flex justify-between items-center px-6 py-4 border-b border-gray-200 bg-white bg-opacity-80">
              <h2 className="text-xl font-medium text-gray-800">Medical Consultation</h2>
              <button 
                onClick={toggleMinimize}
                className="text-gray-600 hover:text-gray-800 transition-colors"
                aria-label="Minimize chat"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </div>
            
            <div className="flex-grow overflow-y-auto p-4 space-y-2">
              {/* Messages */}
              {messages.map((msg, index) => (
                <motion.div 
                  key={index} 
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3 }}
                  className={`p-4 rounded-2xl my-3 max-w-[85%] ${
                    msg.sender === "user" ? 
                      "bg-blue-600 text-white ml-auto" : 
                      "bg-white text-gray-800 mr-auto shadow-md"
                  }`}
                  style={{
                    boxShadow: msg.sender === "user" ? 
                      "0 4px 6px -1px rgba(59, 130, 246, 0.2), 0 2px 4px -1px rgba(59, 130, 246, 0.1)" : 
                      "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)"
                  }}
                >
                  {msg.text}
                  {msg.sender === "bot" && msg.spoken && (
                    <div className="text-xs text-gray-500 mt-1 flex items-center gap-1">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15.536a5 5 0 001.414 1.414m2.828-2.828a3 3 0 00-4.242-4.243" />
                      </svg>
                      <span>Spoken</span>
                    </div>
                  )}
                </motion.div>
              ))}
              <div ref={messagesEndRef} />
              
              {/* Speaking Indicator */}
              {isSpeaking && (
                <motion.div 
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="py-2 px-4 bg-blue-50 text-blue-700 rounded-full text-sm inline-flex items-center gap-2 mx-auto"
                >
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: "0s" }}></span>
                    <span className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }}></span>
                    <span className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: "0.4s" }}></span>
                  </div>
                  <span>Avatar speaking</span>
                </motion.div>
              )}
            </div>

            {/* Age and Sex Input - Step 0 */}
            {!sessionId && step === 0 && (
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4 }}
                className="bg-white p-6 m-4 rounded-2xl shadow-lg"
              >
                <h3 className="text-lg font-medium text-gray-800 mb-4">Patient Information</h3>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Age</label>
                    <select 
                      onChange={(e) => setAge(parseInt(e.target.value, 10))} 
                      defaultValue=""
                      className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
                    >
                      <option value="" disabled>Select your age</option>
                      {[...Array(100).keys()].map((n) => (
                        <option key={n} value={n}>{n}</option>
                      ))}
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Sex</label>
                    <select 
                      onChange={(e) => setSex(e.target.value)} 
                      defaultValue=""
                      className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
                    >
                      <option value="" disabled>Select your sex</option>
                      <option value="male">Male</option>
                      <option value="female">Female</option>
                    </select>
                  </div>
                </div>
                
                <button 
                  onClick={() => setStep(1)}
                  disabled={age === null || sex === null}
                  className={`w-full py-3 mt-6 rounded-lg text-white font-medium transition-all ${
                    age !== null && sex !== null ?
                      'bg-blue-600 hover:bg-blue-700 shadow-md hover:shadow-lg transform hover:-translate-y-1' :
                      'bg-gray-300 cursor-not-allowed'
                  }`}
                  style={{
                    boxShadow: age !== null && sex !== null ? 
                      "0 4px 6px -1px rgba(59, 130, 246, 0.3), 0 2px 4px -1px rgba(59, 130, 246, 0.2)" : 
                      "none"
                  }}
                >
                  Continue
                </button>
              </motion.div>
            )}

            {/* Chat Input - Step 1 */}
            {step === 1 && !isComplete && (
              <motion.form 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                onSubmit={handleSubmit} 
                className="p-4 bg-white bg-opacity-90 border-t border-gray-200"
              >
                <div className="flex items-center space-x-2">
                  <div className="relative flex-grow">
                    <input
                      type="text"
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      className="w-full pl-4 pr-10 py-3 bg-gray-100 rounded-full border-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all"
                      placeholder={isSpeaking ? "Avatar is speaking..." : "Describe your symptoms..."}
                      disabled={isComplete || isSpeaking}
                    />
                    <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex gap-2">
                      {/* Image Upload Button */}
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
                          className={`p-2 rounded-full text-gray-500 hover:text-blue-600 hover:bg-blue-50 cursor-pointer transition-colors ${
                            isComplete || isSpeaking ? 'opacity-50 cursor-not-allowed' : ''
                          }`}
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                          </svg>
                        </label>
                        {imageData && (
                          <div className="absolute -top-10 right-0 bg-white p-2 rounded-lg shadow-md">
                            <div className="text-xs text-green-600 flex items-center gap-1">
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                              </svg>
                              Image uploaded
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Send Button */}
                      <button 
                        type="submit" 
                        className={`p-2 rounded-full ${
                          isComplete || isSpeaking || !input.trim() ? 
                            'text-gray-400 cursor-not-allowed' : 
                            'text-blue-600 hover:bg-blue-50 transition-colors'
                        }`}
                        disabled={isComplete || isSpeaking || !input.trim()}
                      >
                        <svg 
                          xmlns="http://www.w3.org/2000/svg" 
                          className="h-5 w-5" 
                          fill="none" 
                          viewBox="0 0 24 24" 
                          stroke="currentColor"
                        >
                          <path 
                            strokeLinecap="round" 
                            strokeLinejoin="round" 
                            strokeWidth={2} 
                            d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" 
                          />
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>
              </motion.form>
            )}
            
            {/* Consultation Complete */}
            {isComplete && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="m-4 p-6 bg-gradient-to-br from-green-50 to-blue-50 rounded-2xl shadow-lg border border-green-100"
              >
                <div className="flex items-center gap-3 mb-4">
                  <div className="bg-green-100 p-2 rounded-full">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-medium text-gray-800">Consultation Complete</h3>
                </div>
                <p className="text-gray-600 mb-4">Thank you for using our virtual medical consultation service. Your recommendations have been provided above.</p>
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
                  className="w-full py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all shadow-md hover:shadow-lg transform hover:-translate-y-1"
                >
                  Start New Consultation
                </button>
              </motion.div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
