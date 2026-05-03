/**
 * MedExplain AI — Frontend Application
 * Handles: wakeup screen, file upload, API calls, results rendering
 */

// ── Config ────────────────────────────────────────────────────────────────────
const API_BASE = window.location.origin; // Same origin — Flask serves frontend

// ── DOM refs ──────────────────────────────────────────────────────────────────
const wakeupOverlay  = document.getElementById("wakeup-overlay");
const wuBar          = document.getElementById("wu-bar");
const wuStatus       = document.getElementById("wu-status");

const dropZone       = document.getElementById("drop-zone");
const fileInput      = document.getElementById("file-input");
const fileNameEl     = document.getElementById("file-name");
const languageSelect = document.getElementById("language-select");
const analyzeBtn     = document.getElementById("analyze-btn");
const btnText        = document.querySelector(".btn-text");
const btnSpinner     = document.getElementById("btn-spinner");

const uploadCard     = document.getElementById("upload-card");
const errorBox       = document.getElementById("error-box");
const errorMsg       = document.getElementById("error-msg");

const resultsSection = document.getElementById("results-section");
const uploadSection  = document.getElementById("upload-section");
const resetBtn       = document.getElementById("reset-btn");

// ── State ─────────────────────────────────────────────────────────────────────
let selectedFile = null;


// ══════════════════════════════════════════════════════════════════════════════
// WAKEUP SCREEN
// ══════════════════════════════════════════════════════════════════════════════

async function wakeBackend() {
  let progress = 0;

  const ticker = setInterval(() => {
    progress = Math.min(progress + 1, 90);
    wuBar.style.width = progress + "%";
  }, 600);

  const tryPing = async (attempt) => {
    try {
      wuStatus.textContent = attempt > 1
        ? `Still waking up... (attempt ${attempt})`
        : "Connecting to server...";

      const res = await fetch(`${API_BASE}/health`, {
        signal: AbortSignal.timeout(15000),
      });

      if (res.ok) {
        clearInterval(ticker);
        wuBar.style.width = "100%";
        wuStatus.textContent = "✅ Ready!";
        wuStatus.style.color = "#22CC88";
        setTimeout(() => {
          wakeupOverlay.style.opacity = "0";
          wakeupOverlay.style.transition = "opacity 0.5s ease";
          setTimeout(() => wakeupOverlay.remove(), 500);
        }, 600);
        return true;
      }
    } catch (_) {}
    return false;
  };

  for (let i = 1; i <= 12; i++) {
    const ok = await tryPing(i);
    if (ok) return;
    await new Promise((r) => setTimeout(r, 5000));
  }

  clearInterval(ticker);
  wuBar.style.width = "100%";
  wuBar.style.background = "#C0392B";
  wuStatus.textContent = "⚠️ Server is taking long. Try refreshing the page.";
  wuStatus.style.color = "#FF7777";
  setTimeout(() => wakeupOverlay.remove(), 4000);
}

wakeBackend();


// ══════════════════════════════════════════════════════════════════════════════
// FILE HANDLING
// ══════════════════════════════════════════════════════════════════════════════

fileInput.addEventListener("change", (e) => {
  handleFileSelect(e.target.files[0]);
});

dropZone.addEventListener("click", (e) => {
  if (e.target === fileInput || e.target.classList.contains("btn-upload")) return;
  fileInput.click();
});

dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropZone.classList.add("drag-over");
});

dropZone.addEventListener("dragleave", () => {
  dropZone.classList.remove("drag-over");
});

dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropZone.classList.remove("drag-over");
  const file = e.dataTransfer.files[0];
  if (file) handleFileSelect(file);
});

function handleFileSelect(file) {
  if (!file) return;

  if (!file.name.toLowerCase().endsWith(".pdf")) {
    showError("Only PDF files are supported. Please upload a .pdf file.");
    return;
  }

  const sizeMB = file.size / (1024 * 1024);
  if (sizeMB > 10) {
    showError(`File is too large (${sizeMB.toFixed(1)} MB). Maximum size is 10 MB.`);
    return;
  }

  selectedFile = file;
  fileNameEl.textContent = `✓ ${file.name} (${sizeMB.toFixed(1)} MB)`;
  analyzeBtn.disabled = false;
  hideError();
}


// ══════════════════════════════════════════════════════════════════════════════
// ANALYZE
// ══════════════════════════════════════════════════════════════════════════════

analyzeBtn.addEventListener("click", analyze);

async function analyze() {
  if (!selectedFile) return;

  setLoading(true);
  hideError();

  const formData = new FormData();
  formData.append("file", selectedFile);
  formData.append("language", languageSelect.value);

  try {
    const res = await fetch(`${API_BASE}/api/analyze`, {
      method: "POST",
      body: formData,
    });

    const data = await res.json();

    if (!res.ok || !data.success) {
      showError(data.error || "Analysis failed. Please try again.");
      setLoading(false);
      return;
    }

    renderResults(data);
  } catch (err) {
    showError("Network error. Please check your connection and try again.");
  } finally {
    setLoading(false);
  }
}


// ══════════════════════════════════════════════════════════════════════════════
// RENDER RESULTS
// ══════════════════════════════════════════════════════════════════════════════

