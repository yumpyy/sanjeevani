"use client"
import { useRef } from "react";
import InteractiveAvatar from "../../components/InteractiveAvatar";

export default function AvatarControl() {
  const avatarRef = useRef(null);

  const startAvatar = async () => {
    await avatarRef.current?.startSession("Ann_Doctor_Standing2_public", "en");
  };

  const speakText = async () => {
    await avatarRef.current?.speakText("Hello, I am your AI assistant!");
  };

  return (
    <div>
      <InteractiveAvatar ref={avatarRef} />
      <button onClick={startAvatar}>Start Avatar</button>
      <button onClick={speakText}>Speak</button>
    </div>
  );
}
