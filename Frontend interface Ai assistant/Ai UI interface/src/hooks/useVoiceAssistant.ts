import { useCallback, useEffect, useRef, useState } from "react";
import * as LivekitClient from "livekit-client";
import { fetchBrowserApiJson, getBrowserApiBase } from "@/utils/browserApi";

type Status = "idle" | "listening" | "speaking" | "connecting" | "error";

function classifyTranscriptSource(
  participant: LivekitClient.Participant | undefined,
  fallbackStatus: Status,
) {
  if (participant?.isLocal === true) return "user";
  if (participant?.isLocal === false) return "agent";
  return fallbackStatus === "listening" ? "user" : "agent";
}

export function useVoiceAssistant() {
  const [status, setStatus] = useState<Status>("idle");
  const [transcript, setTranscript] = useState("");
  const [interim, setInterim] = useState("");
  const [reply, setReply] = useState("");
  const [supported] = useState(true);
  const [level, setLevel] = useState(0);
  const [audioBlocked, setAudioBlocked] = useState(false);

  const roomRef = useRef<LivekitClient.Room | null>(null);
  const remoteAudioTrackRef = useRef<LivekitClient.RemoteAudioTrack | null>(null);
  const remoteAudioElementRef = useRef<HTMLAudioElement | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const rafRef = useRef<number | null>(null);
  const statusRef = useRef<Status>("idle");

  useEffect(() => {
    statusRef.current = status;
  }, [status]);

  const stopAnalyser = useCallback(() => {
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    rafRef.current = null;
    analyserRef.current = null;
    setLevel(0);
  }, []);

  const ensureRemoteAudioElement = useCallback(() => {
    if (remoteAudioElementRef.current) return remoteAudioElementRef.current;

    const audio = document.createElement("audio");
    audio.autoplay = true;
    audio.playsInline = true;
    audio.preload = "auto";
    audio.style.display = "none";
    document.body.appendChild(audio);
    remoteAudioElementRef.current = audio;
    return audio;
  }, []);

  const detachRemoteAudio = useCallback(() => {
    if (remoteAudioTrackRef.current) {
      remoteAudioTrackRef.current.detach();
      remoteAudioTrackRef.current = null;
    }

    if (remoteAudioElementRef.current) {
      remoteAudioElementRef.current.pause();
      remoteAudioElementRef.current.srcObject = null;
    }
  }, []);

  const closeAudioContext = useCallback(() => {
    if (audioCtxRef.current) {
      audioCtxRef.current.close().catch(() => {});
      audioCtxRef.current = null;
    }
  }, []);

  const startAnalyser = useCallback(
    (track: LivekitClient.LocalAudioTrack | LivekitClient.RemoteAudioTrack) => {
      stopAnalyser();
      closeAudioContext();

      try {
        const ctx = new (window.AudioContext || (window as typeof window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext!)();
        audioCtxRef.current = ctx;
        if (ctx.state === "suspended") {
          void ctx.resume();
        }

        const source = ctx.createMediaStreamSource(new MediaStream([track.mediaStreamTrack]));
        const analyser = ctx.createAnalyser();
        analyser.fftSize = 512;
        source.connect(analyser);
        analyserRef.current = analyser;

        const data = new Uint8Array(analyser.frequencyBinCount);
        const tick = () => {
          if (!analyserRef.current) return;
          analyserRef.current.getByteTimeDomainData(data);

          let sum = 0;
          for (let i = 0; i < data.length; i += 1) {
            const value = (data[i] - 128) / 128;
            sum += value * value;
          }

          setLevel(Math.min(1, Math.sqrt(sum / data.length) * 5));
          rafRef.current = requestAnimationFrame(tick);
        };

        tick();
      } catch (error) {
        console.error("[Whisper] Analyser error", error);
      }
    },
    [closeAudioContext, stopAnalyser],
  );

  const connect = useCallback(async () => {
    if (roomRef.current || statusRef.current === "connecting") return;

    setStatus("connecting");
    setInterim("");
    const apiBase = getBrowserApiBase();
    console.log("[Whisper] Connecting to API at:", apiBase);

    try {
      let config;
      if (window.pywebview && window.pywebview.api) {
        console.log("[Whisper] Using pywebview API");
        // @ts-ignore
        config = await window.pywebview.api.get_livekit_config();
      } else {
        console.log("[Whisper] Attempting to fetch LiveKit config from backend...");
        
        // First, check if backend is healthy
        try {
          const healthResponse = await fetch(`${apiBase}/healthz`);
          if (!healthResponse.ok) {
            console.warn("[Whisper] Backend health check failed:", healthResponse.status, healthResponse.statusText);
          } else {
            console.log("[Whisper] Backend is healthy");
          }
        } catch (healthError) {
          console.error("[Whisper] Backend health check error:", healthError);
        }

        console.log(`[Whisper] Fetching LiveKit config from ${apiBase}/livekit/config`);
        config = await fetchBrowserApiJson("/livekit/config");
      }
      const { url, token } = config;
      console.log("[Whisper] LiveKit config received:", { url: url ? "present" : "missing", token: token ? "present" : "missing" });
      if (!url || !token) {
        const errorMsg = `Missing LiveKit configuration - URL: ${url ? "✓" : "✗"}, Token: ${token ? "✓" : "✗"}`;
        console.error("[Whisper]", errorMsg);
        throw new Error(errorMsg);
      }

      const room = new LivekitClient.Room({
        adaptiveStream: true,
        dynacast: true,
        webAudioMix: false,
        audioCaptureDefaults: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      roomRef.current = room;

      room.on(
        LivekitClient.RoomEvent.TranscriptionReceived,
        (
          segments: LivekitClient.TranscriptionSegment[],
          participant?: LivekitClient.Participant,
          _publication?: LivekitClient.TrackPublication,
        ) => {
          const text = segments.map((segment) => segment.text).join(" ").trim();
          if (!text) return;

          const isFinal = segments.every((segment) => segment.final);
          const source = classifyTranscriptSource(participant, statusRef.current);

          console.log(`[Transcript] ${source.toUpperCase()} (${isFinal ? "final" : "interim"}): "${text}"`);

          if (source === "user") {
            if (isFinal) {
              setTranscript(text);
              setInterim("");
            } else {
              setInterim(text);
            }
            setStatus("listening");
            return;
          }

          setReply(text);
          setStatus("speaking");
        },
      );

      room.on(LivekitClient.RoomEvent.AudioPlaybackStatusChanged, (canPlay: boolean) => {
        console.log("[Whisper] AudioPlaybackStatus:", canPlay);
        setAudioBlocked(!canPlay);
        if (!canPlay) {
          console.warn("[Whisper] Audio blocked - user interaction is required");
        }
      });

      room.on(LivekitClient.RoomEvent.ActiveSpeakersChanged, (speakers) => {
        const agentSpeaking = speakers.some((speaker) => !speaker.isLocal);
        const userSpeaking = speakers.some((speaker) => speaker.isLocal);

        if (agentSpeaking) {
          setStatus("speaking");
        } else if (userSpeaking) {
          setStatus("listening");
        } else {
          setStatus((prev) => (prev === "speaking" || prev === "listening" ? "idle" : prev));
        }
      });

      room.on(LivekitClient.RoomEvent.ParticipantConnected, (participant) => {
        console.log("[Whisper] Participant joined:", participant.identity, "isLocal:", participant.isLocal);
      });

      room.on(LivekitClient.RoomEvent.ParticipantDisconnected, (participant) => {
        console.log("[Whisper] Participant left:", participant.identity);
      });

      room.on(LivekitClient.RoomEvent.TrackSubscribed, (track, _pub, participant) => {
        if (track.kind === LivekitClient.Track.Kind.Audio && !participant.isLocal) {
          console.log("[Whisper] Agent audio subscribed - attaching to hidden audio element");
          const remoteTrack = track as LivekitClient.RemoteAudioTrack;
          const audioElement = ensureRemoteAudioElement();
          detachRemoteAudio();
          remoteAudioTrackRef.current = remoteTrack;
          remoteTrack.attach(audioElement);
          void audioElement.play().then(() => {
            setAudioBlocked(false);
            console.log("[Whisper] Remote audio playback started");
          }).catch((error) => {
            console.warn("[Whisper] Remote audio playback blocked:", error);
            setAudioBlocked(true);
          });
          setStatus("speaking");
          startAnalyser(remoteTrack);
        }
      });

      room.on(LivekitClient.RoomEvent.TrackUnsubscribed, (track) => {
        if (track.kind === LivekitClient.Track.Kind.Audio) {
          detachRemoteAudio();
          stopAnalyser();
          closeAudioContext();
          setStatus((prev) => (prev === "speaking" ? "idle" : prev));
        }
      });

      room.on(LivekitClient.RoomEvent.LocalTrackPublished, (publication) => {
        if (publication.track?.kind === LivekitClient.Track.Kind.Audio) {
          console.log("[Whisper] Mic published - analysing audio");
          startAnalyser(publication.track as LivekitClient.LocalAudioTrack);
        }
      });

      room.on(LivekitClient.RoomEvent.DataReceived, (payload: Uint8Array) => {
        const str = new TextDecoder().decode(payload);
        try {
          const data = JSON.parse(str);
          if (data.type === "command" && (window as any).pywebview?.api) {
            const api = (window as any).pywebview.api;
            console.log("[Whisper] Received remote command:", data.command, data.data);
            if (data.command === "open_url") {
              api.open_url(data.data.url);
            } else if (data.command === "open_app") {
              api.open_app(data.data.name);
            } else if (data.command === "take_screenshot") {
              api.take_screenshot();
            }
          }
        } catch (e) {
          console.error("[Whisper] Failed to parse data message:", e);
        }
      });

      room.on(LivekitClient.RoomEvent.Disconnected, () => {
        console.log("[Whisper] Disconnected");
        detachRemoteAudio();
        roomRef.current = null;
        stopAnalyser();
        closeAudioContext();
        setStatus("idle");
      });

      await room.connect(url, token);
      console.log("[Whisper] Room connected:", room.name);

      try {
        await room.startAudio();
        setAudioBlocked(false);
        console.log("[Whisper] Audio started successfully");
      } catch (error) {
        console.warn("[Whisper] startAudio failed (user tap may be needed):", error);
        setAudioBlocked(true);
      }

      try {
        await room.localParticipant.setMicrophoneEnabled(true);
        console.log("[Whisper] Mic enabled");
      } catch (error) {
        console.error("[Whisper] Mic failed:", error);
        setStatus("error");
        return;
      }

      setStatus("listening");
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      console.error("[Whisper] Connection failed:", {
        error: errorMessage,
        apiBase: getBrowserApiBase(),
        timestamp: new Date().toISOString(),
      });
      roomRef.current = null;
      stopAnalyser();
      closeAudioContext();
      setStatus("error");
    }
  }, [closeAudioContext, startAnalyser, stopAnalyser]);

  const startAudio = useCallback(async () => {
    if (!roomRef.current) return;

    try {
      await roomRef.current.startAudio();
      if (remoteAudioElementRef.current) {
        await remoteAudioElementRef.current.play();
      }
      setAudioBlocked(false);
      console.log("[Whisper] Audio playback enabled");
    } catch (error) {
      console.warn("[Whisper] startAudio on interaction failed:", error);
    }
  }, []);

  const disconnect = useCallback(async () => {
    detachRemoteAudio();
    stopAnalyser();
    closeAudioContext();

    if (roomRef.current) {
      await roomRef.current.disconnect();
      roomRef.current = null;
    }

    setStatus("idle");
    setTranscript("");
    setInterim("");
    setReply("");
    setAudioBlocked(false);
  }, [closeAudioContext, detachRemoteAudio, stopAnalyser]);

  const toggle = useCallback(() => {
    if (roomRef.current) {
      void disconnect();
    } else {
      void connect();
    }
  }, [connect, disconnect]);

  useEffect(() => {
    return () => {
      void disconnect();
    };
  }, [disconnect]);

  useEffect(() => {
    return () => {
      detachRemoteAudio();
      if (remoteAudioElementRef.current?.parentNode) {
        remoteAudioElementRef.current.parentNode.removeChild(remoteAudioElementRef.current);
      }
      remoteAudioElementRef.current = null;
    };
  }, [detachRemoteAudio]);

  return {
    status,
    transcript,
    interim,
    reply,
    level,
    supported,
    audioBlocked,
    toggle,
    connect,
    disconnect,
    startAudio,
    startListening: connect,
    stopListening: disconnect,
    stopSpeaking: disconnect,
  };
}
