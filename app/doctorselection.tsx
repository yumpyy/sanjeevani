"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";

// Enhanced doctor data with more details and responsive images
const doctors = [
  {
    id: 1,
    name: "Dr. Sarah Johnson",
    specialty: "Cardiologist",
    image: "/oldwoman.jpg",
    bio: "Over 15 years of experience in cardiovascular care with a focus on preventative medicine.",
    rating: 4.9,
    reviewCount: 342,
  },
  {
    id: 2,
    name: "Dr. James Smith",
    specialty: "Neurologist",
    image: "/oldman.jpg",
    bio: "Board-certified neurologist specializing in cognitive disorders and headache management.",
    rating: 4.8,
    reviewCount: 289,
  },
  {
    id: 3,
    name: "Dr. Emily Davis",
    specialty: "Dermatologist",
    image: "/youngwoman.jpg",
    bio: "Expert in treating both medical and cosmetic skin conditions with the latest techniques.",
    rating: 4.7,
    reviewCount: 315,
  },
];

const DoctorSelection = ({ isOpen, onClose }) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loadedImages, setLoadedImages] = useState(new Set());
  const router = useRouter();
  
  // Refs for swipe detection
  const touchStartX = useRef(null);
  const touchEndX = useRef(null);
  
  // Update image loading status
  useEffect(() => {
    if (!isOpen) return;
    
    // Preload doctor images
    doctors.forEach((doctor) => {
      const img = new window.Image();
      img.src = doctor.image;
      img.onload = () => {
        setLoadedImages((prev) => {
          const newSet = new Set(prev);
          newSet.add(doctor.id);
          return newSet;
        });
      };
    });
    
    // Reset selection when opened
    setCurrentIndex(0);
  }, [isOpen]);
  
  // Handle keyboard navigation
  useEffect(() => {
    if (!isOpen) return;
    
    const handleKeydown = (e) => {
      switch (e.key) {
        case "ArrowLeft":
          goToPrevDoctor();
          break;
        case "ArrowRight":
          goToNextDoctor();
          break;
        case "Escape":
          onClose();
          break;
        case "Enter":
          if (doctors[currentIndex]) {
            startConsultation();
          }
          break;
      }
    };
    
    window.addEventListener("keydown", handleKeydown);
    return () => window.removeEventListener("keydown", handleKeydown);
  }, [isOpen, currentIndex, onClose]);

  // Navigation functions
  const goToNextDoctor = () => {
    setCurrentIndex((prevIndex) => {
      const nextIndex = prevIndex + 1;
      return nextIndex >= doctors.length ? 0 : nextIndex;
    });
  };

  const goToPrevDoctor = () => {
    setCurrentIndex((prevIndex) => {
      const prevDoctorIndex = prevIndex - 1;
      return prevDoctorIndex < 0 ? doctors.length - 1 : prevDoctorIndex;
    });
  };
  
  // Touch handlers for swipe
  const handleTouchStart = (e) => {
    touchStartX.current = e.touches[0].clientX;
  };
  
  const handleTouchMove = (e) => {
    touchEndX.current = e.touches[0].clientX;
  };
  
  const handleTouchEnd = () => {
    if (!touchStartX.current || !touchEndX.current) return;
    
    const diff = touchStartX.current - touchEndX.current;
    const threshold = 50;
    
    if (diff > threshold) {
      // Swiped left - go next
      goToNextDoctor();
    } else if (diff < -threshold) {
      // Swiped right - go prev
      goToPrevDoctor();
    }
    
    // Reset values
    touchStartX.current = null;
    touchEndX.current = null;
  };

  // Function to handle consultation start
  const startConsultation = () => {
    const selectedDoctor = doctors[currentIndex];
    console.log(`Starting consultation with ${selectedDoctor.name}`);
    
    // Close the selection modal first
    if (onClose) {
      onClose();
    }
    
    // Then navigate to the chat page
    router.push("/chat");
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 flex items-center justify-center bg-black/60 z-50 backdrop-blur-md p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className="relative w-full max-w-3xl bg-gradient-to-b from-slate-900 to-slate-800 rounded-2xl shadow-2xl overflow-hidden"
      >
        {/* Header with close button */}
        <div className="relative px-6 py-4 bg-slate-800 border-b border-slate-700 flex justify-between items-center">
          <h2 className="text-2xl font-semibold text-white">Select Your Healthcare Professional</h2>
          <button
            onClick={onClose}
            className="text-gray-300 hover:text-white transition-colors p-2 rounded-full hover:bg-slate-700"
            aria-label="Close dialog"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        {/* Progress indicator */}
        <div className="px-6 pt-4 flex justify-center">
          <div className="flex space-x-2">
            {doctors.map((_, index) => (
              <button
                key={index}
                onClick={() => setCurrentIndex(index)}
                className={`w-3 h-3 rounded-full transition-all duration-300 ${
                  index === currentIndex ? "bg-blue-500 w-8" : "bg-gray-600 hover:bg-gray-500"
                }`}
                aria-label={`Go to doctor ${index + 1}`}
              />
            ))}
          </div>
        </div>

        {/* Doctor cards carousel with simple touch handling */}
        <div 
          className="p-6 flex flex-col items-center"
          onTouchStart={handleTouchStart}
          onTouchMove={handleTouchMove}
          onTouchEnd={handleTouchEnd}
        >
          <div className="relative w-full h-[28rem] flex items-center justify-center">
            {doctors.map((doctor, index) => (
              <div 
                key={doctor.id}
                className={`absolute w-full flex flex-col md:flex-row items-center gap-8 bg-slate-800/60 rounded-xl p-6 transition-opacity duration-300 ${
                  index === currentIndex ? "opacity-100 z-10" : "opacity-0 z-0"
                }`}
              >
                {/* Doctor image with loading state */}
                <div className="relative w-64 h-72 rounded-lg overflow-hidden shadow-xl">
                  {!loadedImages.has(doctor.id) && (
                    <div className="absolute inset-0 flex items-center justify-center bg-slate-700">
                      <svg className="animate-spin h-12 w-12 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                    </div>
                  )}
                  <img
                    src={doctor.image}
                    alt={doctor.name}
                    className={`w-full h-full object-cover transition-opacity duration-300 ${
                      loadedImages.has(doctor.id) ? "opacity-100" : "opacity-0"
                    }`}
                  />
                  
                  {/* Specialty badge */}
                  <div className="absolute bottom-3 left-3 bg-blue-600 text-white text-sm font-medium py-1 px-3 rounded-full shadow-lg">
                    {doctor.specialty}
                  </div>
                </div>
                
                {/* Doctor info */}
                <div className="flex-1 flex flex-col items-center md:items-start space-y-4 text-center md:text-left">
                  <h3 className="text-2xl font-bold text-white">{doctor.name}</h3>
                  
                  {/* Rating */}
                  <div className="flex items-center space-x-2">
                    <div className="flex">
                      {[...Array(5)].map((_, i) => (
                        <svg
                          key={i}
                          className={`w-5 h-5 ${
                            i < Math.floor(doctor.rating) ? "text-yellow-400" : "text-gray-400"
                          }`}
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                        </svg>
                      ))}
                    </div>
                    <span className="text-white font-medium">{doctor.rating.toFixed(1)}</span>
                    <span className="text-gray-400">({doctor.reviewCount} reviews)</span>
                  </div>
                  
                  {/* Bio */}
                  <p className="text-gray-300 text-lg leading-relaxed">{doctor.bio}</p>
                  
                  {/* Doctor selection button */}
                  <button
                    onClick={startConsultation}
                    className="mt-6 group relative inline-flex items-center justify-center px-8 py-3 bg-gradient-to-r from-blue-500 to-blue-600 overflow-hidden text-white rounded-lg shadow-lg transition-all duration-300 hover:from-blue-600 hover:to-blue-700 focus:ring-2 focus:ring-blue-400 focus:ring-offset-2 focus:ring-offset-slate-900 focus:outline-none"
                  >
                    <span className="relative flex items-center">
                      Select & Start Consultation
                      <svg className="ml-2 h-5 w-5 transition-transform group-hover:translate-x-1" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                      </svg>
                    </span>
                  </button>
                </div>
              </div>
            ))}
            
            {/* Simple navigation buttons with explicit z-index */}
            <div className="absolute inset-0 flex justify-between items-center z-20">
              <button
                onClick={goToPrevDoctor}
                className="h-10 w-10 bg-white/10 hover:bg-white/20 text-white flex items-center justify-center rounded-full shadow-lg transition-colors ml-2"
                aria-label="Previous doctor"
              >
                <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              
              <button
                onClick={goToNextDoctor}
                className="h-10 w-10 bg-white/10 hover:bg-white/20 text-white flex items-center justify-center rounded-full shadow-lg transition-colors mr-2"
                aria-label="Next doctor"
              >
                <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>
          </div>
        </div>
        
        {/* Swipe hint */}
        <div className="text-center text-gray-400 text-sm pb-2">
          <p>Swipe left or right to browse doctors</p>
        </div>
        
        {/* Footer with additional info */}
        <div className="px-6 py-4 bg-slate-800/60 border-t border-slate-700 flex flex-col md:flex-row justify-between items-center text-sm text-gray-400">
          <p>Select a healthcare professional to begin your consultation</p>
          <p className="mt-2 md:mt-0">All consultations are private and secure</p>
        </div>
      </div>
    </div>
  );
};

export default DoctorSelection;