"use client";

import React, { useState } from "react";
import DoctorSelection from "./doctorselection";

const HeroSection = () => {
  const [isPopupOpen, setIsPopupOpen] = useState(false);

  return (
    <div className="relative h-screen w-full overflow-hidden">
      {/* Video Background */}
      <video autoPlay loop muted className="absolute top-0 left-0 w-full h-full object-cover">
        <source src="/bg.mp4" type="video/mp4" />
      </video>
      
      {/* Overlay */}
      <div className="absolute inset-0 bg-black bg-opacity-40"></div>
      
      {/* Navbar */}
      <nav className="absolute top-0 w-full flex justify-center items-center p-5 text-white z-10">
        <div className="absolute left-0 top-0 p-5">
          <img src="/logo.svg" alt="Logo" className="-rotate-45 h-24" />
        </div>
        <div className="flex items-center space-x-8">
          <a href="#about" className="hover:underline">About Us</a>
          <a href="#contact" className="hover:underline">Contact Us</a>
          <a href="#more" className="hover:underline">More Links</a>
        </div>
      </nav>
      
      {/* Hero Content */}
      <div className="relative flex flex-col items-center justify-center h-full text-white text-center px-4 z-10">
        <h1 className="text-4xl md:text-6xl font-bold">
          <span className="block">Your AI-Powered Doctor</span>
          <span className="block">
            At Your&nbsp;
            <img src="/heart.jpg" alt="Heart" className="inline-block mr-2 h-16 rounded-lg" />
            Service
          </span>
        </h1>
        <p className="mt-4 max-w-2xl text-lg">Experience the future of healthcare with our AI doctor, providing personalized medication prescriptions and consultations.</p>
        <button 
          onClick={() => setIsPopupOpen(true)}
          className="mt-6 bg-opacity-20 bg-white text-white px-6 py-3 rounded-full text-lg shadow-lg"
        >
          Get Started
        </button>
      </div>
      
      {/* Footer */}
      <footer className="absolute bottom-5 w-full text-center text-white z-10">
        <p>Terms and Conditions</p>
      </footer>

      {/* Doctor Selection Popup */}
      <DoctorSelection isOpen={isPopupOpen} onClose={() => setIsPopupOpen(false)} />
    </div>
  );
};

export default HeroSection;
