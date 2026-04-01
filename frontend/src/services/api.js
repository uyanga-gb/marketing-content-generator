const BASE = "http://54.147.163.175:8000";

export async function startSession() {
  const res = await fetch(`${BASE}/session/start`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to start session");
  return res.json();
}

export async function sendChat(sessionId, message) {
  const res = await fetch(`${BASE}/session/${sessionId}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  if (!res.ok) throw new Error("Chat request failed");
  return res.json();
}

export async function generateContent(sessionId, imageFile = null) {
  const formData = new FormData();
  if (imageFile) formData.append("image", imageFile);

  const res = await fetch(`${BASE}/session/${sessionId}/generate`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Generation failed");
  }
  return res.json();
}
