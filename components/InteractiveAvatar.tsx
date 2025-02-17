import { useEffect, useRef, useState, forwardRef, useImperativeHandle } from "react";
import StreamingAvatar, { TaskMode, TaskType, StreamingEvents, AvatarQuality, VoiceEmotion } from "@heygen/streaming-avatar";

const InteractiveAvatar = forwardRef((props, ref) => {
  const [stream, setStream] = useState<MediaStream>();
  const [isLoadingSession, setIsLoadingSession] = useState(false);
  const [isLoadingRepeat, setIsLoadingRepeat] = useState(false);
  const avatar = useRef<StreamingAvatar | null>(null);

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
      setStream(event.detail);
    });

    try {
      await avatar.current.createStartAvatar({
        quality: AvatarQuality.Low,
        avatarName: avatarId,
        voice: {
          rate: 1.2,
          emotion: VoiceEmotion.NEUTRAL,
        },
        language,
        disableIdleTimeout: true,
      });

      await avatar.current.startVoiceChat({ useSilencePrompt: false });
    } catch (error) {
      console.error("Error starting avatar session:", error);
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
      .speak({ text, taskType: TaskType.REPEAT, taskMode: TaskMode.SYNC })
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
    <div>
      {stream ? (
        <video
          autoPlay
          playsInline
          ref={(el) => el && (el.srcObject = stream)}
          style={{ width: "100%", height: "auto" }}
        />
      ) : (
        <p>Avatar not started</p>
      )}
    </div>
  );
});

export default InteractiveAvatar;
