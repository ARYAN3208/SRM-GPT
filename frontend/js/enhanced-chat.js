
let sessionId = null;
let isSending = false;
let chatHistory = [];
let analyticsData = { questions: [] };

const modelSelect = document.getElementById("modelSelect");
const modelBadge = document.getElementById("modelBadge");

if (modelSelect) {
  modelSelect.addEventListener("change", (e) => {
    modelBadge.textContent = modelSelect.options[modelSelect.selectedIndex].text;
    document.getElementById("currentModel").textContent = 
      modelSelect.options[modelSelect.selectedIndex].text.split(" ")[0] + "...";
  });
}

const detailedToggle = document.getElementById("detailedToggle");
const sourcesToggle = document.getElementById("sourcesToggle");
const docsToggle = document.getElementById("docsToggle");
const debugToggle = document.getElementById("debugToggle");
const compareModeToggle = document.getElementById("compareModeToggle");
const compareModels = document.getElementById("compareModels");

if (compareModeToggle) {
  compareModeToggle.addEventListener("change", (e) => {
    compareModels.style.display = e.target.checked ? "block" : "none";
  });
}

document.getElementById("exportJsonBtn")?.addEventListener("click", () => {
  const data = JSON.stringify(chatHistory, null, 2);
  downloadFile(data, "chat_history.json", "application/json");
});

document.getElementById("exportCsvBtn")?.addEventListener("click", () => {
  const csv = convertToCsv(chatHistory);
  downloadFile(csv, "chat_history.csv", "text/csv");
});

document.getElementById("exportAnalyticsBtn")?.addEventListener("click", () => {
  const data = JSON.stringify(analyticsData, null, 2);
  downloadFile(data, "analytics.json", "application/json");
});

function downloadFile(data, filename, mimeType) {
  const blob = new Blob([data], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function convertToCsv(data) {
  if (data.length === 0) return "";
  const headers = Object.keys(data[0]);
  const csv = [headers.join(",")];
  for (const row of data) {
    csv.push(headers.map(h => JSON.stringify(row[h] || "")).join(","));
  }
  return csv.join("\n");
}

document.getElementById("clearChatBtn")?.addEventListener("click", () => {
  sessionId = null;
  chatHistory = [];
  const chatInner = document.getElementById("chatInner");
  const emptyState = document.getElementById("emptyState");
  chatInner.innerHTML = "";
  chatInner.appendChild(emptyState);
  emptyState.style.display = "grid";
});

function updateMetrics() {
  const totalQueries = analyticsData.questions.length;
  document.getElementById("totalQueries").textContent = totalQueries;
  
  if (totalQueries > 0) {
    const avgResponse = (
      analyticsData.questions.reduce((sum, q) => sum + (q.response_time || 0), 0) / totalQueries
    ).toFixed(2);
    document.getElementById("avgResponse").textContent = avgResponse + "s";
  }
}

function loadAnalytics() {
  const saved = localStorage.getItem("campusgpt_analytics");
  if (saved) {
    try {
      analyticsData = JSON.parse(saved);
      updateMetrics();
    } catch (e) {
      console.error("Failed to load analytics:", e);
    }
  }
}

function saveAnalytics() {
  localStorage.setItem("campusgpt_analytics", JSON.stringify(analyticsData));
  updateMetrics();
}

const chatScroll = document.getElementById("chatScroll");
const chatInner = document.getElementById("chatInner");
const emptyState = document.getElementById("emptyState");
const chatForm = document.getElementById("chatForm");
const chatInput = document.getElementById("chatInput");
const sendBtn = document.getElementById("sendBtn");
const sidebar = document.getElementById("sidebar");
const sidebarCollapseBtn = document.getElementById("sidebarCollapseBtn");
const mobileMenuBtn = document.getElementById("mobileMenuBtn");
const connectionStatus = document.getElementById("connectionStatus");

const userMessageTemplate = document.getElementById("userMessageTemplate");
const assistantMessageTemplate = document.getElementById("assistantMessageTemplate");
const sourceChipTemplate = document.getElementById("sourceChipTemplate");
const typingTemplate = document.getElementById("typingTemplate");

function renderMarkdownLite(text) {
  const lines = text.split("\n");
  let html = "";
  let inList = false;
  let listType = null;

  function flushList() {
    if (inList) {
      html += listType === "ol" ? "</ol>" : "</ul>";
      inList = false;
      listType = null;
    }
  }

  function escapeHtml(s) {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function inlineFormat(s) {
    let out = escapeHtml(s);
    out = out.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    out = out.replace(/`(.+?)`/g, "<code>$1</code>");
    return out;
  }

  for (const rawLine of lines) {
    const line = rawLine.trimEnd();

    if (/^### /.test(line)) {
      flushList();
      html += `<h3>${inlineFormat(line.replace(/^### /, ""))}</h3>`;
    } else if (/^## /.test(line)) {
      flushList();
      html += `<h2>${inlineFormat(line.replace(/^## /, ""))}</h2>`;
    } else if (/^# /.test(line)) {
      flushList();
      html += `<h1>${inlineFormat(line.replace(/^# /, ""))}</h1>`;
    } else if (/^\s*[-*]\s+(.*)/.test(line)) {
      if (!inList || listType !== "ul") {
        flushList();
        html += "<ul>";
        inList = true;
        listType = "ul";
      }
      const match = /^\s*[-*]\s+(.*)/.exec(line);
      html += `<li>${inlineFormat(match[1])}</li>`;
    } else if (/^\s*\d+\.\s+(.*)/.test(line)) {
      if (!inList || listType !== "ol") {
        flushList();
        html += "<ol>";
        inList = true;
        listType = "ol";
      }
      const match = /^\s*\d+\.\s+(.*)/.exec(line);
      html += `<li>${inlineFormat(match[1])}</li>`;
    } else {
      flushList();
      if (line.trim()) {
        html += `<p>${inlineFormat(line)}</p>`;
      }
    }
  }

  flushList();
  return html;
}

function hideEmptyState() {
  if (emptyState) emptyState.style.display = "none";
}

function scrollToBottom() {
  chatScroll.scrollTop = chatScroll.scrollHeight;
}

function appendUserMessage(text) {
  hideEmptyState();
  const node = userMessageTemplate.content.cloneNode(true);
  node.querySelector(".message-bubble").textContent = text;
  chatInner.appendChild(node);
  chatHistory.push({ role: "user", content: text });
  scrollToBottom();
}

function appendTypingIndicator() {
  const node = typingTemplate.content.cloneNode(true);
  const el = node.querySelector(".message-typing");
  chatInner.appendChild(node);
  scrollToBottom();
  return el;
}

function removeTypingIndicator(el) {
  if (el && el.parentNode) el.parentNode.removeChild(el);
}

function confidenceColor(score) {
  if (score >= 80) return "var(--success)";
  if (score >= 60) return "var(--amber)";
  if (score >= 40) return "var(--warning)";
  return "var(--danger)";
}

function appendAssistantMessage(result) {
  hideEmptyState();
  const node = assistantMessageTemplate.content.cloneNode(true);
  const bubbleContent = node.querySelector(".bubble-content");
  bubbleContent.innerHTML = renderMarkdownLite(result.answer || "");

  const ringFill = node.querySelector(".ring-fill");
  const confidenceLabel = node.querySelector(".confidence-label");
  const sourcesCount = node.querySelector(".sources-count");
  const responseTime = node.querySelector(".response-time");
  const sourcesPanel = node.querySelector(".sources-panel");

  const score = Math.max(0, Math.min(100, result.confidence || 0));
  const circumference = 2 * Math.PI * 15.5;
  const offset = circumference - (score / 100) * circumference;

  confidenceLabel.textContent = `${result.confidence_label || "—"} · ${score.toFixed(0)}%`;
  ringFill.style.stroke = confidenceColor(score);

  const docs = result.docs_info || [];
  sourcesCount.textContent = `${docs.length} sources`;

  responseTime.textContent = result.response_time ? `${result.response_time}s` : "";

  chatInner.appendChild(node);
  scrollToBottom();

  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      ringFill.style.strokeDashoffset = offset;
    });
  });

  chatHistory.push({ role: "assistant", content: result.answer });
}

