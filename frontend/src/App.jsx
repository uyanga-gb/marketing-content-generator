import { useState, useEffect, useRef } from "react";
import ChatInterface from "./components/ChatInterface";
import ContentPreview from "./components/ContentPreview";
import ImagePreview from "./components/ImagePreview";
import ValidationCard from "./components/ValidationCard";
import { startSession, generateContent } from "./services/api.js";

const S = {
  app: { minHeight: "100vh", background: "#0f0f1a", color: "#e0e0e0" },
  header: {
    padding: "18px 32px", background: "rgba(22, 22, 42, 0.85)",
    backdropFilter: "blur(16px)", WebkitBackdropFilter: "blur(16px)",
    borderBottom: "1px solid #2a2a4a", position: "sticky", top: 0, zIndex: 40,
    display: "flex", alignItems: "center", gap: 12,
  },
  logo: {
    fontSize: 20, fontWeight: 800,
    background: "linear-gradient(135deg, #7a78ff 0%, #b03ae0 100%)",
    WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
    backgroundClip: "text",
  },
  subtitle: { fontSize: 13, color: "#6666aa" },
  body: {
    maxWidth: 1200, margin: "0 auto", padding: 24,
    display: "grid", gridTemplateColumns: "420px 1fr", gap: 24, alignItems: "start",
  },
  leftCol: { display: "flex", flexDirection: "column", gap: 16 },
  chatWrap: { height: 560 },
  generateCard: {
    background: "#16162a", borderRadius: 20, padding: 20,
    border: "1px solid #2a2a4a",
    boxShadow: "0 16px 32px rgba(56, 39, 76, 0.15)",
  },
  heading: { fontSize: 11, fontWeight: 700, color: "#8888cc", letterSpacing: 2, marginBottom: 14 },
  fileInput: { display: "none" },
  uploadBtn: {
    width: "100%", padding: "10px 0", borderRadius: 50,
    border: "1px dashed #3a3a6a", background: "transparent",
    color: "#8888cc", cursor: "pointer", fontSize: 13, marginBottom: 12,
    transition: "border-color 0.2s, color 0.2s",
  },
  genBtn: (disabled) => ({
    width: "100%", padding: "12px 0", borderRadius: 50, border: "none",
    background: disabled ? "#1e1e3a" : "linear-gradient(135deg, #5a5ae0, #8a3ae0)",
    color: disabled ? "#555" : "#fff",
    cursor: disabled ? "default" : "pointer",
    fontSize: 14, fontWeight: 700, letterSpacing: 1,
    boxShadow: disabled ? "none" : "0 8px 20px rgba(90, 90, 224, 0.3)",
    transition: "transform 0.2s, box-shadow 0.2s",
  }),
  statusBadge: (phase) => ({
    display: "inline-flex", alignItems: "center", gap: 6,
    padding: "4px 12px", borderRadius: 50, fontSize: 11,
    fontWeight: 600, letterSpacing: 1, marginTop: 10,
    background: phase === "complete" ? "#1a3a1a" : phase === "pipeline_ready" ? "#1a2a3a" : "#1e1e2a",
    color: phase === "complete" ? "#66cc66" : phase === "pipeline_ready" ? "#6699ff" : "#666688",
  }),
  statusDot: (phase) => ({
    width: 7, height: 7, borderRadius: "50%", flexShrink: 0,
    background: phase === "complete" ? "#44cc44" : phase === "pipeline_ready" ? "#4499ff" : "#555577",
  }),
  rightCol: { display: "flex", flexDirection: "column", gap: 20 },
  spinnerBar: {
    display: "flex", alignItems: "center", gap: 12,
    padding: "16px 20px", borderRadius: 16,
    background: "#16162a", border: "1px solid #2a2a4a",
    boxShadow: "0 8px 24px rgba(56, 39, 76, 0.12)",
  },
  spinnerAccent: {
    width: 4, height: 48, borderRadius: 4,
    background: "linear-gradient(180deg, #5a5ae0, #8a3ae0)", flexShrink: 0,
  },
  spinnerLabel: { fontSize: 11, fontWeight: 700, color: "#6666aa", letterSpacing: 1, textTransform: "uppercase", marginBottom: 4 },
  spinnerText: { fontSize: 15, fontWeight: 700, color: "#d0d0f0" },
  spinnerHighlight: { color: "#8888ff" },
};

