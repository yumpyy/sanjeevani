import { useEffect, useRef, useState, forwardRef, useImperativeHandle } from "react";
import StreamingAvatar, { TaskMode, TaskType, StreamingEvents, AvatarQuality, VoiceEmotion } from "@heygen/streaming-avatar";

const InteractiveAvatar = forwardRef((props, ref) => {
  const [stream, setStream] = useState<MediaStream>();
  const [isLoadingSession, setIsLoadingSession] = useState(false);
  const [isLoadingRepeat, setIsLoadingRepeat] = useState(false);
  const avatar = useRef<StreamingAvatar | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  async function fetchAccessToken() {
    try {
      const response = await fetch("/api/get-access-token", { method: "POST" });
      return await response.text();
    } catch (error) {
      console.error("Error fetching access token:", error);
      return "";
    }
  }

  async function startSession(avatarId: string, language: string) {
    setIsLoadingSession(true);
    const token = await fetchAccessToken();
    avatar.current = new StreamingAvatar({ token });
    
    avatar.current.on(StreamingEvents.STREAM_READY, (event) => {
      if (videoRef.current) {
        videoRef.current.srcObject = event.detail;
        setStream(event.detail);
      }
    });

    try {
      await avatar.current.createStartAvatar({
        quality: AvatarQuality.High,
        avatarName: avatarId,
        voice: {
          rate: 1.2,
          emotion: VoiceEmotion.NEUTRAL,
        },
        language,
        disableIdleTimeout: true,
      });
    } catch (error) {
      console.log("Error starting avatar session:", error);
    } finally {
      setIsLoadingSession(false);
    }
  }

  async function speakText(text: string) {
    if (!avatar.current) {
      console.error("Avatar session not started.");
      return;
    }
    setIsLoadingRepeat(true);
    await avatar.current
      .speak({ text, taskType: TaskType.REPEAT, })
      .catch((e) => console.error("Error speaking text:", e.message));
    setIsLoadingRepeat(false);
  }

  async function endSession() {
    await avatar.current?.stopAvatar();
    setStream(undefined);
  }

  useImperativeHandle(ref, () => ({
    startSession,
    speakText,
    endSession,
  }));

  useEffect(() => {
    return () => {
      endSession();
    };
  }, []);

  return (
    <div id="avatarContainer" className="relative w-full h-full">
      <video
        ref={videoRef}
        autoPlay
        playsInline
        style={{ width: "100%", height: "100%", objectFit: "cover" }}
        muted={false}
      />
      {!stream && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100">
          <p className="text-lg text-gray-500">Avatar not started</p>
        </div>
      )}
    </div>
  );
});

export default InteractiveAvatar;
