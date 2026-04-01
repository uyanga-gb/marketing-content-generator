import { useState, useRef, useEffect } from "react";

const S = {
  container: {
    display: "flex", flexDirection: "column", height: "100%",
    background: "#16162a", borderRadius: 24, overflow: "hidden",
    boxShadow: "0 32px 64px -12px rgba(56, 39, 76, 0.20)",
    border: "1px solid #2a2a4a",
  },
  header: {
    padding: "16px 20px", background: "#1a1a30",
    borderBottom: "1px solid #2a2a4a",
    display: "flex", alignItems: "center", justifyContent: "space-between",
  },
  headerLeft: { display: "flex", alignItems: "center", gap: 12 },
  headerAvatar: {
    width: 40, height: 40, borderRadius: 12, flexShrink: 0,
    background: "linear-gradient(135deg, #5a5ae0, #8a3ae0)",
    display: "flex", alignItems: "center", justifyContent: "center",
    fontSize: 18, color: "#fff",
  },
  headerTitle: { fontSize: 15, fontWeight: 700, color: "#d0d0f0", lineHeight: 1.2 },
  headerStatus: { display: "flex", alignItems: "center", gap: 6, marginTop: 3 },
  statusDot: { width: 7, height: 7, borderRadius: "50%", background: "#34d399", boxShadow: "0 0 6px #34d399" },
  statusText: { fontSize: 11, color: "#6666aa" },
  messages: {
    flex: 1, overflowY: "auto", padding: "20px 20px",
    display: "flex", flexDirection: "column", gap: 16,
  },
  // User bubble: gradient, sharp top-right corner
  userBubble: {
    maxWidth: "82%", padding: "12px 16px",
    borderRadius: 18, borderTopRightRadius: 4,
    fontSize: 14, lineHeight: 1.6,
    alignSelf: "flex-end",
    background: "linear-gradient(135deg, #5a5ae0, #8a3ae0)",
    color: "#fff", whiteSpace: "pre-wrap",
    boxShadow: "0 4px 16px rgba(90, 90, 224, 0.30)",
  },
  // Assistant row: avatar + bubble
  assistantRow: { display: "flex", gap: 10, alignSelf: "flex-start", maxWidth: "88%" },
  assistantAvatar: {
    width: 32, height: 32, borderRadius: 10, flexShrink: 0, alignSelf: "flex-start",
    background: "linear-gradient(135deg, #5a5ae0, #8a3ae0)",
    display: "flex", alignItems: "center", justifyContent: "center",
    fontSize: 14, color: "#fff",
  },
  assistantBubble: {
    padding: "12px 16px",
    borderRadius: 18, borderTopLeftRadius: 4,
    fontSize: 14, lineHeight: 1.6,
    background: "#1e1e3a", color: "#d0d0f0",
    border: "1px solid #2a2a5a",
    whiteSpace: "pre-wrap",
  },
  promptWrap: {
    padding: "14px 16px", background: "#16162a",
    borderTop: "1px solid #2a2a4a",
  },
  promptOuter: {
    position: "relative", borderRadius: 20,
  },
  promptGlow: {
    position: "absolute", inset: -1, borderRadius: 20,
    background: "linear-gradient(135deg, #5a5ae0, #8a3ae0)",
    opacity: 0.4, filter: "blur(4px)",
  },
  promptInner: {
    position: "relative", background: "#1a1a30",
    border: "1px solid #3a3a6a", borderRadius: 20,
    display: "flex", alignItems: "flex-end", padding: "6px 8px", gap: 6,
  },
  textarea: {
    flex: 1, padding: "8px 10px", background: "transparent",
    border: "none", outline: "none", resize: "none",
    color: "#e0e0f0", fontSize: 14, lineHeight: 1.5,
    fontFamily: "inherit", maxHeight: 100, overflowY: "auto",
    minHeight: 36,
  },
  sendBtn: (disabled) => ({
    width: 38, height: 38, borderRadius: 12, border: "none",
    background: disabled ? "#2a2a4a" : "linear-gradient(135deg, #5a5ae0, #8a3ae0)",
    color: disabled ? "#555" : "#fff",
    cursor: disabled ? "default" : "pointer",
    display: "flex", alignItems: "center", justifyContent: "center",
    fontSize: 16, flexShrink: 0,
    boxShadow: disabled ? "none" : "0 4px 12px rgba(90, 90, 224, 0.40)",
  }),
  disclaimer: {
    textAlign: "center", marginTop: 8,
    fontSize: 10, color: "#444466", letterSpacing: "0.3px",
  },
};

export default function ChatInterface({ sessionId, onCollected }) {
  const [messages, setMessages] = useState([
    { role: "assistant", content: "To create the perfect marketing piece, let's co-create your vision together! ✨\n\nFirst — what product or service are you showcasing? Is it fashion, tech, food, wellness, or something else entirely? The more specific you are, the more tailored your final content will be!" },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async () => {
    if (!input.trim() || loading) return;
    const msg = input.trim();
    setInput("");
    setMessages((m) => [...m, { role: "user", content: msg }]);
    setLoading(true);

    try {
      const { sendChat } = await import("../services/api.js");
      const data = await sendChat(sessionId, msg);

      // Strip the <collected_data> block from the reply shown to user
      let displayReply = data.reply;
      if (displayReply.includes("<collected_data>")) {
        displayReply = "Perfect, I have everything I need! Click \"Generate Content\" on the left to create your marketing content.";
      }

      setMessages((m) => [...m, { role: "assistant", content: displayReply }]);

      if (data.phase === "pipeline_ready" && data.collected) {
        onCollected(data.collected);
      }
    } catch (e) {
      setMessages((m) => [...m, { role: "assistant", content: `Error: ${e.message}` }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={S.container}>
      {/* Header */}
      <div style={S.header}>
        <div style={S.headerLeft}>
          <div style={S.headerAvatar}>✦</div>
          <div>
            <div style={S.headerTitle}>AI Content Strategist</div>
            <div style={S.headerStatus}>
              <span style={S.statusDot} />
              <span style={S.statusText}>Online · collecting your brief</span>
            </div>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div style={S.messages}>
        {messages.map((m, i) =>
          m.role === "user" ? (
            <div key={i} style={S.userBubble}>{m.content}</div>
          ) : (
            <div key={i} style={S.assistantRow}>
              <div style={S.assistantAvatar}>✦</div>
              <div style={S.assistantBubble}>{m.content}</div>
            </div>
          )
        )}
        {loading && (
          <div style={S.assistantRow}>
            <div style={S.assistantAvatar}>✦</div>
            <div style={{ ...S.assistantBubble, color: "#6666aa" }}>Thinking…</div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Prompt bar */}
      <div style={S.promptWrap}>
        <div style={S.promptOuter}>
          <div style={S.promptGlow} />
          <div style={S.promptInner}>
            <textarea
              style={S.textarea}
              value={input}
              rows={1}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
              placeholder="Tell the AI what to create…"
            />
            <button
              style={S.sendBtn(loading || !input.trim())}
              onClick={send}
              disabled={loading || !input.trim()}
            >
              ➤
            </button>
          </div>
        </div>
        <div style={S.disclaimer}>
          AI may produce inaccurate results. Review all outputs before publishing.
        </div>
      </div>
    </div>
  );
}
