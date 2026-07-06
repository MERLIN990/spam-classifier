// Frontend simple que consume la API del backend (integración vía fetch).
// Si se sirve desde el mismo contenedor FastAPI, las rutas relativas
// "/api/..." apuntan automáticamente al backend correcto.
const API_BASE = "/api";

const textInput = document.getElementById("text-input");
const analyzeBtn = document.getElementById("analyze-btn");
const resultSection = document.getElementById("result");
const labelBadge = document.getElementById("label-badge");
const spamBar = document.getElementById("spam-bar");
const hamBar = document.getElementById("ham-bar");
const spamValue = document.getElementById("spam-value");
const hamValue = document.getElementById("ham-value");
const errorMsg = document.getElementById("error-msg");
const healthEl = document.getElementById("health");

function setLoading(loading) {
  analyzeBtn.disabled = loading;
  analyzeBtn.textContent = loading ? "Analizando..." : "Analizar";
}

function showError(message) {
  errorMsg.textContent = message;
  errorMsg.classList.remove("hidden");
  resultSection.classList.add("hidden");
}

function showResult(data) {
  errorMsg.classList.add("hidden");
  resultSection.classList.remove("hidden");

  labelBadge.textContent = data.label === "spam" ? "SPAM" : "NO SPAM (HAM)";
  labelBadge.className = "label-badge " + (data.label === "spam" ? "spam" : "ham");

  const spamPct = Math.round(data.spam_probability * 100);
  const hamPct = Math.round(data.ham_probability * 100);
  spamBar.style.width = spamPct + "%";
  hamBar.style.width = hamPct + "%";
  spamValue.textContent = spamPct + "%";
  hamValue.textContent = hamPct + "%";
}

async function analyze() {
  const text = textInput.value;
  setLoading(true);
  try {
    const res = await fetch(`${API_BASE}/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });

    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail ? JSON.stringify(body.detail) : `Error HTTP ${res.status}`);
    }

    const data = await res.json();
    showResult(data);
  } catch (err) {
    showError("No se pudo clasificar el texto: " + err.message);
  } finally {
    setLoading(false);
  }
}

async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    const data = await res.json();
    healthEl.textContent = data.model_loaded
      ? `API conectada · modelo v${data.model_version}`
      : "API conectada · modelo NO cargado";
  } catch {
    healthEl.textContent = "No se pudo conectar con la API";
  }
}

analyzeBtn.addEventListener("click", analyze);
textInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) analyze();
});

checkHealth();
