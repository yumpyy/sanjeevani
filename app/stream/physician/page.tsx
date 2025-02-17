"use client";

import { useState, useRef } from "react";
import InteractiveAvatar from "@/components/InteractiveAvatar";
import Bg_video from "@/components/background-vid";

const BASE_URL = "http://127.0.0.1:8000";

export default function Chatbot() {
  const avatarRef = useRef(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState(null);
  const [isComplete, setIsComplete] = useState(false);
  const [age, setAge] = useState(null);
  const [sex, setSex] = useState(null);
  const [step, setStep] = useState(0);
  const [imageData, setImageData] = useState("");

  const sendMessage = async (message) => {
    setMessages((prev) => [...prev, { sender: "user", text: message }]);
    if (!sessionId) {
      // First request with age, sex, and symptoms
      const payload = { age, sex, symptoms: message, image_data: imageData };
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

  const processResponse = async (data) => {
    if (data.diagnosis_complete) {
      const res = await fetch(`${BASE_URL}/diagnosis/${sessionId}/recommendation`);
      const recommendation = await res.json();
      setMessages((prev) => [...prev, { sender: "bot", text: recommendation.recommendation }]);
      setIsComplete(true);
    } else {
      setMessages((prev) => [...prev, { sender: "bot", text: data.response }]);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim()) {
      sendMessage(input);
      setInput("");
    }
  };

  const handleImageUpload = (event) => {
    const file = event.target.files[0];
    const reader = new FileReader();
    reader.onloadend = () => setImageData(reader.result.split(",")[1]);
    if (file) reader.readAsDataURL(file);
  };

  return (
    <div className="flex h-screen">
      {/* Avatar Section */}
      <div className="w-3/4 relative">
        <Bg_video />
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
            <select onChange={(e) => setAge(parseInt(e.target.value))}>
              {[...Array(100).keys()].map((n) => (
                <option key={n} value={n}>{n}</option>
              ))}
            </select>
            <label>Sex:</label>
            <select onChange={(e) => setSex(e.target.value)}>
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
