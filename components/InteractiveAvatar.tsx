import { useEffect, useRef, useState, forwardRef, useImperativeHandle } from "react";
import StreamingAvatar, { TaskMode, TaskType, StreamingEvents, AvatarQuality, VoiceEmotion } from "@heygen/streaming-avatar";

const InteractiveAvatar = forwardRef((props, ref) => {
  const [stream, setStream] = useState<MediaStream>();
  const [isLoadingSession, setIsLoadingSession] = useState(false);
  const [isLoadingRepeat, setIsLoadingRepeat] = useState(false);
  const [avatarError, setAvatarError] = useState<string | null>(null);
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
    setAvatarError(null);
    const token = await fetchAccessToken();
    // TEMP: HeyGen is sunset. If we get the placeholder token, don't try
    // to start a real session — the chat still works, the video just
    // shows a placeholder.
    if (!token || token === "placeholder-token") {
      setAvatarError("Avatar disabled (HeyGen migration pending).");
      setIsLoadingSession(false);
      return;
    }
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
    } catch (error: any) {
      console.warn("Avatar disabled:", error?.message ?? error);
      setAvatarError("Avatar unavailable.");
    } finally {
      setIsLoadingSession(false);
    }
  }

  async function speakText(text: string) {
    if (!avatar.current) return;
    setIsLoadingRepeat(true);
    try {
      await avatar.current.speak({ text, taskType: TaskType.REPEAT });
    } catch (e: any) {
      console.warn("Avatar speak skipped:", e?.message ?? e);
    } finally {
      setIsLoadingRepeat(false);
    }
  }

  async function endSession() {
    try {
      await avatar.current?.stopAvatar();
    } catch {
      // ignore
    } finally {
      avatar.current = null;
      setStream(undefined);
    }
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
          <p className="text-lg text-gray-500">
            {avatarError ?? "Avatar not started"}
          </p>
        </div>
      )}
    </div>
  );
});

export default InteractiveAvatar;
