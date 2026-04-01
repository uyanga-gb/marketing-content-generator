import { useState } from "react";

const S = {
  card: {
    background: "#16162a", borderRadius: 20, padding: 20,
    border: "1px solid #2a2a4a",
    boxShadow: "0 16px 32px rgba(56, 39, 76, 0.15)",
  },
  heading: { fontSize: 11, fontWeight: 700, color: "#8888cc", letterSpacing: 2, marginBottom: 14 },
  imgWrap: {
    position: "relative", borderRadius: 12, overflow: "hidden", marginBottom: 4,
  },
  img: {
    width: "100%", display: "block", objectFit: "cover", maxHeight: 400,
    background: "#1e1e3a", transition: "transform 0.4s ease",
  },
  badge: (mode) => ({
    display: "inline-flex", alignItems: "center", gap: 6,
    padding: "4px 12px", borderRadius: 50,
    background: mode === "analyse" ? "#1a3a2a" : "#2a2050",
    color: mode === "analyse" ? "#66cc99" : "#9988ff",
    fontSize: 11, fontWeight: 700, marginBottom: 12, letterSpacing: 1,
    textTransform: "uppercase",
  }),
  badgeDot: (mode) => ({
    width: 6, height: 6, borderRadius: "50%",
    background: mode === "analyse" ? "#44cc88" : "#7777ff",
  }),
  section: { marginTop: 14 },
  label: { fontSize: 11, color: "#6666aa", marginBottom: 4, textTransform: "uppercase", letterSpacing: 1 },
  value: { fontSize: 13, color: "#d0d0f0", lineHeight: 1.5 },
  list: { paddingLeft: 18, fontSize: 13, color: "#d0d0f0", lineHeight: 1.8 },
  note: {
    marginTop: 12, padding: "8px 12px", borderRadius: 8,
    background: "#2a2a1a", border: "1px solid #4a4a2a",
    fontSize: 12, color: "#aaaa66",
  },
  refineToggle: {
    marginTop: 12, padding: "6px 18px", borderRadius: 50,
    border: "1px solid #5a3a9a", background: "transparent",
    color: "#aa88ee", cursor: "pointer", fontSize: 12, fontWeight: 600,
  },
  feedbackArea: {
    marginTop: 12, padding: 12, background: "#1a1a30",
    borderRadius: 12, border: "1px solid #3a2a5a",
  },
  feedbackInput: {
    width: "100%", padding: "8px 12px", borderRadius: 8,
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
  chip: {
    padding: "4px 12px", borderRadius: 50,
    background: "#2a2050", border: "none",
    color: "#aa88ff", cursor: "pointer", fontSize: 11, fontWeight: 600,
  },
  palette: { display: "flex", gap: 8, marginTop: 6 },
  swatch: (color) => ({
    width: 32, height: 32, borderRadius: 8, background: color,
    border: "1px solid #3a3a6a",
  }),
};

const IMAGE_QUICK_PROMPTS = [
  "More dramatic lighting",
  "Outdoor setting",
  "Minimalist background",
  "Warmer color palette",
  "Add people / lifestyle",
];

export default function ImagePreview({ imageData, sessionId, onImageUpdated }) {
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [loading, setLoading] = useState(false);

  if (!imageData) return null;

  const { mode, image_b64, media_type, analysis, prompt_used, note, url } = imageData;

  const handleRefine = async (text) => {
    const f = text || feedback;
    if (!f.trim() || loading) return;
    setLoading(true);
    try {
      const res = await fetch(`/session/${sessionId}/refine/image`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ feedback: f }),
      });
      const data = await res.json();
      onImageUpdated(data.image, data.validation);
      setFeedback("");
      setShowFeedback(false);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const imgSrc = image_b64
    ? `data:${media_type || "image/jpeg"};base64,${image_b64}`
    : url;

  return (
    <div style={S.card}>
      <div style={S.heading}>IMAGE</div>
      <div style={S.badge(mode)}>
        <span style={S.badgeDot(mode)} />
        {mode === "analyse" ? "UPLOADED" : "GENERATED"}
      </div>

      {imgSrc && (
        <div style={S.imgWrap}>
          <img src={imgSrc} alt="Marketing visual" style={S.img} />
        </div>
      )}

      {mode === "analyse" && analysis && (
        <>
          <div style={S.section}>
            <div style={S.label}>Image Assessment</div>
            <div style={S.value}>{analysis.image_assessment}</div>
          </div>

          <div style={S.section}>
            <div style={S.label}>Overlay Suggestions</div>
            <ul style={S.list}>
              {(analysis.overlay_suggestions || []).map((s, i) => <li key={i}>{s}</li>)}
            </ul>
          </div>

          <div style={S.section}>
            <div style={S.label}>Crop Recommendation</div>
            <div style={S.value}>{analysis.crop_recommendation}</div>
          </div>

          {analysis.color_palette && analysis.color_palette.length > 0 && (
            <div style={S.section}>
              <div style={S.label}>Color Palette</div>
              <div style={S.palette}>
                {analysis.color_palette.map((c, i) => (
                  <div key={i} style={S.swatch(c)} title={c} />
                ))}
              </div>
            </div>
          )}

          <div style={S.section}>
            <div style={S.label}>Alt Text</div>
            <div style={S.value}>{analysis.alt_text}</div>
          </div>
        </>
      )}

      {mode === "generate" && (
        <>
          <div style={S.section}>
            <div style={S.label}>Generation Prompt</div>
            <div style={S.value}>{prompt_used}</div>
          </div>
          {note && <div style={S.note}>{note}</div>}

          {/* Refine button — only for generated images */}
          <button style={S.refineToggle} onClick={() => setShowFeedback(!showFeedback)}>
            {showFeedback ? "Cancel" : "✦ Regenerate with changes"}
          </button>

          {showFeedback && (
            <div style={S.feedbackArea}>
              <div style={{ fontSize: 11, color: "#8888aa", marginBottom: 8 }}>
                What would you like to change about the image?
              </div>

              {/* Quick prompt chips */}
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 10 }}>
                {IMAGE_QUICK_PROMPTS.map((p) => (
                  <button
                    key={p}
                    onClick={() => handleRefine(p)}
                    disabled={loading}
                    style={{ ...S.chip, cursor: loading ? "default" : "pointer", opacity: loading ? 0.5 : 1 }}
                  >
                    {p}
                  </button>
                ))}
              </div>

              <textarea
                style={S.feedbackInput}
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                placeholder='e.g. "Put the product on a marble countertop with soft morning light"'
              />
              <button
                style={S.submitBtn(loading)}
                onClick={() => handleRefine()}
                disabled={loading}
              >
                {loading ? "Regenerating…" : "Regenerate Image"}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