function appendErrorMessage(message) {
  hideEmptyState();
  const node = assistantMessageTemplate.content.cloneNode(true);
  node.querySelector(".bubble-content").innerHTML = `<p style="color: var(--danger);">${message}</p>`;
  node.querySelector(".message-meta").style.display = "none";
  chatInner.appendChild(node);
  scrollToBottom();
}

async function handleSend(text) {
  if (isSending) return;
  const trimmed = text.trim();
  if (!trimmed) return;

  isSending = true;
  sendBtn.disabled = true;

  appendUserMessage(trimmed);
  chatInput.value = "";

  const typingEl = appendTypingIndicator();
  const startTime = Date.now();

  try {
    const result = await Api.sendMessage(trimmed, sessionId, modelSelect.value);
    sessionId = result.session_id;
    removeTypingIndicator(typingEl);
    appendAssistantMessage(result);

    const responseTime = ((Date.now() - startTime) / 1000).toFixed(2);
    analyticsData.questions.push({
      question: trimmed,
      model: modelSelect.options[modelSelect.selectedIndex].text,
      confidence: result.confidence,
      response_time: parseFloat(responseTime),
      timestamp: new Date().toLocaleString()
    });
    saveAnalytics();
  } catch (err) {
    removeTypingIndicator(typingEl);
    appendErrorMessage("Error: " + (err.message || "Unknown error"));
  } finally {
    isSending = false;
    sendBtn.disabled = false;
    chatInput.focus();
  }
}

chatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  handleSend(chatInput.value);
});

chatInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    handleSend(chatInput.value);
  }
});

chatInput.addEventListener("input", () => {
  chatInput.style.height = "auto";
  chatInput.style.height = Math.min(chatInput.scrollHeight, 160) + "px";
});

sidebarCollapseBtn.addEventListener("click", () => {
  sidebar.classList.toggle("collapsed");
});

mobileMenuBtn.addEventListener("click", () => {
  sidebar.classList.toggle("mobile-open");
});

async function pollHealth() {
  const ok = await Api.checkHealth();
  connectionStatus.classList.toggle("online", ok);
  connectionStatus.classList.toggle("offline", !ok);
  connectionStatus.querySelector(".status-text").textContent = ok ? "Connected" : "Offline";
}

pollHealth();
setInterval(pollHealth, 15000);

window.addEventListener("load", () => {
  loadAnalytics();
  chatInput.focus();
});
