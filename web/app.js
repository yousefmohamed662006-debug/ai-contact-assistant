/**
 * AI Contact Assistant - Frontend Application Logic
 * Supports real-time chat, card rendering, voice recognition, bilingual UI, and live network failover detection.
 */

document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const htmlRoot = document.getElementById("htmlRoot");
  const chatForm = document.getElementById("chatForm");
  const chatInput = document.getElementById("chatInput");
  const messagesContainer = document.getElementById("messagesContainer");
  const voiceBtn = document.getElementById("voiceBtn");
  const voiceRecordingBar = document.getElementById("voiceRecordingBar");
  const voiceStatusText = document.getElementById("voiceStatusText");
  const stopVoiceBtn = document.getElementById("stopVoiceBtn");
  const directoryList = document.getElementById("directoryList");
  const directorySearchInput = document.getElementById("directorySearchInput");
  const sidebar = document.getElementById("sidebar");
  const openSidebarBtn = document.getElementById("openSidebarBtn");
  const closeSidebarBtn = document.getElementById("closeSidebarBtn");
  const contactModal = document.getElementById("contactModal");
  const modalCardContent = document.getElementById("modalCardContent");
  const settingsBtn = document.getElementById("settingsBtn");
  const settingsModal = document.getElementById("settingsModal");
  const closeSettingsBtn = document.getElementById("closeSettingsBtn");
  const cancelSettingsBtn = document.getElementById("cancelSettingsBtn");
  const saveSettingsBtn = document.getElementById("saveSettingsBtn");
  const apiKeyInput = document.getElementById("apiKeyInput");
  const langToggleBtn = document.getElementById("langToggleBtn");
  const modeToggleBtn = document.getElementById("modeToggleBtn");
  const modeToggleText = document.getElementById("modeToggleText");

  // UI Translation Elements
  const sidebarTitle = document.getElementById("sidebarTitle");
  const sidebarSubtitle = document.getElementById("sidebarSubtitle");
  const sidebarToggleText = document.getElementById("sidebarToggleText");
  const headerMainTitle = document.getElementById("headerMainTitle");
  const headerSubTitle = document.getElementById("headerSubTitle");
  const engineStatusText = document.getElementById("engineStatusText");
  const welcomeBubble = document.getElementById("welcomeBubble");

  let currentLang = "ar"; // 'ar' or 'en'
  let currentMode = "offline"; // 'offline' or 'online'
  let allContacts = [];
  let recognition = null;
  let isRecording = false;

  const translations = {
    ar: {
      toggleBtn: "🌐 English",
      modeOffline: "أوفلاين (محلي)",
      modeOnline: "أونلاين (Gemini)",
      sidebarTitle: "Smart Directory",
      sidebarSubtitle: "دليل الشركة الذكي",
      sidebarToggleText: "دليل الموظفين",
      headerMainTitle: "المساعد الذكي لكبار المسؤولين",
      headerSubTitle: "Smart Directory AI Assistant",
      engineStatusOffline: "المحرك: محلي (Offline)",
      engineStatusOnline: "المحرك: سحابي (Gemini Online)",
      searchInputPlaceholder: "بحث سريع في كل الموظفين...",
      chatInputPlaceholder: "اسألني أو أقدر أساعدك إزاي...",
      voiceListening: "جاري الاستماع لصوتك... تكلم الآن",
      welcomeMessage: `
        <p>أهلاً بك يا فندم! 👋 أنا المساعد الذكي لدليل موظفي الشركة.</p>
        <p>تقدر تسألني بالصوت 🎙️ أو بالكتابة ✍️ عن أي موظف بالاسم، بالقسم، بالوظيفة، أو بالدور والمبنى وسأوافيك بكافة تفاصيله فوراً.</p>
      `,
      callBtn: "📞 اتصال",
      emailBtn: "✉️ إيميل",
      extBadge: "🔢 تحويلة",
      officeLocation: "🏢 مكان المكتب",
      building: "مبنى",
      manager: "👤 المدير المباشر",
      responsibilities: "📋 أبرز المهام والمسؤوليات:",
      viewDetails: "عرض التفاصيل 🔍"
    },
    en: {
      toggleBtn: "🌐 عربي",
      modeOffline: "Offline (Local)",
      modeOnline: "Online (Gemini)",
      sidebarTitle: "Smart Directory",
      sidebarSubtitle: "Enterprise Employee Directory",
      sidebarToggleText: "All Contacts",
      headerMainTitle: "AI Executive Directory Assistant",
      headerSubTitle: "Fast Enterprise Contact Lookup",
      engineStatusOffline: "Engine: Local (Offline)",
      engineStatusOnline: "Engine: Cloud (Gemini Online)",
      searchInputPlaceholder: "Quick search across all staff...",
      chatInputPlaceholder: "Ask me anything or how can I help you...",
      voiceListening: "Listening to your voice... Speak now",
      welcomeMessage: `
        <p>Welcome! 👋 I am your AI Enterprise Directory Assistant.</p>
        <p>Ask me via voice 🎙️ or text ✍️ to look up any colleague by name, department, role, or office floor, and I will display their full details immediately.</p>
      `,
      callBtn: "📞 Call",
      emailBtn: "✉️ Email",
      extBadge: "🔢 Ext",
      officeLocation: "🏢 Office Location",
      building: "Building",
      manager: "👤 Direct Manager",
      responsibilities: "📋 Key Responsibilities & Skills:",
      viewDetails: "View Details 🔍"
    }
  };

  // 1. Initialize
  fetchContacts();
  checkHealth();
  initSpeechRecognition();

  // Live Browser Network Listeners (Instant Automatic Failover)
  window.addEventListener("offline", () => {
    currentMode = "offline";
    updateModeUI();
  });

  window.addEventListener("online", () => {
    checkHealth();
  });

  // 2. Mode Toggle (Online <-> Offline)
  modeToggleBtn.addEventListener("click", async () => {
    currentMode = (currentMode === "offline") ? "online" : "offline";
    updateModeUI();
    try {
      await fetch("/api/set-mode", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode: currentMode })
      });
    } catch (err) {}
  });

  function updateModeUI() {
    const t = translations[currentLang];
    if (currentMode === "online" && navigator.onLine) {
      modeToggleBtn.classList.add("online");
      modeToggleBtn.querySelector(".mode-icon").textContent = "🌐";
      modeToggleText.textContent = t.modeOnline;
      engineStatusText.textContent = t.engineStatusOnline;
    } else {
      currentMode = "offline";
      modeToggleBtn.classList.remove("online");
      modeToggleBtn.querySelector(".mode-icon").textContent = "⚡";
      modeToggleText.textContent = t.modeOffline;
      engineStatusText.textContent = t.engineStatusOffline;
    }
  }

  // 3. Language Switcher Event
  langToggleBtn.addEventListener("click", () => {
    currentLang = (currentLang === "ar") ? "en" : "ar";
    applyLanguage(currentLang);
  });

  function applyLanguage(lang) {
    const t = translations[lang];
    htmlRoot.setAttribute("lang", lang);
    htmlRoot.setAttribute("dir", lang === "ar" ? "rtl" : "ltr");

    langToggleBtn.textContent = t.toggleBtn;
    sidebarTitle.textContent = t.sidebarTitle;
    sidebarSubtitle.textContent = t.sidebarSubtitle;
    sidebarToggleText.textContent = t.sidebarToggleText;
    headerMainTitle.textContent = t.headerMainTitle;
    headerSubTitle.textContent = t.headerSubTitle;
    directorySearchInput.placeholder = t.searchInputPlaceholder;
    chatInput.placeholder = t.chatInputPlaceholder;
    voiceStatusText.textContent = t.voiceListening;
    welcomeBubble.innerHTML = t.welcomeMessage;

    updateModeUI();

    if (recognition) {
      recognition.lang = (lang === "ar") ? "ar-EG" : "en-US";
    }

    fetchContacts();
  }

  // 4. Event Listeners
  chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const query = chatInput.value.trim();
    if (query) {
      handleUserMessage(query);
      chatInput.value = "";
    }
  });

  // Sidebar Toggles
  openSidebarBtn.addEventListener("click", () => sidebar.classList.add("open"));
  closeSidebarBtn.addEventListener("click", () => sidebar.classList.remove("open"));

  // Directory Filter
  directorySearchInput.addEventListener("input", (e) => {
    const term = e.target.value.toLowerCase();
    renderDirectory(allContacts.filter(c => 
      c.name.toLowerCase().includes(term) ||
      c.role.toLowerCase().includes(term) ||
      c.department.toLowerCase().includes(term) ||
      c.phone.includes(term) ||
      c.building.toLowerCase().includes(term)
    ));
  });

  // Settings Modal
  settingsBtn.addEventListener("click", () => settingsModal.style.display = "flex");
  closeSettingsBtn.addEventListener("click", () => settingsModal.style.display = "none");
  cancelSettingsBtn.addEventListener("click", () => settingsModal.style.display = "none");
  
  saveSettingsBtn.addEventListener("click", async () => {
    const key = apiKeyInput.value.trim();
    if (key) {
      try {
        await fetch("/api/set-api-key", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ api_key: key })
        });
        currentMode = "online";
        updateModeUI();
      } catch (err) {
        console.error(err);
      }
    }
    settingsModal.style.display = "none";
  });

  contactModal.addEventListener("click", (e) => {
    if (e.target === contactModal) contactModal.style.display = "none";
  });
  settingsModal.addEventListener("click", (e) => {
    if (e.target === settingsModal) settingsModal.style.display = "none";
  });

  // 5. Voice Input Setup
  function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      voiceBtn.title = "المتصفح لا يدعم التسجيل الصوتي مباشرة";
      return;
    }

    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = (currentLang === "ar") ? "ar-EG" : "en-US";

    recognition.onstart = () => {
      isRecording = true;
      voiceRecordingBar.style.display = "flex";
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      if (transcript) {
        chatInput.value = "";
        handleUserMessage(transcript);
      }
    };

    recognition.onerror = (event) => {
      console.warn("Speech recognition error:", event.error);
      stopVoiceRecording();
    };

    recognition.onend = () => {
      stopVoiceRecording();
    };

    voiceBtn.addEventListener("click", () => {
      if (!isRecording) {
        try {
          recognition.start();
        } catch (err) {
          console.error(err);
        }
      } else {
        stopVoiceRecording();
      }
    });

    stopVoiceBtn.addEventListener("click", () => {
      stopVoiceRecording();
    });
  }

  function stopVoiceRecording() {
    isRecording = false;
    voiceRecordingBar.style.display = "none";
    if (recognition) {
      try { recognition.stop(); } catch (e) {}
    }
  }

  // 6. Chat Interaction
  async function handleUserMessage(query) {
    appendUserMessage(query);
    const typingElem = appendTypingIndicator();

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          message: query,
          mode: currentMode
        })
      });

      const data = await response.json();
      typingElem.remove();

      // If backend reports failover or internet dropped, immediately flip mode button visually
      if (data.failover || data.engine_mode === "local_offline") {
        if (currentMode === "online") {
          currentMode = "offline";
          updateModeUI();
        }
      }

      appendAssistantResponse(data);
    } catch (err) {
      typingElem.remove();
      appendAssistantResponse({
        reply: currentLang === "ar" 
          ? "عذراً، تعذر الاتصال بسيرفر الباك إند المحلي. يرجى التأكد من تشغيل `python run.py`." 
          : "Sorry, could not connect to local backend server. Please verify `python run.py` is running.",
        status: "none",
        contacts: []
      });
    }
  }

  async function fetchContacts() {
    try {
      const res = await fetch(`/api/contacts?lang=${currentLang}`);
      const data = await res.json();
      allContacts = data.contacts || [];
      renderDirectory(allContacts);
    } catch (err) {
      console.error("Failed to load directory", err);
    }
  }

  async function checkHealth() {
    try {
      const res = await fetch("/api/health");
      const data = await res.json();
      if (data.gemini_active && data.active_mode === "online" && navigator.onLine) {
        currentMode = "online";
      } else {
        currentMode = "offline";
      }
      updateModeUI();
    } catch (err) {}
  }

  // 7. DOM Rendering
  function appendUserMessage(text) {
    const group = document.createElement("div");
    group.className = "message-group user";
    group.innerHTML = `<div class="bubble">${escapeHtml(text)}</div>`;
    messagesContainer.appendChild(group);
    scrollToBottom();
  }

  function appendTypingIndicator() {
    const group = document.createElement("div");
    group.className = "message-group assistant";
    const text = (currentLang === "ar") ? "جاري المعالجة والبحث في الدليل... ⏳" : "Processing and searching directory... ⏳";
    group.innerHTML = `
      <div class="assistant-avatar">🤖</div>
      <div class="message-content">
        <div class="bubble">${text}</div>
      </div>
    `;
    messagesContainer.appendChild(group);
    scrollToBottom();
    return group;
  }

  function appendAssistantResponse(data) {
    const group = document.createElement("div");
    group.className = "message-group assistant";

    const avatar = document.createElement("div");
    avatar.className = "assistant-avatar";
    avatar.textContent = "🤖";

    const content = document.createElement("div");
    content.className = "message-content";

    // Text Bubble
    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.innerHTML = formatMarkdown(data.reply);
    content.appendChild(bubble);

    // Cards
    if (data.status === "single" && data.contacts && data.contacts.length > 0) {
      const card = renderSingleContactCard(data.contacts[0]);
      content.appendChild(card);
    } else if (data.status === "multiple" && data.contacts && data.contacts.length > 0) {
      const multiWrapper = document.createElement("div");
      multiWrapper.className = "contact-cards-wrapper";
      data.contacts.forEach(c => {
        const choiceCard = renderChoiceCard(c);
        multiWrapper.appendChild(choiceCard);
      });
      content.appendChild(multiWrapper);
    }

    group.appendChild(avatar);
    group.appendChild(content);
    messagesContainer.appendChild(group);
    scrollToBottom();
  }

  function renderSingleContactCard(c) {
    const card = document.createElement("div");
    card.className = "contact-card-single";
    const t = translations[currentLang];

    const responsibilitiesHtml = (c.responsibilities || []).map(r => 
      `<span class="skill-pill">${escapeHtml(r)}</span>`
    ).join("");

    card.innerHTML = `
      <div class="card-header-main">
        <div class="card-avatar-large" style="background-color: ${c.avatar_color}">
          ${c.avatar_initials}
        </div>
        <div class="card-title-group">
          <h3>${escapeHtml(c.name)}</h3>
          <div class="role-badge">${escapeHtml(c.role)}</div>
          <span class="dept-tag">🏛️ ${escapeHtml(c.department)}</span>
        </div>
      </div>

      <!-- Contact Info Blocks -->
      <div class="card-contact-info-grid">
        <a href="tel:${c.phone}" class="contact-info-item phone-block">
          <span class="info-icon">📞</span>
          <div class="info-text">
            <span class="info-label">${t.callBtn}</span>
            <strong class="info-val">${escapeHtml(c.phone)}</strong>
          </div>
        </a>
        <a href="mailto:${c.email}" class="contact-info-item email-block">
          <span class="info-icon">✉️</span>
          <div class="info-text">
            <span class="info-label">${t.emailBtn}</span>
            <strong class="info-val">${escapeHtml(c.email)}</strong>
          </div>
        </a>
      </div>

      <div class="card-actions-row" style="margin-top: -4px;">
        <div class="action-btn ext-badge" style="flex: 1;">
          ${t.extBadge}: ${escapeHtml(c.extension)}
        </div>
      </div>

      <div class="card-details-grid">
        <div class="detail-item">
          <span class="detail-label">${t.officeLocation}</span>
          <span class="detail-val">${t.building} ${c.building} - ${c.floor}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">${t.manager}</span>
          <span class="detail-val">${escapeHtml(c.manager_name)}</span>
        </div>
      </div>

      ${responsibilitiesHtml ? `
        <div class="card-skills-section">
          <span class="skills-label">${t.responsibilities}</span>
          <div class="skills-tags">
            ${responsibilitiesHtml}
          </div>
        </div>
      ` : ""}
    `;
    return card;
  }

  function renderChoiceCard(c) {
    const card = document.createElement("div");
    card.className = "multi-choice-card";
    const t = translations[currentLang];

    card.innerHTML = `
      <div class="multi-card-left">
        <div class="dir-avatar" style="background-color: ${c.avatar_color}">
          ${c.avatar_initials}
        </div>
        <div class="multi-card-info">
          <h4>${escapeHtml(c.name)}</h4>
          <p>${escapeHtml(c.role)} • ${t.building} ${c.building}</p>
        </div>
      </div>
      <div class="view-btn-pill">${t.viewDetails}</div>
    `;

    card.addEventListener("click", () => openContactModal(c));
    return card;
  }

  function renderDirectory(contacts) {
    directoryList.innerHTML = "";
    contacts.forEach(c => {
      const item = document.createElement("div");
      item.className = "dir-contact-item";
      item.innerHTML = `
        <div class="dir-avatar" style="background-color: ${c.avatar_color}">
          ${c.avatar_initials}
        </div>
        <div class="dir-info">
          <h4>${escapeHtml(c.name)}</h4>
          <p>${escapeHtml(c.role)}</p>
        </div>
      `;
      item.addEventListener("click", () => {
        openContactModal(c);
        if (window.innerWidth <= 768) sidebar.classList.remove("open");
      });
      directoryList.appendChild(item);
    });
  }

  function openContactModal(contact) {
    modalCardContent.innerHTML = "";
    const card = renderSingleContactCard(contact);
    
    const closeBtn = document.createElement("button");
    closeBtn.className = "close-btn";
    closeBtn.style.cssText = "align-self: flex-end; margin-bottom: 8px;";
    closeBtn.textContent = "✕";
    closeBtn.onclick = () => contactModal.style.display = "none";

    modalCardContent.appendChild(closeBtn);
    modalCardContent.appendChild(card);
    contactModal.style.display = "flex";
  }

  function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function formatMarkdown(text) {
    if (!text) return "";
    let html = escapeHtml(text);
    html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    html = html.replace(/\n/g, "<br>");
    return html;
  }
});
