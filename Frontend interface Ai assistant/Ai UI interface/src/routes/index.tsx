import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { DnaWave } from "@/components/orb/DnaWave";
import { useVoiceAssistant } from "@/hooks/useVoiceAssistant";
import { fetchBrowserApiJson } from "@/utils/browserApi";

export const Route = createFileRoute("/")({
  component: Index,
  head: () => ({
    meta: [
      { title: "Whisper AI Assistant" },
      {
        name: "description",
        content:
          "Interactive voice assistant orb with compact transcripts, responsive layout, and real-time credits.",
      },
    ],
  }),
});

type OrbState = "idle" | "listening" | "speaking";

export function Index() {
  const {
    status: orbState,
    transcript,
    interim,
    reply,
    level,
    supported,
    audioBlocked,
    toggle,
    connect,
    startAudio,
  } = useVoiceAssistant();

  const [booted, setBooted] = useState(false);
  const [eyesOpen, setEyesOpen] = useState(false);
  const [blink, setBlink] = useState(false);
  const [eyeOffset, setEyeOffset] = useState({ x: 0, y: 0 });
  const containerRef = useRef<HTMLDivElement>(null);

  const [groqUsage, setGroqUsage] = useState({ used: 0, limit: 30, pct: 0 });
  const [elevenUsage, setElevenUsage] = useState({ used: 0, limit: 10000, pct: 0 });

  const updateUsage = async () => {
    try {
      if (window.pywebview?.api) {
        // @ts-ignore
        const groq = await window.pywebview.api.get_groq_usage();
        // @ts-ignore
        const eleven = await window.pywebview.api.get_elevenlabs_usage();
        if (groq.ok) setGroqUsage(groq.requests);
        if (eleven.ok) setElevenUsage(eleven);
        return;
      }

      const groq = await fetchBrowserApiJson<{
        remaining_requests?: number | string;
      }>("/usage/groq");
      const eleven = await fetchBrowserApiJson<{
        character_count?: number;
        character_limit?: number;
      }>("/usage/elevenlabs");

      if (groq.remaining_requests !== undefined && groq.remaining_requests !== "unknown") {
        const limit = 30;
        const remaining = Number(groq.remaining_requests);
        const used = Math.max(0, limit - remaining);
        setGroqUsage({
          limit,
          used,
          pct: Math.round((used / Math.max(1, limit)) * 100),
        });
      }

      if (eleven.character_limit !== undefined) {
        const used = Number(eleven.character_count || 0);
        const limit = Number(eleven.character_limit || 10000);
        setElevenUsage({
          used,
          limit,
          pct: Math.round((used / Math.max(1, limit)) * 100),
        });
      }
    } catch (error) {
      console.warn("Usage fetch failed", error);
    }
  };

  useEffect(() => {
    const t1 = setTimeout(() => setBooted(true), 450);
    const t2 = setTimeout(() => setEyesOpen(true), 900);
    const t3 = setTimeout(async () => {
      await connect();
      await startAudio();
    }, 1000);
    const t4 = setTimeout(updateUsage, 1800);
    const usageInterval = setInterval(updateUsage, 60000);

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
      clearTimeout(t4);
      clearInterval(usageInterval);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!eyesOpen) return;

    let cancelled = false;
    const loop = () => {
      const delay = 2500 + Math.random() * 3500;
      setTimeout(() => {
        if (cancelled) return;
        setBlink(true);
        setTimeout(() => {
          if (cancelled) return;
          setBlink(false);
          if (Math.random() < 0.25) {
            setTimeout(() => {
              if (cancelled) return;
              setBlink(true);
              setTimeout(() => {
                if (cancelled) return;
                setBlink(false);
                loop();
              }, 120);
            }, 160);
          } else {
            loop();
          }
        }, 130);
      }, delay);
    };

    loop();
    return () => {
      cancelled = true;
    };
  }, [eyesOpen]);

  useEffect(() => {
    const onMove = (event: MouseEvent) => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const cx = rect.left + rect.width / 2;
      const cy = rect.top + rect.height / 2;
      const dx = event.clientX - cx;
      const dy = event.clientY - cy;
      const dist = Math.hypot(dx, dy) || 1;
      const max = 8;
      const nx = (dx / dist) * Math.min(max, dist / 40);
      const ny = (dy / dist) * Math.min(max, dist / 40);
      setEyeOffset({ x: nx, y: ny });
    };

    window.addEventListener("mousemove", onMove);
    return () => window.removeEventListener("mousemove", onMove);
  }, []);

  const isListening = orbState === "listening";
  const isSpeaking = orbState === "speaking";
  const currentUserText = interim || transcript;
  const hasCaptions = Boolean(currentUserText || reply);

  const baseEyeRy = 22;
  const eyeRy = blink ? 1.5 : isListening ? baseEyeRy * 0.65 : isSpeaking ? baseEyeRy * 0.95 : baseEyeRy;

  return (
    <div className="relative h-screen w-full overflow-hidden bg-black text-white">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_25%,rgba(0,0,0,0.9)_100%)]" />

      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: booted ? 1 : 0, y: booted ? 0 : -10 }}
        transition={{ delay: 0.35, duration: 0.5 }}
        className="absolute left-1/2 top-4 z-20 -translate-x-1/2 px-4 text-center sm:top-5"
      >
        <h1 className="text-[10px] font-light uppercase tracking-[0.48em] text-white/38 sm:text-[11px] sm:tracking-[0.6em]">
          Whisper AI Assistant
        </h1>
        <p className="mt-1 text-[8px] uppercase tracking-[0.2em] text-white/20 sm:text-[9px] sm:tracking-[0.28em]">
          {orbState === "connecting"
            ? "Initializing..."
            : orbState === "listening"
              ? "Listening..."
              : orbState === "speaking"
                ? "Speaking..."
                : orbState === "error"
                  ? "Tap to reconnect"
                  : "Online"}
        </p>
      </motion.div>

      <div
        ref={containerRef}
        className="relative flex h-full w-full flex-col items-center justify-between px-4 pb-28 pt-14 sm:px-6 sm:pb-24 sm:pt-16"
      >
        <div className="relative flex w-full max-w-5xl flex-1 flex-col items-center justify-center gap-3 sm:gap-5">
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: booted ? 1 : 0, y: booted ? 0 : -10 }}
            transition={{ delay: 0.45, duration: 0.5 }}
            className="pointer-events-none z-30 w-full"
          >
            <div
              className="mx-auto flex w-full max-w-2xl flex-col gap-2"
              style={{ fontFamily: '"Segoe UI Variable Display", "Aptos", "Trebuchet MS", sans-serif' }}
            >
              <AnimatePresence>
                {orbState === "connecting" && (
                  <motion.span
                    key="status-connecting"
                    initial={{ opacity: 0, scale: 0.96 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0 }}
                    className="self-center rounded-full border border-amber-400/25 bg-amber-400/10 px-3 py-1 text-[10px] uppercase tracking-[0.22em] text-amber-300"
                  >
                    Connecting
                  </motion.span>
                )}
                {orbState === "error" && (
                  <motion.span
                    key="status-error"
                    initial={{ opacity: 0, scale: 0.96 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0 }}
                    className="self-center rounded-full border border-rose-500/25 bg-rose-500/10 px-3 py-1 text-[10px] uppercase tracking-[0.22em] text-rose-300"
                  >
                    Connection error
                  </motion.span>
                )}
              </AnimatePresence>

              <AnimatePresence>
                {!hasCaptions && orbState === "idle" && (
                  <motion.p
                    key="placeholder"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-center text-[11px] uppercase tracking-[0.22em] text-white/28"
                  >
                    Start speaking to see your transcript
                  </motion.p>
                )}
              </AnimatePresence>

              <AnimatePresence>
                {hasCaptions && (
                  <motion.div
                    key="bars"
                    initial={{ opacity: 0, y: -8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    className="grid gap-2"
                  >
                    <div className="rounded-2xl border border-cyan-400/20 bg-[#0d151b] px-4 py-3">
                      <div className="mb-1 flex items-center justify-between gap-3">
                        <span className="text-[9px] uppercase tracking-[0.3em] text-cyan-300/78">You</span>
                        {interim && (
                          <span className="text-[9px] uppercase tracking-[0.2em] text-white/34">Listening</span>
                        )}
                      </div>
                      <p className={`text-[14px] leading-6 sm:text-[16px] ${interim ? "text-white/56 italic" : "text-white/88"}`}>
                        {currentUserText || "Start speaking..."}
                      </p>
                    </div>

                    <div className="rounded-2xl border border-white/10 bg-[#111318] px-4 py-3">
                      <div className="mb-1 flex items-center justify-between gap-3">
                        <span className="text-[9px] uppercase tracking-[0.3em] text-white/56">Whisper</span>
                        {!reply && (
                          <span className="text-[9px] uppercase tracking-[0.2em] text-white/24">
                            {orbState === "connecting" ? "Connecting" : "Waiting"}
                          </span>
                        )}
                      </div>
                      <p className="min-h-[24px] text-[14px] leading-6 text-white/88 sm:text-[16px]">
                        {reply || "The assistant reply will appear here as soon as Whisper speaks."}
                      </p>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </motion.div>

          <OrbScene
            booted={booted}
            eyesOpen={eyesOpen}
            eyeRy={eyeRy}
            eyeOffset={eyeOffset}
            state={orbState}
            level={level}
          />

          <div className="min-h-[44px]">
            <DnaWave
              active={isListening || isSpeaking}
              level={level}
              variant={isSpeaking ? "speaking" : "listening"}
            />
          </div>
        </div>
      </div>

      <div className="pointer-events-none absolute inset-x-0 bottom-4 z-20 flex flex-col items-center gap-3 px-4 sm:bottom-6">
        <AnimatePresence>
          {audioBlocked && (
            <motion.button
              key="audio-blocked"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 10 }}
              onClick={startAudio}
              className="pointer-events-auto rounded-full border border-amber-400/35 bg-amber-400/10 px-4 py-1.5 text-[10px] uppercase tracking-[0.22em] text-amber-300"
            >
              Tap here to enable audio
            </motion.button>
          )}
        </AnimatePresence>

        <div className="pointer-events-auto flex items-center gap-3">
          <motion.button
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: booted ? 1 : 0, y: booted ? 0 : 16 }}
            transition={{ delay: 0.6, duration: 0.45 }}
            onClick={() => {
              void startAudio();
              toggle();
            }}
            disabled={!supported || orbState === "connecting"}
            className="group relative flex h-12 items-center gap-3 rounded-full border border-white/15 bg-white/5 px-6 text-[11px] font-medium uppercase tracking-[0.22em] text-white/80 backdrop-blur-2xl transition-all hover:border-white/30 hover:bg-white/10 disabled:opacity-40 sm:h-14 sm:px-8 sm:text-xs sm:tracking-[0.3em]"
          >
            <span
              className={`relative flex h-3 w-3 items-center justify-center rounded-full transition-colors ${
                orbState === "connecting"
                  ? "bg-amber-400"
                  : isListening
                    ? "bg-rose-500"
                    : isSpeaking
                      ? "bg-cyan-400"
                      : "bg-white/40"
              }`}
            >
              {(isListening || isSpeaking || orbState === "connecting") && (
                <span
                  className={`absolute inset-0 animate-ping rounded-full ${
                    orbState === "connecting"
                      ? "bg-amber-400/50"
                      : isListening
                        ? "bg-rose-500/50"
                        : "bg-cyan-400/50"
                  }`}
                />
              )}
            </span>
            {orbState === "connecting"
              ? "Connecting..."
              : isListening
                ? "Listening... tap to stop"
                : isSpeaking
                  ? "Speaking... tap to stop"
                  : "Tap to speak"}
          </motion.button>

          <motion.button
            title="Restart Agent Backend"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: booted ? 1 : 0, scale: booted ? 1 : 0.9 }}
            transition={{ delay: 0.7, duration: 0.45 }}
            onClick={async () => {
              // @ts-ignore
              if (window.pywebview?.api) {
                // @ts-ignore
                await window.pywebview.api.disconnect();
                setTimeout(async () => {
                  // @ts-ignore
                  await window.pywebview.api.connect();
                  window.location.reload();
                }, 1000);
              } else {
                window.location.reload();
              }
            }}
            className="group relative flex h-12 w-12 items-center justify-center rounded-full border border-white/20 bg-white/5 transition-all hover:border-white/35 hover:bg-white/10 sm:h-14 sm:w-14"
          >
            <svg
              className="h-5 w-5 text-white/70 transition-all duration-500 group-hover:rotate-180 group-hover:text-white"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
          </motion.button>
        </div>

        {!supported && (
          <p className="text-[10px] uppercase tracking-[0.22em] text-rose-400/80">
            Voice not supported in this browser
          </p>
        )}
      </div>

      <motion.div
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: booted ? 1 : 0, x: booted ? 0 : 20 }}
        transition={{ delay: 0.8, duration: 0.45 }}
        className="absolute bottom-20 left-4 right-4 z-20 flex flex-col gap-3 rounded-xl border border-white/10 bg-black/45 p-3 backdrop-blur-md sm:bottom-6 sm:left-auto sm:right-6 sm:w-[220px]"
      >
        <div className="flex flex-col gap-1">
          <div className="flex justify-between text-[9px] uppercase tracking-[0.2em] text-white/40">
            <span>Groq API</span>
            <span>{groqUsage.used}/{groqUsage.limit}</span>
          </div>
          <div className="h-1 w-full overflow-hidden rounded-full bg-white/5">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${groqUsage.pct}%` }}
              className={`h-full ${groqUsage.pct > 80 ? "bg-rose-500" : groqUsage.pct > 50 ? "bg-amber-400" : "bg-cyan-400"}`}
            />
          </div>
        </div>

        <div className="flex flex-col gap-1">
          <div className="flex justify-between text-[9px] uppercase tracking-[0.2em] text-white/40">
            <span>ElevenLabs</span>
            <span>{Math.round(elevenUsage.used / 1000)}k/{Math.round(elevenUsage.limit / 1000)}k</span>
          </div>
          <div className="h-1 w-full overflow-hidden rounded-full bg-white/5">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${elevenUsage.pct}%` }}
              className={`h-full ${elevenUsage.pct > 80 ? "bg-rose-500" : elevenUsage.pct > 50 ? "bg-amber-400" : "bg-purple-500"}`}
            />
          </div>
        </div>
      </motion.div>
    </div>
  );
}

