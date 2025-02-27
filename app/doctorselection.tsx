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

    // Then navigate to the new page
    router.push("/chat/physician");
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
                          className={`w-5 h-5 ${i < Math.floor(doctor.rating) ? "text-yellow-400" : "text-gray-400"}`}
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.693 5.097h5.35c.969 0 1.372 1.24.588 1.768l-4.314 3.14 1.634 5.365c.259.855-.687 1.56-1.33 1.014l-4.2-3.145-4.2 3.145c-.642.547-1.588-.159-1.33-1.014l1.634-5.365-4.314-3.14c-.784-.528-.381-1.768.588-1.768h5.35l1.693-5.097z" />
                        </svg>
                      ))}
                    </div>
                    <span className="text-white text-sm">({doctor.reviewCount} reviews)</span>
                  </div>
                  
                  {/* Bio */}
                  <p className="text-gray-300 text-sm">{doctor.bio}</p>
                  
                  {/* Start consultation button */}
                  <button
                    onClick={startConsultation}
                    className="bg-blue-600 text-white font-semibold py-2 px-4 rounded-lg mt-4 w-full hover:bg-blue-500 transition"
                  >
                    Start Consultation
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DoctorSelection;
