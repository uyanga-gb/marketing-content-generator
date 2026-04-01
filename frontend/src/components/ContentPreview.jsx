import { useState } from "react";

const S = {
  wrap: { display: "flex", flexDirection: "column", gap: 20 },
  card: {
    background: "#16162a", borderRadius: 20, padding: 20, border: "1px solid #2a2a4a",
    boxShadow: "0 16px 32px rgba(56, 39, 76, 0.15)",
  },
  heading: { fontSize: 11, fontWeight: 700, color: "#8888cc", letterSpacing: 2, marginBottom: 14 },
  planGrid: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 },
  planItem: {
    background: "#1e1e3a", borderRadius: 12, padding: "10px 14px",
    boxShadow: "0 4px 12px rgba(56, 39, 76, 0.10)",
  },
  planLabel: { fontSize: 11, color: "#6666aa", marginBottom: 4, textTransform: "uppercase", letterSpacing: 1 },
  planValue: { fontSize: 13, color: "#d0d0f0", lineHeight: 1.4 },
  tabRow: { display: "flex", gap: 8, marginBottom: 14 },
  tab: (active) => ({
    padding: "6px 18px", borderRadius: 50, border: "none", cursor: "pointer",
    background: active ? "linear-gradient(135deg, #5a5ae0, #8a3ae0)" : "#1e1e3a",
    color: active ? "#fff" : "#888",
    fontSize: 13, fontWeight: active ? 700 : 400,
    boxShadow: active ? "0 4px 12px rgba(90, 90, 224, 0.3)" : "none",
  }),
  captionBox: { background: "#1e1e3a", borderRadius: 12, padding: 16 },
  hookLine: { fontSize: 13, color: "#aaaa44", fontWeight: 600, marginBottom: 10 },
  captionText: { fontSize: 13, color: "#d0d0f0", lineHeight: 1.7, whiteSpace: "pre-wrap" },
  charCount: { fontSize: 11, color: "#6666aa", marginTop: 8, textAlign: "right" },
  revisionBadge: {
    display: "inline-block", padding: "2px 8px", borderRadius: 10,
    background: "#2a2a5a", color: "#aaaaff", fontSize: 11, marginLeft: 8,
  },
  actionRow: { display: "flex", gap: 8, marginTop: 10 },
  copyBtn: {
    padding: "6px 16px", borderRadius: 50, border: "1px solid #3a3a6a",
    background: "transparent", color: "#8888cc", cursor: "pointer", fontSize: 12, fontWeight: 600,
  },
  refineToggle: {
    padding: "6px 16px", borderRadius: 50, border: "1px solid #5a3a9a",
    background: "transparent", color: "#aa88ee", cursor: "pointer", fontSize: 12, fontWeight: 600,
  },
  feedbackArea: {
    marginTop: 12, padding: 12, background: "#1a1a30",
    borderRadius: 12, border: "1px solid #3a2a5a",
  },
  feedbackLabel: { fontSize: 11, color: "#8888aa", marginBottom: 8 },
  feedbackInput: {
    width: "100%", padding: "8px 12px", borderRadius: 6,
    background: "#16162a", border: "1px solid #3a3a6a",
    color: "#e0e0f0", fontSize: 13, outline: "none",
    resize: "vertical", minHeight: 60, fontFamily: "inherit",
  },
  submitBtn: (loading) => ({
    marginTop: 8, padding: "7px 20px", borderRadius: 50, border: "none",
    background: loading ? "#333" : "linear-gradient(135deg, #5a3ae0, #8a3ae0)",
    color: loading ? "#666" : "#fff",
    cursor: loading ? "default" : "pointer", fontSize: 13, fontWeight: 600,
    boxShadow: loading ? "none" : "0 6px 16px rgba(90, 58, 224, 0.35)",
  }),
  historyToggle: { fontSize: 11, color: "#6666aa", cursor: "pointer", marginTop: 8, display: "inline-block" },
  historyBox: {
    marginTop: 8, padding: 10, background: "#12122a",
    borderRadius: 6, border: "1px solid #2a2a4a",
  },
  historyItem: { marginBottom: 10, paddingBottom: 10, borderBottom: "1px solid #2a2a4a" },
  historyLabel: { fontSize: 11, color: "#6666aa", marginBottom: 4 },
  historyText: { fontSize: 12, color: "#888899", lineHeight: 1.5 },
};

const QUICK_PROMPTS = [
  "Make it shorter",
  "More playful tone",
  "Stronger CTA",
  "Add more hashtags",
  "More professional",
];

