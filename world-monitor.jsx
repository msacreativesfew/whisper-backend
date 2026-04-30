import { useState, useEffect, useRef, useCallback } from "react";
import * as THREE from "three";

// ─── Globe pin locations ────────────────────────────────────────────────────
const NEWS_PINS = [
  { lat: 33.72,  lon:  73.04, city: "Islamabad",   color: "#f97316", local: true,  pulse: true  },
  { lat: 24.86,  lon:  67.01, city: "Karachi",      color: "#f97316", local: true,  pulse: true  },
  { lat: 31.55,  lon:  74.35, city: "Lahore",       color: "#f97316", local: true,  pulse: true  },
  { lat: 32.08,  lon:  72.69, city: "Faisalabad",   color: "#fb923c", local: true,  pulse: false },
  { lat: 40.71,  lon: -74.01, city: "New York",     color: "#0ea5e9", local: false, pulse: true  },
  { lat: 51.51,  lon:  -0.13, city: "London",       color: "#0ea5e9", local: false, pulse: true  },
  { lat: 48.86,  lon:   2.35, city: "Paris",        color: "#0ea5e9", local: false, pulse: false },
  { lat: 35.68,  lon: 139.69, city: "Tokyo",        color: "#0ea5e9", local: false, pulse: true  },
  { lat: 39.91,  lon: 116.39, city: "Beijing",      color: "#22d3ee", local: false, pulse: true  },
  { lat: 55.75,  lon:  37.62, city: "Moscow",       color: "#0ea5e9", local: false, pulse: false },
  { lat: 28.61,  lon:  77.21, city: "New Delhi",    color: "#a855f7", local: false, pulse: true  },
  { lat: 25.20,  lon:  55.27, city: "Dubai",        color: "#22d3ee", local: false, pulse: true  },
  { lat: 31.77,  lon:  35.22, city: "Jerusalem",    color: "#ef4444", local: false, pulse: true  },
  { lat: 30.06,  lon:  31.25, city: "Cairo",        color: "#22d3ee", local: false, pulse: false },
  { lat: -33.87, lon: 151.21, city: "Sydney",       color: "#0ea5e9", local: false, pulse: false },
  { lat: 37.77,  lon: -122.4, city: "San Francisco",color: "#0ea5e9", local: false, pulse: false },
  { lat: 52.52,  lon:  13.40, city: "Berlin",       color: "#0ea5e9", local: false, pulse: false },
  { lat: 41.01,  lon:  28.98, city: "Istanbul",     color: "#22d3ee", local: false, pulse: true  },
  { lat: 1.35,   lon: 103.82, city: "Singapore",    color: "#22d3ee", local: false, pulse: false },
  { lat: -23.55, lon: -46.63, city: "São Paulo",    color: "#0ea5e9", local: false, pulse: false },
];

// Convert lat/lon to 3D vector on sphere
function ll2v(lat, lon, r = 1) {
  const phi   = (90 - lat) * (Math.PI / 180);
  const theta = (lon + 180) * (Math.PI / 180);
  return new THREE.Vector3(
    -r * Math.sin(phi) * Math.cos(theta),
     r * Math.cos(phi),
     r * Math.sin(phi) * Math.sin(theta)
  );
}

const CAT_COLOR = {
  Politics:      "#ef4444",
  Economy:       "#22d3ee",
  Tech:          "#a855f7",
  Conflict:      "#f97316",
  Climate:       "#22c55e",
  Health:        "#ec4899",
  Security:      "#f59e0b",
  Infrastructure:"#3b82f6",
  Environment:   "#22c55e",
  Sports:        "#84cc16",
  Education:     "#06b6d4",
  Defense:       "#dc2626",
};

const FALLBACK = {
  world: [
    { title: "Global AI Governance Summit Opens in Geneva", summary: "World leaders convene to negotiate binding international AI safety standards.", category: "Tech", location: "Geneva, Switzerland", time: "12 min ago" },
    { title: "Middle East Ceasefire Talks Resume in Cairo", summary: "UN mediators restart negotiations with cautious optimism from both sides.", category: "Conflict", location: "Cairo, Egypt", time: "38 min ago" },
    { title: "Federal Reserve Signals Rate Cut Path", summary: "Fed Chair hints at multiple cuts by year-end amid cooling inflation data.", category: "Economy", location: "Washington DC", time: "1h ago" },
    { title: "European Parliament Passes Digital Sovereignty Bill", summary: "Landmark legislation mandates data localisation for critical infrastructure.", category: "Politics", location: "Brussels, EU", time: "2h ago" },
    { title: "SpaceX Launches 200th Starlink Mission", summary: "Cumulative constellation now provides coverage to 100+ countries.", category: "Tech", location: "Cape Canaveral, USA", time: "3h ago" },
  ],
  pakistan: [
    { title: "PM Chairs National Economic Council Session", summary: "Top ministers review GDP targets and foreign exchange reserve strategy.", category: "Economy", location: "Islamabad", time: "22 min ago" },
    { title: "CPEC Phase III Infrastructure Projects Begin", summary: "Ground broken on seven new corridors linking Gwadar to Central Asia.", category: "Infrastructure", location: "Gwadar, Balochistan", time: "55 min ago" },
    { title: "Pakistan-Turkey Defence Pact Expanded", summary: "Both nations sign MoU for co-production of armoured vehicles.", category: "Defense", location: "Ankara / Rawalpindi", time: "1h 30m ago" },
    { title: "PSX Crosses Historic 100,000 Point Milestone", summary: "Analysts credit IMF programme progress and falling inflation for rally.", category: "Economy", location: "Karachi", time: "2h ago" },
    { title: "Monsoon Pre-Season Rains Forecast Early", summary: "PMD warns of above-average rainfall; NDMA activates disaster response.", category: "Climate", location: "Nationwide", time: "4h ago" },
  ],
  islamabad: [
    { title: "CDA Launches 'Green Islamabad 2030' Drive", summary: "50,000 trees to be planted across Margalla Hills and urban sectors.", category: "Environment", location: "Islamabad", time: "8 min ago" },
    { title: "New Metro Line F-9 to Blue Area Opens", summary: "PM inaugurates extended bus rapid transit route serving 200k daily commuters.", category: "Infrastructure", location: "Islamabad", time: "45 min ago" },
    { title: "Islamabad Tops South Asia Livability Index", summary: "Annual survey ranks capital first for safety, greenery, and air quality.", category: "Health", location: "Islamabad", time: "1h ago" },
    { title: "Federal Board of Revenue Headquarters Relocated", summary: "New purpose-built complex in I-9 inaugurated by Finance Minister.", category: "Economy", location: "I-9, Islamabad", time: "2h ago" },
    { title: "PITB Launches AI Skills Bootcamp for Youth", summary: "6,000 seats open for free AI/ML training programme across the capital.", category: "Education", location: "Islamabad", time: "3h ago" },
  ],
};

