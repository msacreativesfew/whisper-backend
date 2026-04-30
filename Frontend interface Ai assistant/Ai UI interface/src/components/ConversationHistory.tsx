import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

interface Conversation {
  id: string;
  title: string;
  created_at: Date;
  message_count: number;
  messages?: Message[];
}

interface ConversationHistoryProps {
  isOpen: boolean;
  onClose: () => void;
  conversations: Conversation[];
  onSelectConversation: (conversation: Conversation) => void;
  currentConversationId?: string;
}

export function ConversationHistory({
  isOpen,
  onClose,
  conversations,
  onSelectConversation,
  currentConversationId,
}: ConversationHistoryProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedConversation, setExpandedConversation] = useState<string | null>(null);

  const filteredConversations = conversations.filter((conv) =>
    conv.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

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
            initial={{ x: "-100%", opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: "-100%", opacity: 0 }}
            transition={{ type: "spring", damping: 20, stiffness: 300 }}
            className="fixed left-0 top-0 bottom-0 z-50 w-full max-w-sm overflow-y-auto bg-gradient-to-b from-slate-900 to-slate-950 shadow-2xl"
          >
            {/* Header */}
            <div className="sticky top-0 border-b border-white/10 bg-slate-900/95 backdrop-blur px-4 py-4">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-white">Conversations</h2>
                <button
                  onClick={onClose}
                  className="rounded-lg p-2 text-white/60 transition hover:bg-white/10 hover:text-white"
                >
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                </button>
              </div>

              {/* Search */}
              <div className="relative">
                <input
                  type="text"
                  placeholder="Search conversations..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full rounded-lg bg-white/10 border border-white/20 px-3 py-2 text-sm text-white placeholder-white/40 transition focus:border-cyan-400 focus:outline-none focus:ring-1 focus:ring-cyan-400"
                />
                <svg className="absolute right-3 top-2.5 h-4 w-4 text-white/40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
            </div>

            {/* Conversations List */}
            <div className="px-2 py-4">
              {filteredConversations.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <p className="text-white/60 text-sm">No conversations found</p>
                  <p className="text-white/40 text-xs mt-1">Start a new conversation to begin</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {filteredConversations.map((conversation) => (
                    <div
                      key={conversation.id}
                      className={`rounded-lg border transition ${
                        currentConversationId === conversation.id
                          ? "border-cyan-400/50 bg-cyan-500/10"
                          : "border-white/10 hover:bg-white/5"
                      }`}
                    >
                      {/* Conversation Header */}
                      <button
                        onClick={() => {
                          onSelectConversation(conversation);
                          setExpandedConversation(
                            expandedConversation === conversation.id ? null : conversation.id
                          );
                        }}
                        className="w-full px-4 py-3 text-left flex items-center justify-between"
                      >
                        <div className="flex-1 min-w-0">
                          <h3 className="text-sm font-medium text-white truncate">{conversation.title}</h3>
                          <p className="text-xs text-white/40 mt-1">
                            {conversation.message_count} messages
                          </p>
                          <p className="text-xs text-white/30 mt-0.5">
                            {new Date(conversation.created_at).toLocaleDateString()}
                          </p>
                        </div>
                        <motion.div
                          animate={{
                            rotate: expandedConversation === conversation.id ? 180 : 0,
                          }}
                          className="ml-2 flex-shrink-0"
                        >
                          <svg className="h-4 w-4 text-white/40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                          </svg>
                        </motion.div>
                      </button>

                      {/* Expanded Messages */}
                      <AnimatePresence>
                        {expandedConversation === conversation.id && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: "auto", opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.2 }}
                            className="border-t border-white/10 overflow-hidden"
                          >
                            <div className="px-4 py-3 max-h-48 overflow-y-auto space-y-3 text-xs">
                              {conversation.messages && conversation.messages.length > 0 ? (
                                conversation.messages.slice(-5).map((msg) => (
                                  <div key={msg.id} className={msg.role === "user" ? "text-right" : ""}>
                                    <div
                                      className={`inline-block max-w-[80%] rounded-lg px-3 py-2 ${
                                        msg.role === "user"
                                          ? "bg-cyan-500/30 text-cyan-200"
                                          : "bg-white/10 text-white/80"
                                      }`}
                                    >
                                      {msg.content}
                                    </div>
                                  </div>
                                ))
                              ) : (
                                <p className="text-white/40 text-center py-2">No messages yet</p>
                              )}
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>

                      {/* Actions */}
                      <div className="border-t border-white/10 px-4 py-2 flex gap-2">
                        <button className="flex-1 text-xs rounded px-2 py-1.5 bg-white/5 text-white/60 hover:bg-white/10 transition">
                          Resume
                        </button>
                        <button className="flex-1 text-xs rounded px-2 py-1.5 bg-red-500/10 text-red-300/60 hover:bg-red-500/20 transition">
                          Delete
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="border-t border-white/10 bg-slate-900/50 px-4 py-3 sticky bottom-0">
              <button className="w-full rounded-lg bg-cyan-500/20 px-4 py-2 text-sm font-medium text-cyan-300 transition hover:bg-cyan-500/30">
                + New Conversation
              </button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
