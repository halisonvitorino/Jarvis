const conversationList = document.getElementById("conversation-list");
const conversationTitle = document.getElementById("conversation-title");
const messages = document.getElementById("messages");
const messageInput = document.getElementById("message");
const composer = document.getElementById("composer");
const sendButton = document.getElementById("send-message");
const statusMessage = document.getElementById("status");
const assistantAnnouncement = document.getElementById("assistant-announcement");
const speakButton = document.getElementById("speak-button");
let activeSessionId = null;
let isSpeakingEnabled = false;
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

speakButton.addEventListener("click", () => {
  isSpeakingEnabled = !isSpeakingEnabled;
  speakButton.setAttribute("aria-pressed", isSpeakingEnabled);
  setStatus(isSpeakingEnabled ? "Modo de voz ativado." : "Modo de voz desativado.");
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
        speak: isSpeakingEnabled,
      }),
    });
    conversationTitle.textContent = response.title;
    addMessage("user", content);
    addMessage("assistant", response.response, true);
    if (response.spoken) {
      setStatus("Resposta falada pelo assistente.");
    } else if (isSpeakingEnabled) {
      setStatus("Resposta recebida (áudio indisponível).");
    } else {
      setStatus(`Resposta recebida. Modelo: ${response.model}`);
    }
    messageInput.value = "";
    pendingRequestId = null;
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