// ════════════════════════════════════════════════════════════════════════════
export default function WorldMonitor() {
  const [worldNews,     setWorldNews]     = useState([]);
  const [pakNews,       setPakNews]       = useState([]);
  const [isbNews,       setIsbNews]       = useState([]);
  const [loading,       setLoading]       = useState(false);
  const [time,          setTime]          = useState(new Date());
  const [selected,      setSelected]      = useState(null);
  const [tab,           setTab]           = useState("world");
  const [rightTab,      setRightTab]      = useState("isb");
  const [aiQuery,       setAiQuery]       = useState("");
  const [aiResp,        setAiResp]        = useState("");
  const [aiLoading,     setAiLoading]     = useState(false);
  const [ticker,        setTicker]        = useState([]);
  const [zoomVal,       setZoomVal]       = useState(2.6);
  const [filterCat,     setFilterCat]     = useState("All");
  const [searchQ,       setSearchQ]       = useState("");
  const [globeReady,    setGlobeReady]    = useState(false);

  const mountRef    = useRef(null);
  const rendRef     = useRef(null);
  const sceneRef    = useRef(null);
  const camRef      = useRef(null);
  const globeGrp    = useRef(null);
  const frameRef    = useRef(null);
  const dragging    = useRef(false);
  const prevMouse   = useRef({ x: 0, y: 0 });
  const autoRotate  = useRef(true);
  const tickerRef   = useRef(null);

  // ── Clock ──
  useEffect(() => {
    const id = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  // ── Globe setup ──
  useEffect(() => {
    if (!mountRef.current) return;
    const el = mountRef.current;
    const W = el.clientWidth, H = el.clientHeight;

    const scene    = new THREE.Scene();
    sceneRef.current = scene;

    const camera   = new THREE.PerspectiveCamera(45, W / H, 0.1, 500);
    camera.position.z = 2.6;
    camRef.current = camera;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(W, H);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x000000, 0);
    el.appendChild(renderer.domElement);
    rendRef.current = renderer;

    const grp = new THREE.Group();
    globeGrp.current = grp;
    scene.add(grp);

    // ── Earth body ──
    const earthGeo = new THREE.SphereGeometry(1, 64, 64);
    const earthMat = new THREE.MeshPhongMaterial({
      color: new THREE.Color(0x071428),
      emissive: new THREE.Color(0x020a18),
      specular: new THREE.Color(0x112244),
      shininess: 50,
    });
    grp.add(new THREE.Mesh(earthGeo, earthMat));

    // ── Latitude grid ──
    const gridCol = new THREE.Color(0x1a3a6a);
    const addGrid = (points, opacity = 0.35) => {
      const geo = new THREE.BufferGeometry().setFromPoints(points);
      const mat = new THREE.LineBasicMaterial({ color: gridCol, transparent: true, opacity });
      grp.add(new THREE.Line(geo, mat));
    };
    for (let lat = -75; lat <= 75; lat += 15) {
      const pts = [];
      for (let lon = 0; lon <= 362; lon += 3) pts.push(ll2v(lat, lon - 180, 1.002));
      addGrid(pts, lat === 0 ? 0.6 : 0.25);
    }
    for (let lon = 0; lon < 360; lon += 15) {
      const pts = [];
      for (let lat = -90; lat <= 90; lat += 3) pts.push(ll2v(lat, lon - 180, 1.002));
      addGrid(pts, lon === 0 ? 0.5 : 0.2);
    }

    // ── Tropics / Polar lines ──
    [23.5, -23.5, 66.5, -66.5].forEach(lat => {
      const pts = [];
      for (let lon = 0; lon <= 362; lon += 3) pts.push(ll2v(lat, lon - 180, 1.003));
      const mat = new THREE.LineBasicMaterial({ color: new THREE.Color(lat > 0 ? 0x2255aa : 0x225566), transparent: true, opacity: 0.4 });
      grp.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), mat));
    });

    // ── Atmosphere glow ──
    const addAtmos = (r, col, op, side = THREE.FrontSide) => {
      const g = new THREE.SphereGeometry(r, 32, 32);
      const m = new THREE.MeshPhongMaterial({ color: new THREE.Color(col), transparent: true, opacity: op, side });
      scene.add(new THREE.Mesh(g, m));
    };
    addAtmos(1.06, 0x0044cc, 0.07, THREE.BackSide);
    addAtmos(1.12, 0x003399, 0.04, THREE.BackSide);
    addAtmos(1.18, 0x002266, 0.02, THREE.BackSide);

    // ── Pakistan highlight band ──
    for (let lon = 60; lon <= 78; lon += 2) {
      for (let lat = 22; lat <= 38; lat += 2) {
        const p = ll2v(lat, lon, 1.0015);
        const dot = new THREE.Mesh(
          new THREE.SphereGeometry(0.006, 4, 4),
          new THREE.MeshBasicMaterial({ color: new THREE.Color(0xf97316), transparent: true, opacity: 0.15 })
        );
        dot.position.copy(p);
        grp.add(dot);
      }
    }

    // ── Stars ──
    const starPos = [];
    for (let i = 0; i < 4000; i++) {
      const r = 80 + Math.random() * 120;
      const th = Math.random() * Math.PI * 2;
      const ph = Math.acos(2 * Math.random() - 1);
      starPos.push(r * Math.sin(ph) * Math.cos(th), r * Math.sin(ph) * Math.sin(th), r * Math.cos(ph));
    }
    const starGeo = new THREE.BufferGeometry();
    starGeo.setAttribute("position", new THREE.Float32BufferAttribute(starPos, 3));
    scene.add(new THREE.Points(starGeo, new THREE.PointsMaterial({ color: 0xffffff, size: 0.2, transparent: true, opacity: 0.75 })));

    // ── News pins ──
    const pulseRings = [];
    NEWS_PINS.forEach(pin => {
      const pos = ll2v(pin.lat, pin.lon, 1.025);
      // Pin sphere
      const pinMesh = new THREE.Mesh(
        new THREE.SphereGeometry(0.018, 8, 8),
        new THREE.MeshBasicMaterial({ color: new THREE.Color(pin.color) })
      );
      pinMesh.position.copy(pos);
      grp.add(pinMesh);

      // Vertical line from surface
      const linePts = [ll2v(pin.lat, pin.lon, 1.0), ll2v(pin.lat, pin.lon, 1.025)];
      const lineGeo = new THREE.BufferGeometry().setFromPoints(linePts);
      const lineMat = new THREE.LineBasicMaterial({ color: new THREE.Color(pin.color), transparent: true, opacity: 0.5 });
      grp.add(new THREE.Line(lineGeo, lineMat));

      if (pin.pulse) {
        // Pulse ring
        const ringGeo = new THREE.RingGeometry(0.022, 0.035, 20);
        const ringMat = new THREE.MeshBasicMaterial({ color: new THREE.Color(pin.color), transparent: true, opacity: 0.7, side: THREE.DoubleSide });
        const ring = new THREE.Mesh(ringGeo, ringMat);
        ring.position.copy(pos);
        ring.lookAt(new THREE.Vector3(0, 0, 0));
        ring.userData = { phase: Math.random() * Math.PI * 2 };
        grp.add(ring);
        pulseRings.push(ring);
      }
    });

    // ── Lights ──
    scene.add(new THREE.AmbientLight(0x223355, 2.5));
    const sun = new THREE.DirectionalLight(0x7799ff, 3);
    sun.position.set(5, 3, 5);
    scene.add(sun);
    const backLight = new THREE.DirectionalLight(0x001133, 1);
    backLight.position.set(-5, -2, -3);
    scene.add(backLight);

    // ── Animate ──
    let t = 0;
    const animate = () => {
      frameRef.current = requestAnimationFrame(animate);
      t += 0.016;
      if (autoRotate.current) grp.rotation.y += 0.0025;
      pulseRings.forEach(r => {
        const s = 1 + 0.7 * Math.abs(Math.sin(t * 1.8 + r.userData.phase));
        r.scale.setScalar(s);
        r.material.opacity = 0.7 * (1 - Math.abs(Math.sin(t * 1.8 + r.userData.phase)) * 0.8);
      });
      renderer.render(scene, camera);
    };
    animate();
    setGlobeReady(true);

    // ── Resize ──
    const onResize = () => {
      if (!el) return;
      const w = el.clientWidth, h = el.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener("resize", onResize);

    // ── Mouse drag ──
    const onDown = e => { dragging.current = true; autoRotate.current = false; prevMouse.current = { x: e.clientX, y: e.clientY }; };
    const onMove = e => {
      if (!dragging.current) return;
      const dx = e.clientX - prevMouse.current.x;
      const dy = e.clientY - prevMouse.current.y;
      grp.rotation.y += dx * 0.004;
      grp.rotation.x = Math.max(-1.2, Math.min(1.2, grp.rotation.x + dy * 0.004));
      prevMouse.current = { x: e.clientX, y: e.clientY };
    };
    const onUp = () => { dragging.current = false; setTimeout(() => { autoRotate.current = true; }, 3000); };
    const onWheel = e => {
      camera.position.z = Math.max(1.4, Math.min(7, camera.position.z + e.deltaY * 0.004));
      setZoomVal(+camera.position.z.toFixed(2));
    };

    renderer.domElement.addEventListener("mousedown", onDown);
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    renderer.domElement.addEventListener("wheel", onWheel, { passive: true });

    return () => {
      cancelAnimationFrame(frameRef.current);
      window.removeEventListener("resize", onResize);
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
      if (el.contains(renderer.domElement)) el.removeChild(renderer.domElement);
      renderer.dispose();
    };
  }, []);

  // ── Zoom buttons ──
  const doZoom = dir => {
    if (!camRef.current) return;
    camRef.current.position.z = Math.max(1.4, Math.min(7, camRef.current.position.z + dir * 0.35));
    setZoomVal(+camRef.current.position.z.toFixed(2));
  };

  // ── Fetch news ──
  const fetchNews = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "claude-sonnet-4-20250514",
          max_tokens: 1000,
          tools: [{ type: "web_search_20250305", name: "web_search" }],
          messages: [{
            role: "user",
            content: `Search for today's real breaking news: (1) top 5 world headlines, (2) top 5 Pakistan news, (3) top 5 Islamabad local news — date is April 21 2026. Return ONLY a single valid JSON object, no markdown fences, no extra text:
{"world":[{"title":"...","summary":"one sentence","category":"Politics|Economy|Tech|Conflict|Climate|Health|Defense|Security","location":"City, Country","time":"X min ago"}],"pakistan":[same],"islamabad":[same 5 items with location as Islamabad neighborhood]}`
          }]
        })
      });
      const data = await res.json();
      const fullText = data.content.filter(b => b.type === "text").map(b => b.text).join("\n");
      const match = fullText.match(/\{[\s\S]*\}/);
      if (match) {
        const parsed = JSON.parse(match[0]);
        const w = parsed.world    || FALLBACK.world;
        const p = parsed.pakistan || FALLBACK.pakistan;
        const i = parsed.islamabad|| FALLBACK.islamabad;
        setWorldNews(w); setPakNews(p); setIsbNews(i);
        setTicker([...w, ...p, ...i].map(n => n.title));
      } else throw new Error("no json");
    } catch {
      setWorldNews(FALLBACK.world);
      setPakNews(FALLBACK.pakistan);
      setIsbNews(FALLBACK.islamabad);
      setTicker([...FALLBACK.world, ...FALLBACK.pakistan, ...FALLBACK.islamabad].map(n => n.title));
    }
    setLoading(false);
  }, []);

  useEffect(() => { fetchNews(); }, [fetchNews]);

  // ── AI Assistant ──
  const askAI = async () => {
    if (!aiQuery.trim() || aiLoading) return;
    setAiLoading(true); setAiResp("");
    try {
      const res = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "claude-sonnet-4-20250514",
          max_tokens: 1000,
          tools: [{ type: "web_search_20250305", name: "web_search" }],
          messages: [{
            role: "user",
            content: `You are a world news intelligence analyst. The user asks: "${aiQuery}". Search for the latest info and give a concise, expert 2-3 paragraph analysis. Prioritize Pakistan/Islamabad context where relevant.`
          }]
        })
      });
      const data = await res.json();
      const text = data.content.filter(b => b.type === "text").map(b => b.text).join("\n");
      setAiResp(text || "No response from AI analyst.");
    } catch { setAiResp("Network error. Please retry."); }
    setAiLoading(false);
  };

  // ── Derived ──
  const tabMap   = { world: worldNews, pakistan: pakNews, islamabad: isbNews };
  const cats     = ["All", ...new Set((tabMap[tab] || []).map(n => n.category))];
  const filtered = (tabMap[tab] || []).filter(n =>
    (filterCat === "All" || n.category === filterCat) &&
    (searchQ === "" || n.title.toLowerCase().includes(searchQ.toLowerCase()) || n.location.toLowerCase().includes(searchQ.toLowerCase()))
  );

  const pkrTime = time.toLocaleTimeString("en-PK", { timeZone: "Asia/Karachi", hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false });
  const pkrDate = time.toLocaleDateString("en-PK", { timeZone: "Asia/Karachi", weekday: "long", month: "long", day: "numeric", year: "numeric" });
  const utcTime = time.toLocaleTimeString("en-US", { timeZone: "UTC", hour: "2-digit", minute: "2-digit", hour12: false });

  const allCount = worldNews.length + pakNews.length + isbNews.length;

  return (
    <div style={{ width:"100%", height:"100vh", background:"#020917", color:"#e2e8f0", display:"flex", flexDirection:"column", overflow:"hidden", position:"relative", fontFamily:"'Rajdhani', 'Barlow Condensed', sans-serif" }}>

      {/* Fonts */}
      <link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&display=swap" rel="stylesheet" />

      {/* Scan lines overlay */}
      <div style={{ position:"absolute", inset:0, backgroundImage:"repeating-linear-gradient(0deg,transparent,transparent 3px,rgba(8,120,255,0.012) 3px,rgba(8,120,255,0.012) 4px)", pointerEvents:"none", zIndex:200 }} />

      {/* ── TOP HEADER ── */}
      <header style={{ height:52, background:"rgba(2,9,23,0.98)", borderBottom:"1px solid rgba(14,165,233,0.25)", display:"flex", alignItems:"center", padding:"0 18px", gap:14, flexShrink:0, zIndex:10 }}>

        {/* Logo */}
        <div style={{ display:"flex", alignItems:"center", gap:8, flexShrink:0 }}>
          <div style={{ width:8, height:8, borderRadius:"50%", background:"#ef4444", boxShadow:"0 0 8px #ef4444", animation:"blink 1.2s infinite" }} />
          <span style={{ fontFamily:"'Orbitron',monospace", fontSize:17, fontWeight:900, letterSpacing:3, color:"#0ea5e9" }}>
            WORLD<span style={{ color:"#f97316" }}>MONITOR</span>
          </span>
          <span style={{ fontSize:9, background:"rgba(14,165,233,0.15)", border:"1px solid rgba(14,165,233,0.3)", color:"#0ea5e9", padding:"1px 6px", borderRadius:3, letterSpacing:1, fontFamily:"'Share Tech Mono',monospace" }}>LIVE</span>
        </div>

        {/* Divider */}
        <div style={{ width:1, height:30, background:"rgba(14,165,233,0.2)" }} />

        {/* Time zones */}
        <div style={{ display:"flex", gap:16 }}>
          {[
            { label:"PKT", time: pkrTime, color:"#f97316" },
            { label:"UTC", time: utcTime, color:"#0ea5e9" },
          ].map(z => (
            <div key={z.label} style={{ display:"flex", flexDirection:"column", lineHeight:1 }}>
              <span style={{ fontFamily:"'Share Tech Mono',monospace", fontSize:14, color:z.color, letterSpacing:1 }}>{z.time}</span>
              <span style={{ fontSize:8, color:"#475569", letterSpacing:2 }}>{z.label}</span>
            </div>
          ))}
        </div>

        <div style={{ flex:1 }} />

        {/* Stories count */}
        <div style={{ display:"flex", gap:10, alignItems:"center" }}>
          {[
            { label:"WORLD", val: worldNews.length, color:"#0ea5e9" },
            { label:"PAK",   val: pakNews.length,   color:"#f97316" },
            { label:"ISB",   val: isbNews.length,   color:"#22d3ee" },
          ].map(s => (
            <div key={s.label} style={{ textAlign:"center" }}>
              <div style={{ fontFamily:"'Orbitron',monospace", fontSize:13, color:s.color, fontWeight:700 }}>{s.val}</div>
              <div style={{ fontSize:8, color:"#334155", letterSpacing:1 }}>{s.label}</div>
            </div>
          ))}
        </div>

        <div style={{ width:1, height:30, background:"rgba(14,165,233,0.2)" }} />

        {/* Search */}
        <div style={{ display:"flex", alignItems:"center", background:"rgba(14,165,233,0.07)", border:"1px solid rgba(14,165,233,0.18)", borderRadius:6, padding:"0 10px", gap:6 }}>
          <span style={{ color:"#0ea5e9", fontSize:13 }}>⌕</span>
          <input value={searchQ} onChange={e => setSearchQ(e.target.value)} placeholder="Search all news..." style={{ background:"transparent", border:"none", outline:"none", color:"#e2e8f0", fontSize:12, width:170, fontFamily:"'Rajdhani',sans-serif" }} />
        </div>

        {/* Refresh */}
        <button onClick={fetchNews} disabled={loading} style={{ background: loading ? "rgba(14,165,233,0.08)" : "rgba(249,115,22,0.15)", border:`1px solid ${loading ? "rgba(14,165,233,0.2)" : "rgba(249,115,22,0.4)"}`, color: loading ? "#334155" : "#f97316", padding:"6px 14px", borderRadius:6, cursor:"pointer", fontSize:11, fontWeight:700, fontFamily:"'Rajdhani',sans-serif", letterSpacing:1, transition:"all 0.2s" }}>
          {loading ? "⟳ FETCHING" : "⟳ REFRESH"}
        </button>
      </header>

      {/* ── MAIN BODY ── */}
      <div style={{ flex:1, display:"flex", overflow:"hidden" }}>

        {/* ── LEFT PANEL ── */}
        <aside style={{ width:310, flexShrink:0, borderRight:"1px solid rgba(14,165,233,0.18)", display:"flex", flexDirection:"column", overflow:"hidden", background:"rgba(2,9,23,0.7)" }}>

          {/* Tab bar */}
          <div style={{ display:"flex", borderBottom:"1px solid rgba(14,165,233,0.18)", flexShrink:0 }}>
            {[["world","🌍 WORLD"], ["pakistan","🇵🇰 PAKISTAN"], ["islamabad","📍 ISB"]].map(([k, label]) => (
              <button key={k} onClick={() => { setTab(k); setFilterCat("All"); }} style={{ flex:1, padding:"9px 4px", background: tab === k ? "rgba(14,165,233,0.12)" : "transparent", border:"none", borderBottom: tab === k ? "2px solid #0ea5e9" : "2px solid transparent", color: tab === k ? "#0ea5e9" : "#334155", cursor:"pointer", fontSize:9, fontWeight:700, letterSpacing:0.5, fontFamily:"'Orbitron',monospace", transition:"all 0.15s" }}>
                {label}
              </button>
            ))}
          </div>

          {/* Category filters */}
          <div style={{ display:"flex", gap:4, padding:"8px 10px", flexShrink:0, overflowX:"auto", borderBottom:"1px solid rgba(14,165,233,0.1)" }}>
            {cats.map(c => (
              <button key={c} onClick={() => setFilterCat(c)} style={{ padding:"3px 8px", borderRadius:3, border:`1px solid ${filterCat === c ? (CAT_COLOR[c] || "#0ea5e9") : "rgba(14,165,233,0.15)"}`, background: filterCat === c ? `${CAT_COLOR[c] || "#0ea5e9"}22` : "transparent", color: filterCat === c ? (CAT_COLOR[c] || "#0ea5e9") : "#475569", cursor:"pointer", fontSize:9, fontWeight:700, whiteSpace:"nowrap", letterSpacing:0.5 }}>
                {c}
              </button>
            ))}
          </div>

          {/* News list */}
          <div style={{ flex:1, overflowY:"auto", padding:10 }}>
            {loading ? (
              <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
                {[0,1,2,3].map(i => (
                  <div key={i} style={{ background:"rgba(14,165,233,0.04)", borderRadius:8, padding:14, border:"1px solid rgba(14,165,233,0.08)", animation:"pulse 1.5s infinite" }}>
                    <div style={{ height:10, background:"rgba(14,165,233,0.12)", borderRadius:3, marginBottom:8, width:"80%" }} />
                    <div style={{ height:8, background:"rgba(14,165,233,0.07)", borderRadius:3, width:"55%" }} />
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
                {filtered.map((art, i) => {
                  const cc = CAT_COLOR[art.category] || "#64748b";
                  const isSel = selected === art;
                  return (
                    <div key={i} onClick={() => setSelected(isSel ? null : art)} style={{ background: isSel ? "rgba(14,165,233,0.12)" : "rgba(14,165,233,0.03)", border:`1px solid ${isSel ? "rgba(14,165,233,0.35)" : "rgba(14,165,233,0.08)"}`, borderLeft:`3px solid ${cc}`, borderRadius:8, padding:12, cursor:"pointer", transition:"all 0.18s" }}
                    onMouseEnter={e => { if (!isSel) e.currentTarget.style.background = "rgba(14,165,233,0.07)"; }}
                    onMouseLeave={e => { if (!isSel) e.currentTarget.style.background = "rgba(14,165,233,0.03)"; }}>
                      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:5 }}>
                        <span style={{ background:cc, color:"#000", fontSize:8, fontWeight:700, padding:"1px 5px", borderRadius:2, letterSpacing:0.5 }}>{art.category}</span>
                        <span style={{ color:"#334155", fontSize:9, fontFamily:"'Share Tech Mono',monospace" }}>{art.time}</span>
                      </div>
                      <div style={{ fontSize:13, fontWeight:600, lineHeight:1.35, marginBottom:5, color: isSel ? "#e2e8f0" : "#cbd5e1" }}>{art.title}</div>
                      {isSel && <div style={{ fontSize:11, color:"#64748b", lineHeight:1.6, marginBottom:5 }}>{art.summary}</div>}
                      <div style={{ fontSize:9, color:"#0ea5e9", fontFamily:"'Share Tech Mono',monospace" }}>◈ {art.location}</div>
                    </div>
                  );
                })}
                {filtered.length === 0 && <div style={{ color:"#334155", fontSize:12, textAlign:"center", padding:20 }}>No results found</div>}
              </div>
            )}
          </div>
        </aside>

        {/* ── GLOBE CENTER ── */}
        <div style={{ flex:1, position:"relative", overflow:"hidden" }}>
          <div ref={mountRef} style={{ width:"100%", height:"100%", cursor:"grab" }} />

          {/* Overlay: top label */}
          <div style={{ position:"absolute", top:14, left:14, pointerEvents:"none" }}>
            <div style={{ fontFamily:"'Orbitron',monospace", fontSize:9, color:"rgba(14,165,233,0.45)", letterSpacing:2.5, marginBottom:3 }}>LIVE GLOBAL MONITORING SYSTEM</div>
            <div style={{ fontSize:9, color:"#1e3a5f", fontFamily:"'Share Tech Mono',monospace" }}>Drag to rotate  ·  Scroll / +/− to zoom  ·  Auto-rotate on idle</div>
          </div>

          {/* Globe status rings */}
          <div style={{ position:"absolute", top:14, right:14, display:"flex", flexDirection:"column", gap:4, alignItems:"flex-end", pointerEvents:"none" }}>
            {[
              { label:"GLOBE", ok:globeReady },
              { label:"NEWS",  ok: allCount > 0 },
              { label:"AI",    ok: true },
            ].map(s => (
              <div key={s.label} style={{ display:"flex", alignItems:"center", gap:5 }}>
                <span style={{ fontSize:9, color:"#334155", letterSpacing:1 }}>{s.label}</span>
                <div style={{ width:6, height:6, borderRadius:"50%", background: s.ok ? "#22c55e" : "#ef4444", boxShadow:`0 0 6px ${s.ok ? "#22c55e" : "#ef4444"}` }} />
              </div>
            ))}
          </div>

          {/* Zoom controls */}
          <div style={{ position:"absolute", right:14, bottom:80, display:"flex", flexDirection:"column", gap:3, alignItems:"center" }}>
            {[["+", 1], ["−", -1]].map(([lbl, d]) => (
              <button key={lbl} onClick={() => doZoom(d)} style={{ width:34, height:34, background:"rgba(14,165,233,0.12)", border:"1px solid rgba(14,165,233,0.25)", color:"#0ea5e9", borderRadius:6, cursor:"pointer", fontSize:17, display:"flex", alignItems:"center", justifyContent:"center", fontWeight:700, transition:"all 0.15s" }}
              onMouseEnter={e => e.currentTarget.style.background = "rgba(14,165,233,0.25)"}
              onMouseLeave={e => e.currentTarget.style.background = "rgba(14,165,233,0.12)"}>
                {lbl}
              </button>
            ))}
            <div style={{ fontFamily:"'Share Tech Mono',monospace", fontSize:9, color:"#1e3a5f", marginTop:2 }}>{(7 - zoomVal + 1.4).toFixed(0)}x</div>
          </div>

          {/* Pin legend */}
          <div style={{ position:"absolute", left:14, bottom:14, display:"flex", gap:12, pointerEvents:"none" }}>
            {[
              { color:"#f97316", label:"Pakistan/ISB" },
              { color:"#0ea5e9", label:"World News" },
              { color:"#a855f7", label:"India" },
              { color:"#ef4444", label:"Conflict Zone" },
            ].map(l => (
              <div key={l.label} style={{ display:"flex", alignItems:"center", gap:4 }}>
                <div style={{ width:7, height:7, borderRadius:"50%", background:l.color, boxShadow:`0 0 5px ${l.color}` }} />
                <span style={{ fontSize:9, color:"#334155", fontFamily:"'Share Tech Mono',monospace" }}>{l.label}</span>
              </div>
            ))}
          </div>

          {/* Selected article detail card */}
          {selected && (
            <div style={{ position:"absolute", bottom:14, left:"50%", transform:"translateX(-50%)", width:"min(520px,90%)", background:"rgba(2,9,23,0.97)", border:"1px solid rgba(14,165,233,0.3)", borderRadius:12, padding:16, backdropFilter:"blur(20px)", boxShadow:"0 20px 60px rgba(0,0,0,0.7)" }}>
              <div style={{ display:"flex", justifyContent:"space-between", marginBottom:8 }}>
                <div style={{ display:"flex", gap:6, alignItems:"center" }}>
                  <span style={{ background: CAT_COLOR[selected.category] || "#64748b", color:"#000", fontSize:9, fontWeight:700, padding:"2px 7px", borderRadius:2 }}>{selected.category}</span>
                  <span style={{ fontSize:9, color:"#334155", fontFamily:"'Share Tech Mono',monospace" }}>{selected.time}</span>
                </div>
                <button onClick={() => setSelected(null)} style={{ background:"transparent", border:"none", color:"#475569", cursor:"pointer", fontSize:15 }}>✕</button>
              </div>
              <div style={{ fontSize:15, fontWeight:700, marginBottom:7, lineHeight:1.3 }}>{selected.title}</div>
              <div style={{ fontSize:12, color:"#94a3b8", lineHeight:1.65 }}>{selected.summary}</div>
              <div style={{ display:"flex", gap:14, marginTop:10, fontSize:10, color:"#475569", fontFamily:"'Share Tech Mono',monospace" }}>
                <span>◈ {selected.location}</span>
                <span>◷ {selected.time}</span>
              </div>
              <button onClick={() => { setAiQuery(`Tell me more about: ${selected.title}`); }} style={{ marginTop:10, background:"rgba(249,115,22,0.12)", border:"1px solid rgba(249,115,22,0.3)", color:"#f97316", padding:"6px 14px", borderRadius:6, cursor:"pointer", fontSize:11, fontWeight:700 }}>
                ◆ ANALYSE WITH AI →
              </button>
            </div>
          )}
        </div>

        {/* ── RIGHT PANEL ── */}
        <aside style={{ width:310, flexShrink:0, borderLeft:"1px solid rgba(14,165,233,0.18)", display:"flex", flexDirection:"column", overflow:"hidden", background:"rgba(2,9,23,0.7)" }}>

          {/* Right tabs */}
          <div style={{ display:"flex", borderBottom:"1px solid rgba(14,165,233,0.18)", flexShrink:0 }}>
            {[["isb","📍 LOCAL"], ["ai","◆ AI INTEL"], ["stats","▦ STATS"]].map(([k,l]) => (
              <button key={k} onClick={() => setRightTab(k)} style={{ flex:1, padding:"9px 4px", background: rightTab === k ? "rgba(249,115,22,0.1)" : "transparent", border:"none", borderBottom: rightTab === k ? "2px solid #f97316" : "2px solid transparent", color: rightTab === k ? "#f97316" : "#334155", cursor:"pointer", fontSize:9, fontWeight:700, letterSpacing:0.5, fontFamily:"'Orbitron',monospace", transition:"all 0.15s" }}>
                {l}
              </button>
            ))}
          </div>

          {/* ── ISB LOCAL ── */}
          {rightTab === "isb" && (
            <div style={{ flex:1, overflowY:"auto", padding:10 }}>
              <div style={{ display:"flex", alignItems:"center", gap:6, marginBottom:10 }}>
                <div style={{ width:6, height:6, borderRadius:"50%", background:"#f97316", boxShadow:"0 0 6px #f97316", animation:"blink 1.5s infinite" }} />
                <span style={{ fontFamily:"'Orbitron',monospace", fontSize:9, color:"#f97316", letterSpacing:2 }}>ISLAMABAD LOCAL FEED</span>
              </div>
              <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
                {isbNews.map((art, i) => (
                  <div key={i} onClick={() => setSelected(art)} style={{ background:"rgba(249,115,22,0.04)", border:"1px solid rgba(249,115,22,0.12)", borderLeft:"3px solid #f97316", borderRadius:8, padding:12, cursor:"pointer", transition:"all 0.18s" }}
                  onMouseEnter={e => e.currentTarget.style.background = "rgba(249,115,22,0.1)"}
                  onMouseLeave={e => e.currentTarget.style.background = "rgba(249,115,22,0.04)"}>
                    <div style={{ display:"flex", justifyContent:"space-between", marginBottom:4 }}>
                      <span style={{ background: CAT_COLOR[art.category] || "#64748b", color:"#000", fontSize:8, fontWeight:700, padding:"1px 5px", borderRadius:2 }}>{art.category}</span>
                      <span style={{ color:"#334155", fontSize:9, fontFamily:"'Share Tech Mono',monospace" }}>{art.time}</span>
                    </div>
                    <div style={{ fontSize:12, fontWeight:600, lineHeight:1.35, marginBottom:4 }}>{art.title}</div>
                    <div style={{ fontSize:10, color:"#64748b" }}>{art.summary}</div>
                    <div style={{ fontSize:9, color:"#f97316", marginTop:5, fontFamily:"'Share Tech Mono',monospace" }}>◈ {art.location}</div>
                  </div>
                ))}
                {loading && <div style={{ color:"#334155", textAlign:"center", padding:20, fontSize:11, animation:"pulse 1.5s infinite" }}>Loading local news…</div>}
              </div>
            </div>
          )}

          {/* ── AI INTEL ── */}
          {rightTab === "ai" && (
            <div style={{ flex:1, display:"flex", flexDirection:"column", overflow:"hidden" }}>
              <div style={{ padding:"12px 10px 8px", borderBottom:"1px solid rgba(249,115,22,0.15)", flexShrink:0 }}>
                <div style={{ display:"flex", alignItems:"center", gap:6, marginBottom:8 }}>
                  <div style={{ width:6, height:6, background:"#f97316", borderRadius:"50%", boxShadow:"0 0 6px #f97316" }} />
                  <span style={{ fontFamily:"'Orbitron',monospace", fontSize:9, color:"#f97316", letterSpacing:2 }}>AI INTELLIGENCE ANALYST</span>
                </div>
                <div style={{ display:"flex", gap:6 }}>
                  <input value={aiQuery} onChange={e => setAiQuery(e.target.value)} onKeyDown={e => e.key === "Enter" && askAI()} placeholder="Ask about any story or region…" style={{ flex:1, background:"rgba(249,115,22,0.06)", border:"1px solid rgba(249,115,22,0.2)", borderRadius:6, padding:"8px 10px", color:"#e2e8f0", fontSize:12, outline:"none", fontFamily:"'Rajdhani',sans-serif" }} />
                  <button onClick={askAI} disabled={aiLoading} style={{ background: aiLoading ? "rgba(249,115,22,0.06)" : "rgba(249,115,22,0.2)", border:"1px solid rgba(249,115,22,0.35)", color: aiLoading ? "#475569" : "#f97316", padding:"8px 12px", borderRadius:6, cursor:aiLoading ? "default" : "pointer", fontSize:13, fontWeight:700, transition:"all 0.15s" }}>
                    {aiLoading ? "⟳" : "→"}
                  </button>
                </div>
                <div style={{ display:"flex", gap:4, marginTop:6, flexWrap:"wrap" }}>
                  {["Latest Islamabad news?", "Pakistan economy update", "World conflicts today"].map(q => (
                    <button key={q} onClick={() => setAiQuery(q)} style={{ background:"rgba(249,115,22,0.05)", border:"1px solid rgba(249,115,22,0.15)", color:"#64748b", padding:"2px 7px", borderRadius:3, cursor:"pointer", fontSize:9, fontFamily:"'Rajdhani',sans-serif" }}>
                      {q}
                    </button>
                  ))}
                </div>
              </div>
              <div style={{ flex:1, overflowY:"auto", padding:10 }}>
                {aiLoading && (
                  <div style={{ display:"flex", gap:3, alignItems:"center", color:"#f97316", fontSize:11, padding:"10px 0" }}>
                    <span style={{ animation:"pulse 0.8s infinite" }}>◆</span>
                    <span style={{ animation:"pulse 0.8s 0.2s infinite" }}>◆</span>
                    <span style={{ animation:"pulse 0.8s 0.4s infinite" }}>◆</span>
                    <span style={{ color:"#64748b", marginLeft:4 }}>AI analyst processing…</span>
                  </div>
                )}
                {aiResp && (
                  <div style={{ background:"rgba(249,115,22,0.05)", border:"1px solid rgba(249,115,22,0.15)", borderRadius:8, padding:12, fontSize:12, color:"#94a3b8", lineHeight:1.7 }}>
                    <div style={{ fontFamily:"'Orbitron',monospace", fontSize:8, color:"#f97316", letterSpacing:2, marginBottom:8 }}>◆ INTELLIGENCE BRIEF</div>
                    {aiResp}
                  </div>
                )}
                {!aiResp && !aiLoading && (
                  <div style={{ color:"#1e3a5f", fontSize:12, padding:"20px 0", textAlign:"center", lineHeight:1.8 }}>
                    Ask anything about world events,<br />Pakistan politics, or Islamabad local news.<br />
                    <span style={{ fontSize:10, color:"#111827" }}>Powered by live web search</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ── STATS ── */}
          {rightTab === "stats" && (
            <div style={{ flex:1, overflowY:"auto", padding:10 }}>
              <div style={{ fontFamily:"'Orbitron',monospace", fontSize:9, color:"#0ea5e9", letterSpacing:2, marginBottom:10 }}>◆ MONITORING STATISTICS</div>
              
              {/* Counts */}
              <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:8, marginBottom:12 }}>
                {[
                  { label:"World Stories",    val: worldNews.length, color:"#0ea5e9" },
                  { label:"Pakistan Stories", val: pakNews.length,   color:"#f97316" },
                  { label:"Islamabad Local",  val: isbNews.length,   color:"#22d3ee" },
                  { label:"Countries",        val: 195,              color:"#a855f7" },
                  { label:"Pins Active",      val: NEWS_PINS.length, color:"#22c55e" },
                  { label:"AI Searches",      val: "∞",             color:"#f59e0b" },
                ].map((s,i) => (
                  <div key={i} style={{ background:"rgba(14,165,233,0.04)", border:"1px solid rgba(14,165,233,0.1)", borderRadius:7, padding:"10px 12px" }}>
                    <div style={{ fontFamily:"'Orbitron',monospace", fontSize:20, color:s.color, fontWeight:700 }}>{s.val}</div>
                    <div style={{ fontSize:9, color:"#334155", marginTop:2, letterSpacing:0.5 }}>{s.label}</div>
                  </div>
                ))}
              </div>

              {/* Category breakdown */}
              <div style={{ fontFamily:"'Orbitron',monospace", fontSize:9, color:"#0ea5e9", letterSpacing:2, marginBottom:8 }}>◆ CATEGORY BREAKDOWN</div>
              {Object.entries(
                [...worldNews, ...pakNews, ...isbNews].reduce((acc, n) => { acc[n.category] = (acc[n.category] || 0) + 1; return acc; }, {})
              ).map(([cat, count]) => (
                <div key={cat} style={{ display:"flex", alignItems:"center", gap:8, marginBottom:5 }}>
                  <span style={{ fontSize:10, color:"#475569", width:90, flexShrink:0 }}>{cat}</span>
                  <div style={{ flex:1, height:4, background:"rgba(14,165,233,0.1)", borderRadius:2 }}>
                    <div style={{ width:`${(count / allCount) * 100}%`, height:"100%", background: CAT_COLOR[cat] || "#0ea5e9", borderRadius:2, transition:"width 0.5s" }} />
                  </div>
                  <span style={{ fontSize:10, color: CAT_COLOR[cat] || "#0ea5e9", fontFamily:"'Share Tech Mono',monospace", width:16, textAlign:"right" }}>{count}</span>
                </div>
              ))}

              {/* PKT date */}
              <div style={{ marginTop:14, padding:10, background:"rgba(249,115,22,0.05)", border:"1px solid rgba(249,115,22,0.15)", borderRadius:7 }}>
                <div style={{ fontFamily:"'Orbitron',monospace", fontSize:8, color:"#f97316", letterSpacing:2, marginBottom:4 }}>◆ ISLAMABAD / RAWALPINDI</div>
                <div style={{ fontFamily:"'Share Tech Mono',monospace", fontSize:11, color:"#f97316" }}>{pkrTime}</div>
                <div style={{ fontSize:10, color:"#64748b", marginTop:2 }}>{pkrDate}</div>
              </div>
            </div>
          )}
        </aside>
      </div>

      {/* ── BOTTOM TICKER ── */}
      <div style={{ height:32, background:"rgba(2,9,23,0.98)", borderTop:"1px solid rgba(14,165,233,0.18)", display:"flex", alignItems:"center", overflow:"hidden", flexShrink:0, zIndex:10 }}>
        <div style={{ background:"#ef4444", color:"#fff", padding:"0 10px", height:"100%", display:"flex", alignItems:"center", fontFamily:"'Orbitron',monospace", fontWeight:900, fontSize:9, letterSpacing:2, flexShrink:0 }}>LIVE</div>
        <div style={{ flex:1, overflow:"hidden", position:"relative" }}>
          <div style={{ display:"flex", gap:48, whiteSpace:"nowrap", animation:"ticker 40s linear infinite" }}>
            {ticker.length > 0
              ? [...ticker, ...ticker, ...ticker].map((h, i) => (
                  <span key={i} style={{ fontSize:11, color:"#64748b", fontFamily:"'Rajdhani',sans-serif", letterSpacing:0.3 }}>
                    <span style={{ color:"#0ea5e9", marginRight:4 }}>▶</span>{h}
                  </span>
                ))
              : <span style={{ fontSize:11, color:"#1e3a5f", padding:"0 20px" }}>Loading news ticker…</span>
            }
          </div>
        </div>
        <div style={{ padding:"0 12px", fontFamily:"'Share Tech Mono',monospace", fontSize:9, color:"#1e3a5f", flexShrink:0, borderLeft:"1px solid rgba(14,165,233,0.12)" }}>
          PKT {pkrTime}
        </div>
      </div>

      {/* ── STYLES ── */}
      <style>{`
        @keyframes ticker { from { transform:translateX(0) } to { transform:translateX(-33.33%) } }
        @keyframes blink  { 0%,100%{opacity:1} 50%{opacity:0.3} }
        @keyframes pulse  { 0%,100%{opacity:1} 50%{opacity:0.4} }
        ::-webkit-scrollbar { width:3px }
        ::-webkit-scrollbar-track { background:transparent }
        ::-webkit-scrollbar-thumb { background:rgba(14,165,233,0.25); border-radius:2px }
        * { box-sizing:border-box }
        input::placeholder { color:#1e3a5f }
        canvas { display:block }
      `}</style>
    </div>
  );
}