function CaptionsCard({ captions, sessionId, onCaptionsUpdated }) {
  const [active, setActive] = useState(0);
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [loading, setLoading] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [histories, setHistories] = useState({});

  const cap = captions[active];

  const copy = () => navigator.clipboard.writeText(cap.caption);

  const handleRefine = async (text) => {
    const f = text || feedback;
    if (!f.trim() || loading) return;
    setLoading(true);
    try {
      const res = await fetch(`/session/${sessionId}/refine/caption`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ variation_index: active, feedback: f }),
      });
      const data = await res.json();
      // Merge new revision history
      setHistories((h) => ({ ...h, ...data.revision_history }));
      onCaptionsUpdated(data.captions, data.validation);
      setFeedback("");
      setShowFeedback(false);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const currentHistory = histories[String(active)] || [];

  return (
    <div style={S.card}>
      <div style={S.heading}>CAPTIONS</div>
      <div style={S.tabRow}>
        {captions.map((c, i) => (
          <button key={i} style={S.tab(i === active)} onClick={() => { setActive(i); setShowFeedback(false); setShowHistory(false); }}>
            {c.label}
            {c.revision && <span style={S.revisionBadge}>v{c.revision}</span>}
          </button>
        ))}
      </div>

      <div style={S.captionBox}>
        <div style={S.hookLine}>Hook: {cap.hook}</div>
        <div style={S.captionText}>{cap.caption}</div>
        <div style={S.charCount}>{cap.char_count} characters</div>
      </div>

      {cap.feedback_applied && (
        <div style={{ marginTop: 8, fontSize: 11, color: "#8888aa" }}>
          Last change: "{cap.feedback_applied}"
        </div>
      )}

      <div style={S.actionRow}>
        <button style={S.copyBtn} onClick={copy}>Copy</button>
        <button style={S.refineToggle} onClick={() => setShowFeedback(!showFeedback)}>
          {showFeedback ? "Cancel" : "✦ Refine this caption"}
        </button>
      </div>

      {showFeedback && (
        <div style={S.feedbackArea}>
          <div style={S.feedbackLabel}>What would you like to change?</div>

          {/* Quick prompt chips */}
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 10 }}>
            {QUICK_PROMPTS.map((p) => (
              <button
                key={p}
                onClick={() => handleRefine(p)}
                style={{
                  padding: "4px 12px", borderRadius: 50, border: "none",
                  background: "#2a2050", color: "#aa88ff",
                  cursor: "pointer", fontSize: 11, fontWeight: 600,
                }}
              >
                {p}
              </button>
            ))}
          </div>

          <textarea
            style={S.feedbackInput}
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder='e.g. "Make it under 100 characters with a stronger hook" or "Add more urgency"'
          />
          <button style={S.submitBtn(loading)} onClick={() => handleRefine()} disabled={loading}>
            {loading ? "Refining…" : "Apply Feedback"}
          </button>
        </div>
      )}

      {currentHistory.length > 0 && (
        <>
          <span style={S.historyToggle} onClick={() => setShowHistory(!showHistory)}>
            {showHistory ? "▲ Hide" : "▼ Show"} revision history ({currentHistory.length})
          </span>
          {showHistory && (
            <div style={S.historyBox}>
              {currentHistory.map((h, i) => (
                <div key={i} style={S.historyItem}>
                  <div style={S.historyLabel}>v{h.revision || 1} {h.feedback_applied ? `— "${h.feedback_applied}"` : "(original)"}</div>
                  <div style={S.historyText}>{h.caption?.slice(0, 120)}…</div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

function PlanCard({ plan }) {
  const fields = [
    ["Post Format", plan.post_format],
    ["Tone", plan.tone],
    ["CTA", plan.cta],
    ["Platform Tips", plan.platform_tips],
    ["Hashtag Theme", plan.hashtag_theme],
    ["Key Messages", (plan.key_messages || []).join(" • ")],
  ];
  return (
    <div style={S.card}>
      <div style={S.heading}>CONTENT PLAN</div>
      <div style={S.planGrid}>
        {fields.map(([label, value]) => (
          <div key={label} style={S.planItem}>
            <div style={S.planLabel}>{label}</div>
            <div style={S.planValue}>{value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function ContentPreview({ result, sessionId, onResultUpdated }) {
  if (!result) return null;
  const { content_plan, captions } = result;

  const handleCaptionsUpdated = (newCaptions, newValidation) => {
    onResultUpdated({ ...result, captions: newCaptions, validation: newValidation });
  };

  return (
    <div style={S.wrap}>
      {content_plan && <PlanCard plan={content_plan} />}
      {captions && captions.length > 0 && (
        <CaptionsCard
          captions={captions}
          sessionId={sessionId}
          onCaptionsUpdated={handleCaptionsUpdated}
        />
      )}
    </div>
  );
}
