const conversationList = document.getElementById("conversation-list");
const conversationTitle = document.getElementById("conversation-title");
const messages = document.getElementById("messages");
const messageInput = document.getElementById("message");
const composer = document.getElementById("composer");
const sendButton = document.getElementById("send-message");
const statusMessage = document.getElementById("status");
const assistantAnnouncement = document.getElementById("assistant-announcement");
let activeSessionId = null;
let isSending = false;
let isCreatingSession = false;
let sessionLoadToken = 0;
let sessionListToken = 0;
let pendingRequestId = null;

messageInput.addEventListener("input", () => {
  pendingRequestId = null;
});

async function requestJson(path, options = {}) {
  const response = await fetch(path, options);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(
      payload.detail || "Não foi possível concluir a solicitação.",
    );
  }
  return payload;
}

function setStatus(message, isError = false) {
  statusMessage.textContent = message;
  statusMessage.dataset.state = isError ? "error" : "ready";
}

function addMessage(role, content, announce = false) {
  document.getElementById("empty-state")?.remove();
  const article = document.createElement("article");
  article.className = "message";
  article.dataset.role = role;

  const label = document.createElement("span");
  label.className = "message-role";
  label.textContent = role === "user" ? "Você" : "J.A.R.V.I.S.";

  const text = document.createElement("p");
  text.className = "message-content";
  text.textContent = content;
  article.append(label, text);
  messages.append(article);
  messages.scrollTop = messages.scrollHeight;
  if (role === "assistant" && announce)
    assistantAnnouncement.textContent = content;
}

function showEmptyState() {
  if (messages.children.length) return;
  const emptyState = document.createElement("div");
  emptyState.className = "empty-state";
  emptyState.id = "empty-state";
  const heading = document.createElement("h2");
  heading.textContent = "Como posso ajudar?";
  const description = document.createElement("p");
  description.textContent = "Escreva uma mensagem para iniciar a conversa.";
  emptyState.append(heading, description);
  messages.append(emptyState);
}

async function loadSessions(selectedId = activeSessionId) {
  const loadToken = ++sessionListToken;
  let payload;
  try {
    payload = await requestJson("/api/sessions");
  } catch (error) {
    if (loadToken !== sessionListToken) return;
    throw error;
  }
  if (loadToken !== sessionListToken) return;
  conversationList.replaceChildren();
  if (!payload.sessions.length) {
    const emptyItem = document.createElement("li");
    emptyItem.className = "history-empty";
    emptyItem.textContent = "Nenhuma conversa";
    conversationList.append(emptyItem);
    return;
  }

  for (const session of payload.sessions) {
    const item = document.createElement("li");
    const button = document.createElement("button");
    button.className = "conversation-item";
    button.type = "button";
    button.disabled = isSending;
    button.textContent = session.title;
    button.setAttribute(
      "aria-current",
      session.session_id === selectedId ? "page" : "false",
    );
    button.addEventListener("click", () => openSession(session.session_id));
    item.append(button);
    conversationList.append(item);
  }
}

async function openSession(sessionId) {
  if (isSending) return;
  const loadToken = ++sessionLoadToken;
  sessionListToken += 1;
  try {
    const session = await requestJson(
      `/api/sessions/${encodeURIComponent(sessionId)}`,
    );
    if (loadToken !== sessionLoadToken || isSending) return;
    activeSessionId = session.session_id;
    conversationTitle.textContent = session.title;
    messages.replaceChildren();
    for (const message of session.messages)
      addMessage(message.role, message.content);
    showEmptyState();
    await loadSessions(activeSessionId);
    setStatus("Conversa aberta");
  } catch (error) {
    if (loadToken === sessionLoadToken && !isSending) {
      setStatus(error.message, true);
    }
  }
}

async function startSession() {
  const createToken = ++sessionLoadToken;
  sessionListToken += 1;
  try {
    const payload = await requestJson("/api/sessions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: "Nova conversa" }),
    });
    if (createToken !== sessionLoadToken) {
      await loadSessions(activeSessionId);
      return false;
    }
    activeSessionId = payload.session_id;
    conversationTitle.textContent = payload.title;
    messages.replaceChildren();
    showEmptyState();
    await loadSessions(activeSessionId);
    setStatus("Conversa aberta");
    return true;
  } catch (error) {
    if (createToken !== sessionLoadToken) return false;
    throw error;
  }
}

document.getElementById("new-session").addEventListener("click", async () => {
  if (isSending || isCreatingSession) return;
  isCreatingSession = true;
  document.getElementById("new-session").disabled = true;
  try {
    await startSession();
    messageInput.focus();
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    isCreatingSession = false;
    document.getElementById("new-session").disabled = false;
  }
});

composer.addEventListener("submit", async (event) => {
  event.preventDefault();
  const content = messageInput.value.trim();
  if (!content || isSending || isCreatingSession) return;

  isSending = true;
  sessionLoadToken += 1;
  sessionListToken += 1;
  sendButton.disabled = true;
  messageInput.disabled = true;
  document.getElementById("new-session").disabled = true;
  setStatus("Enviando...");
  try {
    if (!activeSessionId && !(await startSession())) return;
    pendingRequestId ??= crypto.randomUUID();
    const response = await requestJson("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: activeSessionId,
        message: content,
        request_id: pendingRequestId,
      }),
    });
    conversationTitle.textContent = response.title;
    addMessage("user", content);
    addMessage("assistant", response.response, true);
    messageInput.value = "";
    pendingRequestId = null;
    await loadSessions(activeSessionId);
    setStatus(`Resposta recebida. Modelo: ${response.model}`);
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    isSending = false;
    sendButton.disabled = false;
    messageInput.disabled = false;
    document.getElementById("new-session").disabled = false;
    await loadSessions(activeSessionId).catch(() => {});
    messageInput.focus();
  }
});

loadSessions().catch((error) => setStatus(error.message, true));
