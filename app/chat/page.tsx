"use client";

import React, { useState, useRef, useEffect } from "react";

const ChatPage = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [chatActive, setChatActive] = useState(true);
  const [isListening, setIsListening] = useState(false);
  const messageEndRef = useRef(null);
  const recognitionRef = useRef(null);

  // Scroll to the most recent message
  useEffect(() => {
    messageEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Clean up speech recognition on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, []);

  const sendMessage = () => {
    if (input.trim() === "") return;

    const userMessage = { text: input, sender: "user", timestamp: new Date() };
    setMessages((prevMessages) => [userMessage, ...prevMessages]);
    setInput("");

    // Simulating a bot response after a short delay
    setTimeout(() => {
      const botMessage = { 
        text: "I'm a bot! How can I help?", 
        sender: "bot", 
        timestamp: new Date() 
      };
      setMessages((prevMessages) => [botMessage, ...prevMessages]);
    }, 1000);
  };

  const toggleChat = () => setChatActive((prevState) => !prevState);

  const handleVoiceInput = () => {
    if (!window.SpeechRecognition && !window.webkitSpeechRecognition) {
      alert("Speech Recognition not supported in this browser.");
      return;
    }

    if (!recognitionRef.current) {
      recognitionRef.current = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
      recognitionRef.current.lang = "en-US";
      recognitionRef.current.continuous = true;
      recognitionRef.current.interimResults = true;

      recognitionRef.current.onstart = () => setIsListening(true);
      recognitionRef.current.onend = () => setIsListening(false);
      recognitionRef.current.onresult = (event) => {
        const lastResultIndex = event.results.length - 1;
        const transcript = event.results[lastResultIndex][0].transcript;
        setInput(transcript);
      };
      
      recognitionRef.current.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
      };
    }

    if (isListening) {
      recognitionRef.current.stop();
    } else {
      recognitionRef.current.start();
    }
  };

  return (
    <div className="relative h-screen w-full flex items-center justify-center">
      {/* Video Background */}
      <video autoPlay loop muted className="absolute top-0 left-0 w-full h-full object-cover">
        <source src="/bg.mp4" type="video/mp4" />
      </video>

      {/* Dark Overlay */}
      <div className="absolute inset-0 bg-black bg-opacity-50"></div>

      {/* Chat Container */}
      <div className={`relative flex flex-col w-full max-w-2xl h-[100vh] rounded-lg shadow-xl p-6 ${!chatActive ? 'hidden' : ''}`}>
        {/* Chat Messages */}
        <div className="flex-grow flex flex-col-reverse overflow-y-auto p-4 space-y-2 scrollbar-hide mb-4">
          <div ref={messageEndRef} />
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`relative px-4 py-2 rounded-lg max-w-[75%] text-white text-lg shadow-md transition-opacity duration-500 ${
                msg.sender === "user"
                  ? "bg-blue-500 self-end animate-fadeIn"
                  : "bg-gray-700 self-start animate-fadeIn"
              }`}
              style={{ opacity: 1 - index * 0.05 > 0.5 ? 1 - index * 0.05 : 0.5 }}
            >
              <div>{msg.text}</div>
              <div className="text-xs mt-1 opacity-60">
                {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </div>
            </div>
          ))}
        </div>

        {/* Input Field Container with Buttons */}
        <div className="flex items-center space-x-2">
          {/* Chat Toggle Button (Left Side) */}
          <button
            onClick={toggleChat}
            className="bg-red-500 text-white p-2 rounded-lg hover:bg-red-600 transition flex-shrink-0"
            aria-label="Toggle chat"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
            </svg>
          </button>

          {/* Input Field */}
          <div className="flex-1 bg-white bg-opacity-20 p-2 rounded-lg shadow-lg flex items-center">
            <input
              type="text"
              className="flex-1 p-3 text-white bg-transparent outline-none placeholder-gray-300"
              placeholder="Type a message..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            />
            
            {/* Send Button */}
            <button
              onClick={sendMessage}
              disabled={!input.trim()}
              className={`p-2 rounded-full mx-1 ${input.trim() ? 'text-blue-400 hover:bg-blue-100 hover:bg-opacity-20' : 'text-gray-400'}`}
              aria-label="Send message"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
          </div>

          {/* Voice Input Button (Right Side) */}
          <button
            onClick={handleVoiceInput}
            className={`p-2 rounded-lg flex-shrink-0 transition ${
              isListening ? 'bg-red-500 text-white hover:bg-red-600' : 'bg-green-500 text-white hover:bg-green-600'
            }`}
            aria-label={isListening ? "Stop voice input" : "Start voice input"}
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                d={isListening 
                  ? "M21 12a9 9 0 11-18 0 9 9 0 0118 0z M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" 
                  : "M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"} 
              />
            </svg>
          </button>
        </div>
      </div>

      {/* Floating Button when chat is inactive */}
      {!chatActive && (
        <button
          onClick={toggleChat}
          className="fixed bottom-6 right-6 bg-blue-500 text-white p-4 rounded-full hover:bg-blue-600 transition shadow-lg z-10"
          aria-label="Open chat"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
        </button>
      )}
    </div>
  );
};

export default ChatPage;
