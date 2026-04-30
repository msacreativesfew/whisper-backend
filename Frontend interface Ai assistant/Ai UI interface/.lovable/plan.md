
# Voice Assistant Orb — Animated Visual Demo

A single-page interactive showcase of a voice-assistant orb matching the reference image: black sphere with white oval eyes, surrounded by a glowing blue/purple/pink chromatic halo. Pure visual demo (no real audio).

## The Orb
- Black glossy sphere, centered on deep black background
- Multi-layered chromatic halo ring: blue → purple → pink → cyan, with soft bloom and subtle lens-flare leaks (matches reference)
- Two white oval eyes inside the sphere

## Animations

**1. Opening boot animation (Gemini-style)**
- Halo starts as a tiny bright dot → expands outward into the full ring
- Chromatic colors swirl in around the sphere
- Sphere fades up, then eyes pop open with a quick scale
- Plays once on page load (~2s)

**2. Idle state**
- Eyes blink naturally at random intervals (every 3–6s, occasional double-blink)
- Halo gently breathes (subtle scale + opacity pulse)
- Slow color rotation around the ring

**3. Eyes follow cursor**
- Pupils/eye-shapes shift slightly toward mouse position
- Smooth easing, constrained within the sphere
- Subtle head-tilt feel via slight sphere offset

**4. State controls (bottom of screen)**
Three minimal buttons to toggle the orb's mode:
- **Idle** — default blinking + breathing
- **Listening** — concentric soft waves ripple outward from the orb; halo intensifies and pulses with a fake audio rhythm; eyes slightly squint
- **Speaking** — vertical waveform bars appear around the lower halo, animating with a speech-like pattern; halo shimmers brighter; eyes do small expressive movements

## Visual Style
- Pure black background (#000)
- Chromatic palette: electric blue, violet, magenta, cyan
- Heavy use of blur + glow for the halo bloom
- Soft lens flare accents (orange/red leak on one side, like reference)
- Smooth Framer Motion springs for all transitions
- Centered, full-screen, immersive

## Tech
- Single new route component on `/` (homepage)
- SVG + CSS filters for the orb, halo, and waveforms
- Framer Motion for state transitions and boot animation
- Mouse tracking via React state for eye movement