const PHASE_LABELS = {
  chat: "Collecting info…",
  pipeline_ready: "Ready to generate",
  complete: "Complete",
};

export default function App() {
  const [sessionId, setSessionId] = useState(null);
  const [phase, setPhase] = useState("chat");
  const [result, setResult] = useState(null);
  const [imageFile, setImageFile] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState(null);
  const fileRef = useRef(null);

  useEffect(() => {
    startSession().then((d) => setSessionId(d.session_id)).catch(console.error);
  }, []);

  const handleCollected = () => {
    setPhase("pipeline_ready");
  };

  const handleGenerate = async () => {
    if (!sessionId || generating) return;
    setGenerating(true);
    setError(null);
    try {
      const data = await generateContent(sessionId, imageFile);
      setResult(data);
      setPhase("complete");
    } catch (e) {
      setError(e.message);
    } finally {
      setGenerating(false);
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) setImageFile(file);
  };

  return (
    <div style={S.app}>
      <div style={S.header}>
        <div>
          <div style={S.logo}>✦ Marketing Content Generator</div>
          <div style={S.subtitle}>Multi-agent AI system · Chat → Plan → Caption → Image</div>
        </div>
      </div>

      <div style={S.body}>
        {/* Left column: chat + generate controls */}
        <div style={S.leftCol}>
          <div style={S.chatWrap}>
            {sessionId ? (
              <ChatInterface sessionId={sessionId} onCollected={handleCollected} />
            ) : (
              <div style={{ color: "#555", padding: 20 }}>Starting session…</div>
            )}
          </div>

          <div style={S.generateCard}>
            <div style={S.heading}>GENERATE CONTENT</div>

            <input
              type="file"
              accept="image/*"
              ref={fileRef}
              style={S.fileInput}
              onChange={handleFileChange}
            />
            <button style={S.uploadBtn} onClick={() => fileRef.current?.click()}>
              {imageFile ? `📎 ${imageFile.name}` : "+ Upload image (optional)"}
            </button>

            <button
              style={S.genBtn(phase !== "pipeline_ready" || generating)}
              onClick={handleGenerate}
              disabled={phase !== "pipeline_ready" || generating}
            >
              {generating ? "Generating…" : "Generate Content"}
            </button>

            {error && <div style={{ marginTop: 10, color: "#cc4444", fontSize: 12 }}>{error}</div>}

            <div style={S.statusBadge(phase)}>
              <span style={S.statusDot(phase)} />
              {PHASE_LABELS[phase] || phase}
            </div>
          </div>
        </div>

        {/* Right column: results */}
        <div style={S.rightCol}>
          {generating && (
            <div style={S.spinnerBar}>
              <div style={S.spinnerAccent} />
              <div>
                <div style={S.spinnerLabel}>Pipeline Running</div>
                <div style={S.spinnerText}>
                  Planner → Caption Generator → Image Agent…{" "}
                  <span style={S.spinnerHighlight}>In Progress</span>
                </div>
              </div>
            </div>
          )}
          {result && !generating && (
            <>
              <ContentPreview
                result={result}
                sessionId={sessionId}
                onResultUpdated={setResult}
              />
              <ImagePreview
                imageData={result.image}
                sessionId={sessionId}
                onImageUpdated={(newImage, newValidation) =>
                  setResult((r) => ({ ...r, image: newImage, validation: newValidation }))
                }
              />
              <ValidationCard validation={result.validation} />
            </>
          )}
          {!result && !generating && (
            <div style={{ color: "#333", padding: 60, textAlign: "center", fontSize: 14 }}>
              Complete the chat on the left, then click Generate Content.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
