import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface SettingsPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SettingsPanel({ isOpen, onClose }: SettingsPanelProps) {
  const [activeTab, setActiveTab] = useState<"preferences" | "integrations" | "analytics">("preferences");
  const [voiceSpeed, setVoiceSpeed] = useState(1.0);
  const [responseLength, setResponseLength] = useState("medium");
  const [selectedLanguage, setSelectedLanguage] = useState("en");
  const [privacyMode, setPrivacyMode] = useState(false);

  const languages = [
    { code: "en", name: "English" },
    { code: "es", name: "Español" },
    { code: "fr", name: "Français" },
    { code: "de", name: "Deutsch" },
    { code: "it", name: "Italiano" },
    { code: "pt", name: "Português" },
    { code: "ja", name: "日本語" },
    { code: "zh", name: "简体中文" },
    { code: "ko", name: "한국어" },
    { code: "ru", name: "Русский" },
    { code: "ar", name: "العربية" },
    { code: "hi", name: "हिन्दी" },
  ];

  const integrations = [
    { id: "google_calendar", name: "Google Calendar", icon: "📅", connected: false },
    { id: "gmail", name: "Gmail", icon: "📧", connected: false },
    { id: "slack", name: "Slack", icon: "💬", connected: false },
    { id: "todoist", name: "Todoist", icon: "✓", connected: false },
    { id: "spotify", name: "Spotify", icon: "🎵", connected: false },
  ];

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm"
          />

          {/* Panel */}
          <motion.div
            initial={{ x: "100%", opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: "100%", opacity: 0 }}
            transition={{ type: "spring", damping: 20, stiffness: 300 }}
            className="fixed right-0 top-0 bottom-0 z-50 w-full max-w-md overflow-y-auto bg-gradient-to-b from-slate-900 to-slate-950 shadow-2xl"
          >
            {/* Header */}
            <div className="sticky top-0 border-b border-white/10 bg-slate-900/95 backdrop-blur px-6 py-4">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-white">Settings</h2>
                <button
                  onClick={onClose}
                  className="rounded-lg p-2 text-white/60 transition hover:bg-white/10 hover:text-white"
                >
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Tabs */}
              <div className="mt-4 flex gap-2">
                {["preferences", "integrations", "analytics"].map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab as any)}
                    className={`flex-1 rounded-lg px-3 py-2 text-sm font-medium transition ${
                      activeTab === tab
                        ? "bg-cyan-500/20 text-cyan-300"
                        : "text-white/60 hover:bg-white/5 hover:text-white"
                    }`}
                  >
                    {tab.charAt(0).toUpperCase() + tab.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            {/* Content */}
            <div className="px-6 py-6">
              {/* Preferences Tab */}
              {activeTab === "preferences" && (
                <div className="space-y-6">
                  {/* Language Selection */}
                  <div>
                    <label className="block text-sm font-medium text-white/80 mb-3">Language</label>
                    <div className="grid grid-cols-2 gap-2">
                      {languages.map((lang) => (
                        <button
                          key={lang.code}
                          onClick={() => setSelectedLanguage(lang.code)}
                          className={`rounded-lg px-3 py-2 text-sm transition ${
                            selectedLanguage === lang.code
                              ? "bg-cyan-500/30 border border-cyan-400 text-white"
                              : "border border-white/10 text-white/70 hover:bg-white/5"
                          }`}
                        >
                          {lang.name}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Voice Speed */}
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <label className="text-sm font-medium text-white/80">Voice Speed</label>
                      <span className="text-sm text-cyan-400">{voiceSpeed.toFixed(1)}x</span>
                    </div>
                    <input
                      type="range"
                      min="0.5"
                      max="2.0"
                      step="0.1"
                      value={voiceSpeed}
                      onChange={(e) => setVoiceSpeed(parseFloat(e.target.value))}
                      className="w-full"
                    />
                    <div className="mt-2 flex justify-between text-xs text-white/40">
                      <span>Slow</span>
                      <span>Fast</span>
                    </div>
                  </div>

                  {/* Response Length */}
                  <div>
                    <label className="block text-sm font-medium text-white/80 mb-3">Response Length</label>
                    <div className="space-y-2">
                      {["short", "medium", "long"].map((length) => (
                        <label
                          key={length}
                          className="flex items-center gap-3 cursor-pointer rounded-lg border border-white/10 p-3 transition hover:bg-white/5"
                        >
                          <input
                            type="radio"
                            name="response_length"
                            value={length}
                            checked={responseLength === length}
                            onChange={(e) => setResponseLength(e.target.value)}
                            className="h-4 w-4 text-cyan-500"
                          />
                          <span className="flex-1 text-sm text-white/80 capitalize">{length}</span>
                          <span className="text-xs text-white/40">
                            {length === "short" && "Concise"}
                            {length === "medium" && "Balanced"}
                            {length === "long" && "Detailed"}
                          </span>
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* Privacy Mode */}
                  <div className="flex items-center justify-between rounded-lg border border-white/10 p-4">
                    <div>
                      <p className="text-sm font-medium text-white">Privacy Mode</p>
                      <p className="text-xs text-white/40">Don&apos;t store conversation history</p>
                    </div>
                    <button
                      onClick={() => setPrivacyMode(!privacyMode)}
                      className={`relative h-6 w-11 rounded-full transition ${
                        privacyMode ? "bg-cyan-500" : "bg-white/10"
                      }`}
                    >
                      <motion.div
                        layout
                        className={`absolute top-0.5 h-5 w-5 rounded-full bg-white ${
                          privacyMode ? "right-0.5" : "left-0.5"
                        }`}
                      />
                    </button>
                  </div>
                </div>
              )}

              {/* Integrations Tab */}
              {activeTab === "integrations" && (
                <div className="space-y-3">
                  {integrations.map((integration) => (
                    <div
                      key={integration.id}
                      className="flex items-center justify-between rounded-lg border border-white/10 p-4 hover:bg-white/5 transition"
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-2xl">{integration.icon}</span>
                        <div>
                          <p className="text-sm font-medium text-white">{integration.name}</p>
                          <p className="text-xs text-white/40">
                            {integration.connected ? "Connected" : "Not connected"}
                          </p>
                        </div>
                      </div>
                      <button
                        className={`px-3 py-1 rounded-lg text-sm font-medium transition ${
                          integration.connected
                            ? "bg-red-500/20 text-red-300 hover:bg-red-500/30"
                            : "bg-cyan-500/20 text-cyan-300 hover:bg-cyan-500/30"
                        }`}
                      >
                        {integration.connected ? "Disconnect" : "Connect"}
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Analytics Tab */}
              {activeTab === "analytics" && (
                <div className="space-y-4">
                  <div className="rounded-lg bg-white/5 border border-white/10 p-4">
                    <p className="text-xs text-white/60 mb-2">This Month</p>
                    <p className="text-2xl font-bold text-cyan-400">142 Messages</p>
                    <p className="text-xs text-white/40 mt-2">+23% from last month</p>
                  </div>

                  <div className="rounded-lg bg-white/5 border border-white/10 p-4">
                    <p className="text-xs text-white/60 mb-2">API Usage</p>
                    <div className="space-y-2">
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span className="text-white/80">Groq</span>
                          <span className="text-white/60">45,230 tokens</span>
                        </div>
                        <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                          <div className="h-full w-1/3 bg-cyan-500" />
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span className="text-white/80">ElevenLabs</span>
                          <span className="text-white/60">128k / 500k chars</span>
                        </div>
                        <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                          <div className="h-full w-1/4 bg-purple-500" />
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="rounded-lg bg-white/5 border border-white/10 p-4">
                    <p className="text-xs text-white/60 mb-3">Cost Breakdown</p>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-white/80">API Costs</span>
                        <span className="text-white/60">$2.13</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-white/80">Daily Average</span>
                        <span className="text-white/60">$0.07</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