function OrbScene({
  booted,
  eyesOpen,
  eyeRy,
  eyeOffset,
  state,
  level,
}: {
  booted: boolean;
  eyesOpen: boolean;
  eyeRy: number;
  eyeOffset: { x: number; y: number };
  state: OrbState;
  level: number;
}) {
  const isListening = state === "listening";
  const isSpeaking = state === "speaking";

  return (
    <div className="relative aspect-square w-full max-w-[min(340px,44vh,78vw)] sm:max-w-[min(400px,48vh,72vw)]">
      <AnimatePresence>
        {isListening &&
          [0, 1].map((index) => (
            <motion.div
              key={`ripple-${index}`}
              initial={{ scale: 0.68, opacity: 0 }}
              animate={{ scale: 1.45, opacity: [0, 0.35, 0] }}
              exit={{ opacity: 0 }}
              transition={{
                duration: 2.2,
                repeat: Infinity,
                delay: index * 0.75,
                ease: "easeOut",
              }}
              className="absolute inset-0 rounded-full border border-cyan-300/25"
              style={{
                boxShadow: "0 0 40px rgba(90,170,255,0.18), inset 0 0 40px rgba(150,120,255,0.08)",
              }}
            />
          ))}
      </AnimatePresence>

      <motion.div
        initial={{ scale: 0.08, opacity: 0 }}
        animate={{ scale: booted ? 1 : 0.08, opacity: booted ? 1 : 0 }}
        transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
        className="absolute inset-0"
      >
        <ChromaticHalo state={state} level={level} />
      </motion.div>

      <motion.div
        initial={{ scale: 0, opacity: 0 }}
        animate={{ scale: booted ? 1 : 0, opacity: booted ? 1 : 0 }}
        transition={{
          delay: 0.25,
          duration: 0.8,
          type: "spring",
          stiffness: 120,
          damping: 14,
        }}
        className="absolute inset-0 flex items-center justify-center"
      >
        <motion.div
          animate={{
            x: eyeOffset.x * 0.35,
            y: eyeOffset.y * 0.35,
            scale: isListening ? 1 + level * 0.04 : isSpeaking ? 1 + level * 0.03 : 1,
          }}
          transition={{
            x: { type: "spring", stiffness: 80, damping: 18 },
            y: { type: "spring", stiffness: 80, damping: 18 },
            scale: { type: "spring", stiffness: 120, damping: 14 },
          }}
          className="relative h-[58%] w-[58%] rounded-full"
          style={{
            background: "radial-gradient(circle at 35% 30%, #2a2a2e 0%, #0a0a0c 55%, #000 100%)",
            boxShadow:
              "inset -20px -30px 60px rgba(0,0,0,0.9), inset 20px 30px 60px rgba(80,80,120,0.15), 0 30px 80px rgba(0,0,0,0.8)",
          }}
        >
          <div
            className="absolute left-[18%] top-[12%] h-[35%] w-[45%] rounded-full opacity-60"
            style={{
              background: "radial-gradient(ellipse at center, rgba(255,255,255,0.18) 0%, transparent 70%)",
              filter: "blur(8px)",
            }}
          />

          <svg viewBox="0 0 200 200" className="absolute inset-0 h-full w-full">
            <g
              style={{
                transform: `translate(${eyeOffset.x * 0.6}px, ${eyeOffset.y * 0.6}px)`,
                transition: "transform 0.25s ease-out",
              }}
            >
              <Eye cx={75} cy={100} ry={eyesOpen ? eyeRy : 0.5} />
              <Eye cx={125} cy={100} ry={eyesOpen ? eyeRy : 0.5} />
            </g>
          </svg>
        </motion.div>
      </motion.div>
    </div>
  );
}