function renderResults(data) {
  const { analysis, meta } = data;

  // Scroll to results
  uploadSection.style.display = "none";
  resultsSection.hidden = false;
  window.scrollTo({ top: 0, behavior: "smooth" });

  // Title
  document.getElementById("results-title").textContent =
    analysis.report_type || "Analysis Complete";

  // Meta
  document.getElementById("results-meta").innerHTML =
    `📄 ${meta.filename}<br/>` +
    `${meta.pages} page${meta.pages !== 1 ? "s" : ""} · ${meta.word_count} words · ${meta.language}`;

  // Status Banner
  renderStatusBanner(analysis.overall_status);

  // Summary
  document.getElementById("summary-text").textContent = analysis.summary || "";

  // Findings
  renderFindings(analysis.findings || []);

  // Abnormal flags
  renderAbnormal(analysis.abnormal_flags || []);

  // Doctor questions
  renderQuestions(analysis.doctor_questions || []);

  // Lifestyle tips
  renderTips(analysis.lifestyle_tips || []);

  // Disclaimer
  document.getElementById("disclaimer-box").textContent =
    analysis.disclaimer || "This is for educational purposes only. Consult a qualified healthcare professional.";
}

function renderStatusBanner(status) {
  const banner = document.getElementById("status-banner");
  const map = {
    normal:           { cls: "normal",    icon: "✅", text: "All values appear within normal ranges." },
    attention_needed: { cls: "attention", icon: "⚠️", text: "Some values need attention — see details below." },
    urgent:           { cls: "urgent",    icon: "🚨", text: "One or more values are critically abnormal — please contact your doctor soon." },
  };
  const cfg = map[status] || map["attention_needed"];
  banner.className = `status-banner ${cfg.cls}`;
  banner.innerHTML = `<span>${cfg.icon}</span><span>${cfg.text}</span>`;
}

function renderFindings(findings) {
  const container = document.getElementById("findings-table");
  container.innerHTML = "";

  if (!findings.length) {
    container.innerHTML = '<p style="color:var(--text-soft); font-size:0.9rem;">No individual findings extracted.</p>';
    return;
  }

  findings.forEach((f, i) => {
    const statusLabel = { normal: "Normal", low: "Low", high: "High", critical: "Critical" };
    const row = document.createElement("div");
    row.className = "finding-row";
    row.innerHTML = `
      <div>
        <div class="finding-name">${escHtml(f.name)}</div>
      </div>
      <div class="finding-value val-${f.status}">${escHtml(f.value)}</div>
      <div class="finding-ref">Ref: ${escHtml(f.reference_range || "—")}</div>
      <div class="finding-badge status-${f.status}">${statusLabel[f.status] || f.status}</div>
      <div class="finding-detail">
        <strong>What it measures:</strong> ${escHtml(f.explanation || "")}<br/><br/>
        <strong>What your result means:</strong> ${escHtml(f.what_it_means || "")}
      </div>
    `;
    row.addEventListener("click", () => row.classList.toggle("expanded"));
    container.appendChild(row);
  });

  // Add hint
  const hint = document.createElement("p");
  hint.style.cssText = "font-size:0.8rem; color:var(--text-soft); margin-top:8px;";
  hint.textContent = "💡 Click any row for a detailed explanation.";
  container.appendChild(hint);
}

function renderAbnormal(flags) {
  const grid = document.getElementById("abnormal-grid");
  grid.innerHTML = "";

  if (!flags.length) {
    grid.innerHTML = '<div class="no-abnormal">🎉 No values outside the normal range found!</div>';
    return;
  }

  flags.forEach((f) => {
    const card = document.createElement("div");
    card.className = `abnormal-card ${f.status}`;
    card.innerHTML = `
      <div class="abnormal-card-name">${escHtml(f.name)}</div>
      <div class="abnormal-card-val">${escHtml(f.value)} ${f.status === "high" ? "↑" : f.status === "low" ? "↓" : "⚠"}</div>
      <div class="abnormal-card-exp">${escHtml(f.simple_explanation)}</div>
    `;
    grid.appendChild(card);
  });
}

function renderQuestions(questions) {
  const list = document.getElementById("questions-list");
  list.innerHTML = "";
  questions.forEach((q, i) => {
    const li = document.createElement("li");
    li.innerHTML = `<span class="q-num">${i + 1}</span><span>${escHtml(q)}</span>`;
    list.appendChild(li);
  });
}

function renderTips(tips) {
  const grid = document.getElementById("tips-grid");
  grid.innerHTML = "";
  tips.forEach((t) => {
    const card = document.createElement("div");
    card.className = "tip-card";
    card.innerHTML = `
      <div class="tip-card-tip">${escHtml(t.tip)}</div>
      <div class="tip-card-reason">${escHtml(t.reason)}</div>
    `;
    grid.appendChild(card);
  });
}


// ══════════════════════════════════════════════════════════════════════════════
// RESET
// ══════════════════════════════════════════════════════════════════════════════

resetBtn.addEventListener("click", () => {
  selectedFile = null;
  fileInput.value = "";
  fileNameEl.textContent = "";
  analyzeBtn.disabled = true;
  hideError();
  resultsSection.hidden = true;
  uploadSection.style.display = "";
  window.scrollTo({ top: uploadSection.offsetTop - 80, behavior: "smooth" });
});


// ══════════════════════════════════════════════════════════════════════════════
// UTILITIES
// ══════════════════════════════════════════════════════════════════════════════

function setLoading(loading) {
  analyzeBtn.disabled = loading;
  btnText.hidden = loading;
  btnSpinner.hidden = !loading;
}

function showError(msg) {
  errorMsg.textContent = msg;
  errorBox.hidden = false;
  errorBox.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function hideError() {
  errorBox.hidden = true;
  errorMsg.textContent = "";
}

function escHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
