import React, { useState, useRef, useEffect, useCallback } from "react";
import { getBrowserApiBase } from "../utils/browserApi";

interface DetectedObject {
  label: string;
  confidence: number;
  bbox: [number, number, number, number];
  timestamp: string;
}

interface VideoSession {
  sessionId: string;
  status: "idle" | "active" | "processing" | "error";
  camera: "front" | "back";
  duration: number;
}

interface Detection {
  sessionId: string;
  summary: string;
  detectedObjects: Record<string, DetectedObject[]>;
  totalDetections: number;
  processingTime: number;
  cameraUsed: string;
}

const VideoCallPanel: React.FC<{ userId: string }> = ({ userId }) => {
  const [session, setSession] = useState<VideoSession | null>(null);
  const [detection, setDetection] = useState<Detection | null>(null);
  const [rememberedObjects, setRememberedObjects] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [customLabel, setCustomLabel] = useState("");
  const [customInfo, setCustomInfo] = useState("");
  const [selectedObject, setSelectedObject] = useState<string | null>(null);

  const apiBase = getBrowserApiBase();
  const videoRef = useRef<HTMLVideoElement>(null);

  // Load remembered objects on mount
  useEffect(() => {
    loadRememberedObjects();
  }, [userId]);

  const loadRememberedObjects = async () => {
    try {
      const response = await fetch(`${apiBase}/video/remembered-objects/${userId}`);
      if (response.ok) {
        const data = await response.json();
        setRememberedObjects(data.objects);
      }
    } catch (e) {
      console.error("[VideoPanel] Failed to load remembered objects:", e);
    }
  };

  const startVideoCall = async (camera: "front" | "back" = "front") => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${apiBase}/video/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          camera,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to start video call");
      }

      const data = await response.json();
      setSession({
        sessionId: data.session_id,
        status: "active",
        camera: data.camera,
        duration: 0,
      });

      // Request camera access
      try {
        await navigator.mediaDevices.getUserMedia({
          video: { facingMode: camera === "back" ? "environment" : "user" },
        });
      } catch (e) {
        console.warn("[VideoPanel] Camera permission denied:", e);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to start video call");
      console.error("[VideoPanel] Start call error:", e);
    } finally {
      setLoading(false);
    }
  };

  const runDetection = async (duration: number = 5) => {
    if (!session) return;

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${apiBase}/video/detect/${session.sessionId}?duration=${duration}`, {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error("Detection failed");
      }

      const data = await response.json();
      setDetection(data);
      setSession((prev) => (prev ? { ...prev, status: "idle" } : null));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Detection failed");
      console.error("[VideoPanel] Detection error:", e);
    } finally {
      setLoading(false);
    }
  };

  const switchCamera = async () => {
    if (!session) return;

    try {
      setLoading(true);
      const response = await fetch(`${apiBase}/video/switch-camera`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: session.sessionId,
          user_id: userId,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setSession((prev) =>
          prev ? { ...prev, camera: data.camera === "front" ? "back" : "front" } : null
        );
      }
    } catch (e) {
      console.error("[VideoPanel] Camera switch error:", e);
    } finally {
      setLoading(false);
    }
  };

  const rememberObject = async (objectLabel: string) => {
    if (!customLabel) {
      setError("Please enter a custom name");
      return;
    }

    try {
      setLoading(true);
      const response = await fetch(`${apiBase}/video/remember-object`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          object_label: objectLabel,
          user_name: customLabel,
          custom_info: customInfo || undefined,
        }),
      });

      if (response.ok) {
        setCustomLabel("");
        setCustomInfo("");
        setSelectedObject(null);
        await loadRememberedObjects();
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to remember object");
    } finally {
      setLoading(false);
    }
  };

  const endVideoCall = async () => {
    if (!session) return;

    try {
      await fetch(`${apiBase}/video/end/${session.sessionId}`, { method: "POST" });
      setSession(null);
      setDetection(null);
    } catch (e) {
      console.error("[VideoPanel] End call error:", e);
    }
  };

  return (
    <div className="video-call-panel">
      <style>{`
        .video-call-panel {
          display: grid;
          gap: 20px;
          padding: 20px;
          background: linear-gradient(135deg, rgba(13, 17, 27, 0.9), rgba(8, 10, 16, 0.94));
          border: 1px solid rgba(77, 231, 255, 0.18);
          border-radius: 24px;
          color: rgba(244, 248, 255, 0.94);
          font-family: "Segoe UI", sans-serif;
        }

        .video-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding-bottom: 12px;
          border-bottom: 1px solid rgba(77, 231, 255, 0.18);
        }

        .video-header h2 {
          margin: 0;
          font-size: 16px;
          letter-spacing: 0.1em;
        }

        .video-status {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          padding: 6px 12px;
          background: rgba(77, 231, 255, 0.1);
          border: 1px solid rgba(77, 231, 255, 0.2);
          border-radius: 999px;
          font-size: 12px;
          text-transform: uppercase;
          letter-spacing: 0.1em;
        }

        .video-status.idle { background: rgba(142, 247, 181, 0.1); color: #8ef7b5; }
        .video-status.active { background: rgba(77, 231, 255, 0.1); color: #4de7ff; }
        .video-status.error { background: rgba(255, 155, 155, 0.1); color: #ff9b9b; }

        .video-status::before {
          content: "";
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: currentColor;
          animation: pulse 2s infinite;
        }

        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }

        .video-controls {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
          gap: 10px;
        }

        .btn {
          padding: 12px 16px;
          background: rgba(77, 231, 255, 0.1);
          border: 1px solid rgba(77, 231, 255, 0.2);
          border-radius: 12px;
          color: #4de7ff;
          cursor: pointer;
          font-size: 12px;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.1em;
          transition: all 0.3s ease;
        }

        .btn:hover { background: rgba(77, 231, 255, 0.2); transform: translateY(-2px); }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .btn.primary { background: rgba(77, 231, 255, 0.2); }
        .btn.danger { background: rgba(255, 99, 214, 0.1); color: #ff63d6; border-color: rgba(255, 99, 214, 0.2); }

        .detection-result {
          display: grid;
          gap: 12px;
          padding: 16px;
          background: rgba(255, 255, 255, 0.02);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 16px;
        }

        .summary {
          font-size: 14px;
          line-height: 1.6;
          color: rgba(244, 248, 255, 0.92);
          padding: 12px;
          background: rgba(77, 231, 255, 0.05);
          border-left: 3px solid #4de7ff;
          border-radius: 8px;
        }

        .objects-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
          gap: 10px;
        }

        .object-card {
          padding: 12px;
          background: rgba(156, 125, 255, 0.08);
          border: 1px solid rgba(156, 125, 255, 0.2);
          border-radius: 12px;
          cursor: pointer;
          transition: all 0.3s ease;
          text-align: center;
        }

        .object-card:hover {
          background: rgba(156, 125, 255, 0.15);
          border-color: rgba(156, 125, 255, 0.4);
          transform: translateY(-2px);
        }

        .object-label {
          font-size: 13px;
          font-weight: 600;
          color: #9c7dff;
        }

        .object-confidence {
          font-size: 11px;
          color: rgba(244, 248, 255, 0.58);
          margin-top: 4px;
        }

        .memory-section {
          display: grid;
          gap: 12px;
          padding: 16px;
          background: rgba(255, 255, 255, 0.02);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 16px;
        }

        .memory-section h3 {
          margin: 0 0 8px;
          font-size: 12px;
          text-transform: uppercase;
          letter-spacing: 0.1em;
          color: rgba(244, 248, 255, 0.58);
        }

        .input-group {
          display: grid;
          gap: 8px;
        }

        .input-group input {
          padding: 10px 12px;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(77, 231, 255, 0.2);
          border-radius: 8px;
          color: rgba(244, 248, 255, 0.92);
          font-family: inherit;
          font-size: 12px;
        }

        .input-group input::placeholder {
          color: rgba(244, 248, 255, 0.3);
        }

        .remembered-list {
          display: grid;
          gap: 8px;
          max-height: 200px;
          overflow-y: auto;
        }

        .remembered-item {
          padding: 10px 12px;
          background: rgba(142, 247, 181, 0.08);
          border: 1px solid rgba(142, 247, 181, 0.2);
          border-radius: 8px;
          font-size: 12px;
        }

        .remembered-item strong {
          color: #8ef7b5;
        }

        .error-message {
          padding: 12px 16px;
          background: rgba(255, 99, 214, 0.1);
          border: 1px solid rgba(255, 99, 214, 0.2);
          border-radius: 8px;
          color: #ff9b9b;
          font-size: 12px;
        }

        .stats {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
          gap: 10px;
          padding: 12px;
          background: rgba(255, 255, 255, 0.02);
          border-radius: 8px;
        }

        .stat {
          text-align: center;
        }

        .stat-value {
          font-size: 20px;
          font-weight: 700;
          color: #4de7ff;
        }

        .stat-label {
          font-size: 10px;
          text-transform: uppercase;
          letter-spacing: 0.1em;
          color: rgba(244, 248, 255, 0.58);
          margin-top: 4px;
        }
      `}</style>

      <div className="video-header">
        <h2>📹 Video Call with Object Detection</h2>
        <div className={`video-status ${session?.status || "idle"}`}>
          {session ? `${session.camera} camera` : "disconnected"}
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}

      {!session ? (
        <div className="video-controls">
          <button className="btn primary" onClick={() => startVideoCall("front")} disabled={loading}>
            {loading ? "Starting..." : "Start (Front Camera)"}
          </button>
          <button className="btn primary" onClick={() => startVideoCall("back")} disabled={loading}>
            {loading ? "Starting..." : "Start (Back Camera)"}
          </button>
        </div>
      ) : (
        <>
          <div className="video-controls">
            <button className="btn" onClick={() => runDetection(5)} disabled={loading}>
              {loading ? "Detecting..." : "Detect (5s)"}
            </button>
            <button className="btn" onClick={() => runDetection(10)} disabled={loading}>
              {loading ? "Detecting..." : "Detect (10s)"}
            </button>
            <button className="btn" onClick={switchCamera} disabled={loading}>
              Switch Camera
            </button>
            <button className="btn danger" onClick={endVideoCall}>
              End Call
            </button>
          </div>

          {detection && (
            <>
              <div className="detection-result">
                <div className="summary">
                  <strong>Summary:</strong> {detection.summary}
                </div>

                {detection.totalDetections > 0 && (
                  <>
                    <div className="stats">
                      <div className="stat">
                        <div className="stat-value">{detection.totalDetections}</div>
                        <div className="stat-label">Objects Detected</div>
                      </div>
                      <div className="stat">
                        <div className="stat-value">{detection.processingTime.toFixed(1)}s</div>
                        <div className="stat-label">Processing Time</div>
                      </div>
                    </div>

                    <div className="objects-grid">
                      {Object.entries(detection.detectedObjects).map(([label, objects]) => (
                        <div
                          key={label}
                          className="object-card"
                          onClick={() => setSelectedObject(label)}
                        >
                          <div className="object-label">{label}</div>
                          <div className="object-confidence">
                            {(objects[0].confidence * 100).toFixed(0)}% confident
                          </div>
                        </div>
                      ))}
                    </div>
                  </>
                )}
              </div>

              {selectedObject && (
                <div className="memory-section">
                  <h3>Learn custom name for "{selectedObject}"</h3>
                  <div className="input-group">
                    <input
                      type="text"
                      placeholder={`e.g., "My Laptop"`}
                      value={customLabel}
                      onChange={(e) => setCustomLabel(e.target.value)}
                    />
                    <input
                      type="text"
                      placeholder={`Additional info (optional)`}
                      value={customInfo}
                      onChange={(e) => setCustomInfo(e.target.value)}
                    />
                    <button
                      className="btn primary"
                      onClick={() => rememberObject(selectedObject)}
                      disabled={loading || !customLabel}
                    >
                      Remember This
                    </button>
                  </div>
                </div>
              )}
            </>
          )}

          {Object.keys(rememberedObjects).length > 0 && (
            <div className="memory-section">
              <h3>Your Remembered Objects</h3>
              <div className="remembered-list">
                {Object.entries(rememberedObjects).map(([label, data]) => (
                  <div key={label} className="remembered-item">
                    <strong>{label}</strong> → {data.user_name}
                    {data.custom_info && ` (${data.custom_info})`}
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default VideoCallPanel;
