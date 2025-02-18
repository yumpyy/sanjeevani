"use client"
import { useEffect, useState, useRef } from "react";
import InteractiveAvatar from "@/components/InteractiveAvatar";
>>>>>>> a7ca718 (feat(ui): add avatar real-time interaction)

const BASE_URL = "http://127.0.0.1:8000";

export default function Chatbot() {
  const avatarRef = useRef<any>(null); // Use `any` since we're using a ref to the avatar component
  const [messages, setMessages] = useState<{ sender: string; text: string }[]>([]);
  const [input, setInput] = useState<string>("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isComplete, setIsComplete] = useState<boolean>(false);
  const [age, setAge] = useState<number | null>(null);
  const [sex, setSex] = useState<string | null>(null);
  const [step, setStep] = useState<number>(0);
  const [imageData, setImageData] = useState<string>("");

  // Start avatar session as soon as page is loaded
  useEffect(() => {
    const startAvatarSession = async () => {
      if (avatarRef.current) {
        // Starting the avatar session with appropriate avatar id and language
        await avatarRef.current.startSession("Ann_Doctor_Standing2_public", "en-US");
      }
    };

    startAvatarSession();

    return () => {
      if (avatarRef.current) {
        avatarRef.current.endSession();
      }
    };
  }, []); // Empty dependency array ensures it runs only once on mount

  const sendMessage = async (message: string) => {
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
  };

  const processResponse = async (data: any) => {
    if (!avatarRef.current) {
      console.error("Avatar session not started.");
      return;
    }

    const messagesToAdd = [];

    if (data.diagnosis_complete) {
      const res = await fetch(`${BASE_URL}/diagnosis/${sessionId}/recommendation`);
      const recommendation = await res.json();

      messagesToAdd.push(
        { sender: "bot", text: `Diagnosis: ${recommendation.diagnosis}` },
        { sender: "bot", text: `Recommended Medicines: ${recommendation.recommend_medicines.join(", ")}` },
        { sender: "bot", text: `Dosage: ${recommendation.dosage}` },
        { sender: "bot", text: `Side Effects: ${recommendation.potential_side_effects.join(", ")}` },
        { sender: "bot", text: `Contraindications: ${recommendation.contraindications.join(", ")}` },
        { sender: "bot", text: `Alternative Treatments: ${recommendation.alternative_treatments.join(", ")}` },
        { sender: "bot", text: `Emergency Aid: ${recommendation.emergency_aid || "Not provided"}` },
        { sender: "bot", text: `Consultation Required: ${recommendation.consultation_required ? "Yes" : "No"}` },
      );

      setIsComplete(true);
    } else {
      messagesToAdd.push({ sender: "bot", text: data.response });
    }

    setMessages((prev) => [...prev, ...messagesToAdd]);
  };

  // This useEffect will trigger every time a new message is added to the messages state
  useEffect(() => {
    // Speak the latest bot message (if it's not empty and is from the bot)
    const latestMessage = messages[messages.length - 1];
    if (latestMessage?.sender === "bot" && avatarRef.current) {
      avatarRef.current.speakText(latestMessage.text);
    }
  }, [messages]); // Trigger the effect whenever the messages array changes

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

  return (
    <div className="flex h-screen">
      {/* Avatar Section */}
      <div className="w-3/4 relative">
        <InteractiveAvatar ref={avatarRef} />
      </div>

      {/* Chat Section */}
      <div className="w-1/4 flex flex-col p-4 border-l bg-white">
        <div className="flex-grow overflow-y-auto p-2">
          {messages.map((msg, index) => (
            <div key={index} className={`p-2 rounded-lg my-1 ${msg.sender === "user" ? "bg-blue-200" : "bg-gray-200"}`}>
              {msg.text}
            </div>
          ))}
        </div>

        {/* Input Fields */}
        {!sessionId && step === 0 && (
          <div className="flex flex-col space-y-2">
            <label>Age:</label>
            <select onChange={(e) => setAge(parseInt(e.target.value, 10))} defaultValue="">
              {[...Array(100).keys()].map((n) => (
                <option key={n} value={n}>{n}</option>
              ))}
            </select>
            <label>Sex:</label>
            <select onChange={(e) => setSex(e.target.value)} defaultValue="">
              <option value="" disabled>Select your sex</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
            </select>
            <button onClick={() => setStep(1)}>Next</button>
          </div>
        )}

        {step === 1 && !isComplete && (
          <form onSubmit={handleSubmit} className="flex space-x-2 mt-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              className="flex-grow border p-2"
              placeholder="Type here..."
              disabled={isComplete}
            />
            <button type="submit" className="bg-blue-500 text-white px-4" disabled={isComplete}>Send</button>
            <input type="file" onChange={handleImageUpload} accept="image/*" className="hidden" id="upload" />
            <label htmlFor="upload" className="bg-gray-500 text-white px-4 cursor-pointer">📷</label>
          </form>
        )}
      </div>
    </div>
  );
}