// Voice Reactive Three.js Sphere - initialization start
function initVoiceSphere() {
// Voice Reactive Three.js Sphere - animation loop
function animate() {
// Voice Reactive Three.js Sphere - color update
function updateSphereColor() {
// Voice Reactive Three.js Sphere - live caption
let isTyping = false;
// Voice Reactive Three.js Sphere - WebSocket and voice state
let wsVoice = null;
// Voice Reactive Three.js Sphere - start on DOM load
document.addEventListener("DOMContentLoaded", () => {
  initVoiceSphere();
  connectVoiceWS();
});
// Voice reactive state
let volumeData = { volume: 0.0, bands: [0.0] * 16 };
let voiceData = { volume: 0.0, bands: [0.0] * 16, speaking: false, thinking: false };

function connectVoiceWS() {
  wsVoice = new WebSocket(`ws:${window.location.host}/ws/voice`);
  
  wsVoice.onopen = () => console.log("Voice WS connected");
  
  wsVoice.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      updateVoiceState(data);
    } catch (e) {
      console.error("WS parse error:", e);
    }
  };
  
  wsVoice.onclose = () => {
    console.log("Voice WS disconnected");
    setTimeout(connectVoiceWS, 2000);
  };
  
  wsVoice.onerror = (error) => {
    console.error("WS error:", error);
  };
}

function updateVoiceState(data) {
  volumeData.volume = volumeData.volume + (data.volume - volumeData.volume) * 0.15;
  voiceData.volume = volumeData.volume;
  voiceData.speaking = data.speaking === true || volumeData.volume > 0.3;
  voiceData.thinking = data.thinking === true;
  
  if (data.bands) {
    for (let i = 0; i < 16; i++) {
      voiceData.bands[i] = voiceData.bands[i] + (data.bands[i] - voiceData.bands[i]) * 0.15;
    }
  }
  
  updateSphereVisuals();
  
  if (voiceData.speaking && !isTyping) {
    addLiveCaption("");
  }
}

function lerp(a, b, t) {
  return a + (b - a) * t;
}

// Voice Reactive Three.js Sphere - visual update
function updateSphereVisuals() {
  const baseScale = 1 + voiceData.volume * 0.3;
  sphere.scale.setScalar(baseScale);
  
  if (voiceData.speaking) {
    const speed = 0.02 + voiceData.volume * 0.1;
    sphere.rotation.y += speed;
    sphere.rotation.x += speed * 0.5;
  }
  
  sphere.material.emissiveIntensity = Math.min(0.5, voiceData.volume * 0.5);
}
// Voice Reactive Three.js Sphere - WebSocket and voice state end
let captionQueue = [];

function addLiveCaption(text) {
  if (isTyping) {
    captionQueue.push(text);
    return;
  }
  
  isTyping = true;
  const captionSpan = document.querySelector(".caption-text");
  const liveCaption = document.getElementById("live-caption");
  
  captionSpan.textContent = "";
  liveCaption.classList.add("visible");
  
  let i = 0;
  const typeInterval = setInterval(() => {
    if (i < text.length) {
      captionSpan.textContent += text.charAt(i);
      i++;
    } else {
      clearInterval(typeInterval);
      isTyping = false;
      
      if (captionQueue.length > 0) {
        const nextText = captionQueue.shift();
        setTimeout(() => addLiveCaption(nextText), 200);
      } else {
        setTimeout(() => {
          liveCaption.classList.remove("visible");
          isTyping = false;
        }, 1500);
      }
    }
  }, 30);
  
  captionSpan.style.animation = "type-on 0.5s forwards";
  captionSpan.style.background = "rgba(40, 120, 95, 0.8)";
}
// Voice Reactive Three.js Sphere - live caption end
  let targetColor;
  
  if (voiceData.speaking) {
    targetColor = 0xe74c3c;
    sphere.material.emissive = new THREE.Color(0xe74c3c);
    sphere.material.emissiveIntensity = 0.3 + 0.2 * Math.sin(Date.now() * 0.02);
  } else if (voiceData.thinking) {
    targetColor = 0x9b59b6;
    if (Math.sin(Date.now() * 0.01) > 0) {
      thinkingMesh.visible = true;
      thinkingMesh.material.opacity = 0.3 + 0.2 * Math.sin(Date.now() * 0.01);
    } else {
      thinkingMesh.visible = true;
      thinkingMesh.material.opacity = 0.1;
    }
  } else if (voiceData.volume > 0.1) {
    targetColor = 0xf39c12;
    sphere.material.emissive = new THREE.Color(0xf39c12);
    sphere.material.emissiveIntensity = voiceData.volume * 0.5;
  } else {
    targetColor = 0x28785f;
    thinkingMesh.visible = false;
    sphere.material.emissiveIntensity = 0;
  }
  
  sphere.material.color.setStyle(
    THREE.ColorUtils.lerpColor(
      new THREE.Color(sphere.material.color.getHex()),
      new THREE.Color(targetColor),
      0.1
    )
  );
}
// Voice Reactive Three.js Sphere - color update end
  requestAnimationFrame(animate);
  
  if (voiceData.speaking) {
    sphere.rotation.y += 0.02 * (1 + voiceData.volume);
    sphere.rotation.x += 0.01 * voiceData.volume;
  } else if (voiceData.thinking) {
    sphere.rotation.y += 0.005;
  } else {
    sphere.rotation.y += 0.002;
    sphere.rotation.x += 0.001;
  }
  
  const breatheScale = 1 + 0.05 * Math.sin(Date.now() * 0.002);
  sphere.scale.set(breatheScale, breatheScale, breatheScale);
  
  updateSphereColor();
  
  controls.update();
  renderer.render(scene, camera);
}
// Voice Reactive Three.js Sphere - animation loop end
  const container = document.getElementById("voice-sphere-canvas");
  if (!container) return;
  
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(60, container.clientWidth / container.clientHeight, 0.1, 1000);
  camera.position.z = 5;
  
  const renderer = new THREE.WebGLRenderer({ antialias: true, canvas: container });
  renderer.setSize(container.clientWidth, container.clientHeight);
  
  const geometry = new THREE.SphereGeometry(1, 64, 64);
  sphere = new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({ color: 0x28785f }));
  scene.add(sphere);
  
  const ambientLight = new THREE.AmbientLight(0x28785f, 0.5);
  scene.add(ambientLight);
  
  const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
  dirLight.position.set(5, 5, 5);
  scene.add(dirLight);
  
  thinkingMesh = new THREE.Mesh(
    new THREE.SphereGeometry(1.1, 64, 64),
    new THREE.MeshBasicMaterial({ color: 0x9b59b6, transparent: true, opacity: 0, visible: false })
  );
  scene.add(thinkingMesh);
  
  controls = new THREE.OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.05;
  
  window.addEventListener("resize", () => {
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
  });
  
  animate();
}
// Voice Reactive Three.js Sphere - initialization end
loadSessions().catch((error) => setStatus(error.message, true));
