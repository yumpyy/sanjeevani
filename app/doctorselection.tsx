"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

const doctors = [
  { id: 1, name: "Dr. Sarah Johnson", specialty: "Cardiologist", image: "/oldwoman.jpg" },
  { id: 2, name: "Dr. James Smith", specialty: "Neurologist", image: "/oldman.jpg" },
  { id: 3, name: "Dr. Emily Davis", specialty: "Dermatologist", image: "/youngwoman.jpg" },
];

const DoctorSelection = ({ isOpen, onClose }) => {
  const [currentIndex, setCurrentIndex] = useState(0);

  const nextDoctor = () => {
    setCurrentIndex((prevIndex) => (prevIndex + 1) % doctors.length);
  };

  const prevDoctor = () => {
    setCurrentIndex((prevIndex) => (prevIndex - 1 + doctors.length) % doctors.length);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50 backdrop-blur-lg">
      <div className="relative w-[30rem] pt-10 pb-44 bg-white bg-opacity-20 rounded-xl shadow-xl text-center flex flex-col items-center">
        <button onClick={onClose} className="absolute top-2 right-2 text-gray-300">✕</button>
        <h2 className="text-2xl font-semibold mb-6 text-white">Select a Doctor</h2>
        
        <div className="relative w-full flex flex-col items-center h-96">
          <AnimatePresence>
            {doctors.map((doctor, index) => (
              index === currentIndex && (
                <motion.div
                  key={doctor.id}
                  initial={{ x: 50, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  exit={{ x: -50, opacity: 0 }}
                  transition={{ type: "spring", stiffness: 300, damping: 20 }}
                  className="absolute flex flex-col items-center"
                >
                  <div className="relative w-full flex justify-center">
                    <button onClick={prevDoctor} className="absolute left-2 top-1/2 transform -translate-y-1/2 bg-gray-300 text-white p-2 rounded-full">←</button>
                    <img src={doctor.image} alt={doctor.name} className="w-80 h-96 rounded-lg shadow-md object-cover" />
                    <button onClick={nextDoctor} className="absolute right-2 top-1/2 transform -translate-y-1/2 bg-gray-300 text-white p-2 rounded-full">→</button>
                  </div>
                  <h3 className="mt-4 text-xl font-medium text-white">{doctor.name}</h3>
                  <p className="text-gray-300 text-lg">{doctor.specialty}</p>
                  <button className="mt-4 px-5 py-3 bg-blue-500 text-white rounded-lg text-lg">Chat</button>
                </motion.div>
              )
            ))}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};

export default DoctorSelection;
