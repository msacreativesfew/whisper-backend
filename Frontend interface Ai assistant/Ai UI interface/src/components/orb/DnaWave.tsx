import { motion } from "framer-motion";
import { useMemo } from "react";

interface DnaWaveProps {
  active: boolean;
  level: number; // 0..1 audio level
  variant: "listening" | "speaking";
}

/**
 * DNA-style double-helix wave. Two sine strands cross with connecting rungs.
 * Smoothly animates phase + amplitude based on audio level.
 */
export function DnaWave({ active, level, variant }: DnaWaveProps) {
  const points = 80;
  const width = 720;
  const height = 140;
  const xs = useMemo(
    () => Array.from({ length: points }, (_, i) => (i / (points - 1)) * width),
    [],
  );

  const amp = 24 + level * 32;
  const speed = variant === "speaking" ? 2.4 : 1.6;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: active ? 1 : 0, y: active ? 0 : 20 }}
      transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      className="pointer-events-none absolute inset-x-0 mx-auto flex justify-center"
      style={{ bottom: "12%", width: "min(720px, 90vw)" }}
    >
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="w-full"
        style={{ filter: "drop-shadow(0 0 18px rgba(120,150,255,0.55))" }}
      >
        <defs>
          <linearGradient id="dnaA" x1="0" x2="1" y1="0" y2="0">
            <stop offset="0%" stopColor="#00d4ff" />
            <stop offset="50%" stopColor="#b18cff" />
            <stop offset="100%" stopColor="#ff5ec4" />
          </linearGradient>
          <linearGradient id="dnaB" x1="0" x2="1" y1="0" y2="0">
            <stop offset="0%" stopColor="#ff5ec4" />
            <stop offset="50%" stopColor="#7b5cff" />
            <stop offset="100%" stopColor="#3effd1" />
          </linearGradient>
        </defs>

        {/* Connecting rungs */}
        <RungsLayer xs={xs} width={width} height={height} amp={amp} speed={speed} />

        {/* Two helix strands */}
        <StrandPath xs={xs} height={height} amp={amp} speed={speed} phase={0} stroke="url(#dnaA)" />
        <StrandPath xs={xs} height={height} amp={amp} speed={speed} phase={Math.PI} stroke="url(#dnaB)" />
      </svg>
    </motion.div>
  );
}

function StrandPath({
  xs,
  height,
  amp,
  speed,
  phase,
  stroke,
}: {
  xs: number[];
  height: number;
  amp: number;
  speed: number;
  phase: number;
  stroke: string;
}) {
  // Animate via CSS variable on SVG path using SMIL-free approach: use motion to drive phase
  return (
    <motion.path
      initial={false}
      animate={{ "--p": [0, Math.PI * 2] } as any}
      transition={{ duration: 4 / speed, ease: "linear", repeat: Infinity }}
      stroke={stroke}
      strokeWidth={2.5}
      fill="none"
      strokeLinecap="round"
      d={buildPath(xs, height, amp, phase, 0)}
      // Re-render path per frame via key trick: use animate prop on `d`? framer-motion doesn't tween d strings.
      // Instead we drive a CSS variable and rebuild via React state in parent... simpler: use SMIL.
    >
      <animate
        attributeName="d"
        dur={`${4 / speed}s`}
        repeatCount="indefinite"
        values={buildPathFrames(xs, height, amp, phase)}
      />
    </motion.path>
  );
}

function RungsLayer({
  xs,
  width,
  height,
  amp,
  speed,
}: {
  xs: number[];
  width: number;
  height: number;
  amp: number;
  speed: number;
}) {
  // Subset of rungs for clarity
  const rungIndices = xs.map((_, i) => i).filter((i) => i % 4 === 0);
  return (
    <g opacity={0.55}>
      {rungIndices.map((i) => (
        <line
          key={i}
          x1={xs[i]}
          x2={xs[i]}
          y1={height / 2}
          y2={height / 2}
          stroke="rgba(180,200,255,0.7)"
          strokeWidth={1}
          strokeLinecap="round"
        >
          <animate
            attributeName="y1"
            dur={`${4 / speed}s`}
            repeatCount="indefinite"
            values={rungFrames(xs[i], width, height, amp, 0)}
          />
          <animate
            attributeName="y2"
            dur={`${4 / speed}s`}
            repeatCount="indefinite"
            values={rungFrames(xs[i], width, height, amp, Math.PI)}
          />
        </line>
      ))}
    </g>
  );
}

function buildPath(xs: number[], height: number, amp: number, phase: number, t: number) {
  const cy = height / 2;
  const k = (Math.PI * 4) / (xs[xs.length - 1] || 1); // 2 full waves
  let d = "";
  for (let i = 0; i < xs.length; i++) {
    const x = xs[i];
    const y = cy + Math.sin(x * k + phase + t) * amp;
    d += i === 0 ? `M ${x} ${y}` : ` L ${x} ${y}`;
  }
  return d;
}

function buildPathFrames(xs: number[], height: number, amp: number, phase: number) {
  const steps = 24;
  const frames: string[] = [];
  for (let s = 0; s <= steps; s++) {
    const t = (s / steps) * Math.PI * 2;
    frames.push(buildPath(xs, height, amp, phase, t));
  }
  return frames.join(";");
}

function rungFrames(x: number, width: number, height: number, amp: number, phase: number) {
  const cy = height / 2;
  const k = (Math.PI * 4) / width;
  const steps = 24;
  const frames: number[] = [];
  for (let s = 0; s <= steps; s++) {
    const t = (s / steps) * Math.PI * 2;
    frames.push(cy + Math.sin(x * k + phase + t) * amp);
  }
  return frames.join(";");
}