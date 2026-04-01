const S = {
  card: {
    background: "#16162a", borderRadius: 20, padding: 20,
    border: "1px solid #2a2a4a",
    boxShadow: "0 16px 32px rgba(56, 39, 76, 0.15)",
  },
  heading: { fontSize: 11, fontWeight: 700, color: "#8888cc", letterSpacing: 2, marginBottom: 14 },
  statusBanner: (ready) => ({
    display: "flex", alignItems: "center", gap: 10,
    padding: "14px 18px", borderRadius: 14, marginBottom: 16,
    background: ready ? "#0f2a1a" : "#2a0f0f",
    border: `1px solid ${ready ? "#1a5a2a" : "#5a1a1a"}`,
    boxShadow: ready
      ? "0 4px 16px rgba(44, 204, 44, 0.08)"
      : "0 4px 16px rgba(204, 44, 44, 0.08)",
  }),
  statusDot: (ready) => ({
    width: 10, height: 10, borderRadius: "50%",
    background: ready ? "#44cc44" : "#cc4444", flexShrink: 0,
    boxShadow: ready ? "0 0 6px #44cc44" : "0 0 6px #cc4444",
  }),
  statusText: (ready) => ({
    fontSize: 14, fontWeight: 700,
    color: ready ? "#66ee66" : "#ee6666",
  }),
  section: { marginBottom: 14 },
  sectionLabel: { fontSize: 11, color: "#6666aa", letterSpacing: 1, marginBottom: 8, textTransform: "uppercase" },
  row: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 },
  capLabel: { fontSize: 13, color: "#aaaacc" },
  pill: (pass) => ({
    padding: "3px 12px", borderRadius: 50, fontSize: 11, fontWeight: 700,
    background: pass ? "#0f2a1a" : "#2a0f0f",
    color: pass ? "#66cc66" : "#cc6666",
    letterSpacing: "0.5px",
  }),
  messageList: { display: "flex", flexDirection: "column", gap: 6 },
  error: {
    padding: "8px 14px", borderRadius: 10,
    background: "#2a0a0a", border: "1px solid #5a1a1a",
    fontSize: 12, color: "#ff8888",
  },
  warning: {
    padding: "8px 14px", borderRadius: 10,
    background: "#2a2a0a", border: "1px solid #5a5a1a",
    fontSize: 12, color: "#dddd66",
  },
  packageBox: {
    background: "#1a1a30", borderRadius: 14, padding: 16,
    border: "1px solid #3a3a6a",
    boxShadow: "0 8px 20px rgba(56, 39, 76, 0.10)",
  },
  packageLabel: { fontSize: 11, color: "#6666aa", marginBottom: 6, textTransform: "uppercase", letterSpacing: 1 },
  packageText: { fontSize: 13, color: "#d0d0f0", lineHeight: 1.6, whiteSpace: "pre-wrap" },
  imgThumb: { width: "100%", borderRadius: 10, marginTop: 12, maxHeight: 200, objectFit: "cover" },
  copyBtn: {
    marginTop: 10, padding: "6px 16px", borderRadius: 50,
    border: "1px solid #3a3a6a", background: "transparent",
    color: "#8888cc", cursor: "pointer", fontSize: 12, fontWeight: 600,
  },
};

export default function ValidationCard({ validation }) {
  if (!validation) return null;

  const { ready_to_post, platform, caption_validations, image_validation,
          best_caption, package: pkg, all_errors, all_warnings } = validation;

  const imgSrc = pkg.image_b64
    ? `data:${pkg.media_type};base64,${pkg.image_b64}`
    : pkg.image_url;

  const copy = () => navigator.clipboard.writeText(pkg.caption);

  return (
    <div style={S.card}>
      <div style={S.heading}>VALIDATION &amp; READY-TO-POST PACKAGE</div>

      {/* Status banner */}
      <div style={S.statusBanner(ready_to_post)}>
        <div style={S.statusDot(ready_to_post)} />
        <div style={S.statusText(ready_to_post)}>
          {ready_to_post
            ? `✓ Ready to post on ${platform}`
            : `✗ Needs fixes before posting on ${platform}`}
        </div>
      </div>

      {/* Caption validation per variation */}
      <div style={S.section}>
        <div style={S.sectionLabel}>Caption Check</div>
        {caption_validations.map((v, i) => (
          <div key={i} style={S.row}>
            <span style={S.capLabel}>{v.label} — {v.char_count} chars, {v.hashtag_count} hashtags</span>
            <span style={S.pill(v.passed)}>{v.passed ? "Pass" : "Fail"}</span>
          </div>
        ))}
      </div>

      {/* Image validation */}
      <div style={S.section}>
        <div style={S.sectionLabel}>Image Check</div>
        <div style={S.row}>
          <span style={S.capLabel}>
            {image_validation.width && image_validation.height
              ? `${image_validation.width}×${image_validation.height}px`
              : "Dimensions unverified"}
          </span>
          <span style={S.pill(image_validation.passed)}>
            {image_validation.passed ? "Pass" : "Fail"}
          </span>
        </div>
      </div>

      {/* Errors */}
      {all_errors.length > 0 && (
        <div style={{ ...S.section, ...S.messageList }}>
          <div style={S.sectionLabel}>Errors</div>
          {all_errors.map((e, i) => <div key={i} style={S.error}>✗ {e}</div>)}
        </div>
      )}

      {/* Warnings */}
      {all_warnings.length > 0 && (
        <div style={{ ...S.section, ...S.messageList }}>
          <div style={S.sectionLabel}>Warnings</div>
          {all_warnings.map((w, i) => <div key={i} style={S.warning}>⚠ {w}</div>)}
        </div>
      )}

      {/* Ready-to-post package */}
      <div style={S.packageBox}>
        <div style={S.packageLabel}>Ready-to-Post Package — {best_caption?.label}</div>
        <div style={S.packageText}>{pkg.caption}</div>
        <button style={S.copyBtn} onClick={copy}>Copy Caption</button>
        {imgSrc && <img src={imgSrc} alt="Post visual" style={S.imgThumb} />}
        {!imgSrc && pkg.image_url && (
          <div style={{ marginTop: 10, fontSize: 12, color: "#8888cc" }}>
            Image URL: <a href={pkg.image_url} target="_blank" rel="noreferrer" style={{ color: "#aaaaff" }}>Open DALL-E image</a>
          </div>
        )}
      </div>
    </div>
  );
}