function Eye({ cx, cy, ry }: { cx: number; cy: number; ry: number }) {
  return (
    <motion.ellipse
      cx={cx}
      cy={cy}
      rx={11}
      animate={{ ry }}
      transition={{ duration: 0.12, ease: "easeOut" }}
      fill="white"
      style={{ filter: "drop-shadow(0 0 8px rgba(200,220,255,0.6))" }}
    />
  );
}

const HALO_GRADIENTS: Record<OrbState, string> = {
  idle: "conic-gradient(from 0deg, #00d4ff, #7b5cff, #ff3eb5, #ff6a3d, #ffd166, #3effd1, #00d4ff)",
  listening:
    "conic-gradient(from 0deg, #5ee0ff, #00d4ff, #b18cff, #5ee0ff, #00d4ff, #b18cff, #5ee0ff)",
  speaking:
    "conic-gradient(from 0deg, #ff5ec4, #ffb15e, #ffd166, #ff5ec4, #b18cff, #ffb15e, #ff5ec4)",
};

function ChromaticHalo({ state, level }: { state: OrbState; level: number }) {
  const intense = state !== "idle";
  const rotateDuration = state === "speaking" ? 10 : state === "listening" ? 14 : 18;

  return (
    <div className="absolute inset-0">
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: rotateDuration, ease: "linear", repeat: Infinity }}
        className="absolute inset-0 rounded-full"
        style={{
          background: HALO_GRADIENTS[state],
          transition: "background 1.2s ease, filter 0.6s ease, opacity 0.6s ease",
          filter: `blur(${intense ? 48 + level * 8 : 38}px) saturate(${140 + level * 50}%)`,
          opacity: intense ? 0.9 : 0.75,
          maskImage: "radial-gradient(circle, transparent 32%, black 42%, black 65%, transparent 78%)",
          WebkitMaskImage:
            "radial-gradient(circle, transparent 32%, black 42%, black 65%, transparent 78%)",
        }}
      />

      <motion.div
        animate={{ rotate: -360 }}
        transition={{ duration: rotateDuration + 8, ease: "linear", repeat: Infinity }}
        className="absolute inset-0 rounded-full"
        style={{
          background:
            state === "speaking"
              ? "conic-gradient(from 90deg, transparent, #ffb15e, transparent, #ff5ec4, transparent, #b18cff, transparent)"
              : state === "listening"
                ? "conic-gradient(from 90deg, transparent, #5ee0ff, transparent, #b18cff, transparent, #00d4ff, transparent)"
                : "conic-gradient(from 90deg, transparent, #b18cff, transparent, #ff5ec4, transparent, #5ee0ff, transparent)",
          filter: "blur(30px)",
          opacity: 0.45 + level * 0.25,
          maskImage: "radial-gradient(circle, transparent 36%, black 45%, black 62%, transparent 75%)",
          WebkitMaskImage:
            "radial-gradient(circle, transparent 36%, black 45%, black 62%, transparent 75%)",
        }}
      />
    </div>
  );
}
