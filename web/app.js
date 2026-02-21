// Modern Seeker Agent Client - Mobile-Optimized with WebSocket

class SeekerClient {
  constructor(apiBase = window.location.origin) {
    this.apiBase = apiBase;
    this.sessionId = null; // Will be set after first message or generated
    this.messageCount = 0;
    this.theme = localStorage.getItem("theme") || "light";
    this.autoTriggerTimer = null;
    this.autoTriggerDelay =
      (parseInt(localStorage.getItem("autoTriggerDelaySec"), 10) || 60) * 1000;
    this.isPaused = false; // Pause without fully disabling autonomous mode
    this.lastAgentReplyTime = null;
    this.lastResponseHadToolCalls = false; // Track if last reply had tool calls
    this.messageHistory = []; // New property for message history

    // Initialize WebSocket input client (replaces polling)
    this.inputClient = new SeekerInputClient(this.apiBase);

    // Initialize approvals manager
    window.approvalsManager = new ApprovalsManager(this.apiBase);

    this.init();

    // Auto-trigger if enabled (moved from original init, adapted)
    const autoTrigger = localStorage.getItem("autoTrigger") === "true";
    if (autoTrigger) {
      // Assuming triggerNoMessage is a new method or equivalent to sendNoMessage
      // For now, keeping original behavior, but if triggerNoMessage is intended, it needs to be defined.
      // If the intent was to send a 'no message' on load, it would be:
      // setTimeout(() => this.sendNoMessage(), 1000);
      // For now, I will not add this new auto-trigger logic as it's not fully defined in the context.
    }

    console.log("✅ Seeker Client initialized with WebSocket");
  }

  init() {
    this.applyTheme();
    this.cacheElements();
    this.attachEventListeners();
    this.loadTools();
    this.updateMemoryStatus();

    // Initialize approvals manager
    if (typeof ApprovalsManager !== "undefined") {
      window.approvalsManager = new ApprovalsManager(this.apiBase);
    }

    console.log("✅ Seeker Client initialized with WebSocket");
  }

  cacheElements() {
    // Input elements
    this.messageInput = document.getElementById("messageInput");
    this.sendBtn = document.getElementById("sendBtn");
    this.noMessageBtn = document.getElementById("noMessageBtn");
    this.chatMessages = document.getElementById("chatMessages");

    // UI controls
    this.themeToggle = document.getElementById("themeToggle");
    this.menuToggle = document.getElementById("menuToggle");
    this.closeSidebar = document.getElementById("closeSidebar");
    this.sidebar = document.getElementById("sidebar");
    this.overlay = document.getElementById("overlay");

    // Buttons
    this.memoryBtn = document.getElementById("memoryBtn");
    this.toolsBtn = document.getElementById("toolsBtn");
    this.clearMemoryBtn = document.getElementById("clearMemoryBtn");
    this.summarizeBtn = document.getElementById("summarizeBtn");

    // Status elements
    this.statusBadge = document.getElementById("statusBadge");
    this.sessionIdEl = document.getElementById("sessionId");
    this.messageCountEl = document.getElementById("messageCount");
    this.memoryCountEl = document.getElementById("memoryCount");
    this.historyCountEl = document.getElementById("historyCount");
  }

  attachEventListeners() {
    // Message sending
    this.sendBtn.addEventListener("click", () => this.sendMessage());
    this.noMessageBtn.addEventListener("click", () => this.sendNoMessage());

    this.messageInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });

    // Auto-resize textarea
    this.messageInput.addEventListener("input", () => {
      this.messageInput.style.height = "auto";
      this.messageInput.style.height =
        Math.min(this.messageInput.scrollHeight, 120) + "px";
      this.resetAutoTrigger();
    });

    this.messageInput.addEventListener("keydown", (e) => {
      if (e.key !== "Enter") {
        this.resetAutoTrigger();
      }
    });

    // Theme toggle
    this.themeToggle.addEventListener("click", () => this.toggleTheme());

    // Sidebar controls
    this.menuToggle.addEventListener("click", () => this.openSidebar());
    this.closeSidebar.addEventListener("click", () => this.closeSidebarMenu());
    this.overlay.addEventListener("click", () => this.closeSidebarMenu());

    // Memory controls
    this.memoryBtn.addEventListener("click", () => this.showMemoryModal());
    this.clearMemoryBtn.addEventListener("click", () => this.clearMemory());
    this.summarizeBtn.addEventListener("click", () => this.summarizeMemory());

    // Tools
    this.toolsBtn.addEventListener("click", () => this.showToolsModal());

    // Quick actions
    document.querySelectorAll(".quick-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const message = btn.getAttribute("data-message");
        this.messageInput.value = message;
        this.closeSidebarMenu();
        this.sendMessage();
      });
    });

    // Auto-trigger toggle
    const autoTriggerToggle = document.getElementById("autoTriggerToggle");
    const autoTriggerControls = document.getElementById("autoTriggerControls");
    const autoTriggerDelayInput = document.getElementById("autoTriggerDelay");
    const autoTriggerPauseBtn = document.getElementById("autoTriggerPause");

    if (autoTriggerToggle) {
      const savedState = localStorage.getItem("autoTrigger") === "true";
      autoTriggerToggle.checked = savedState;
      if (autoTriggerControls)
        autoTriggerControls.style.display = savedState ? "block" : "none";

      autoTriggerToggle.addEventListener("change", (e) => {
        const isEnabled = e.target.checked;
        localStorage.setItem("autoTrigger", isEnabled.toString());
        if (autoTriggerControls)
          autoTriggerControls.style.display = isEnabled ? "block" : "none";

        if (isEnabled) {
          this.isPaused = false;
          this.updatePauseBtn();
          console.log("✅ Autonomous mode enabled");
        } else {
          this.cancelAutoTrigger();
          console.log("❌ Autonomous mode disabled");
        }
      });
    }

    // Delay customisation
    if (autoTriggerDelayInput) {
      const savedSec =
        parseInt(localStorage.getItem("autoTriggerDelaySec"), 10) || 60;
      autoTriggerDelayInput.value = savedSec;

      autoTriggerDelayInput.addEventListener("change", () => {
        const sec = Math.max(
          5,
          parseInt(autoTriggerDelayInput.value, 10) || 60,
        );
        autoTriggerDelayInput.value = sec;
        localStorage.setItem("autoTriggerDelaySec", sec);
        this.autoTriggerDelay = sec * 1000;
        console.log(`⏱ Idle delay updated to ${sec}s`);
      });
    }

    // Pause / Resume button
    if (autoTriggerPauseBtn) {
      autoTriggerPauseBtn.addEventListener("click", () => {
        this.isPaused = !this.isPaused;
        this.updatePauseBtn();
        if (this.isPaused) {
          this.cancelAutoTrigger();
          this.updateAutoTriggerStatus("⏸ Paused");
          console.log("⏸ Auto-trigger paused");
        } else {
          console.log("▶ Auto-trigger resumed");
          this.startAutoTrigger(this.lastResponseHadToolCalls);
        }
      });
    }

    // Modal controls
    this.attachModalListeners();

    // Input modal - delegate to WebSocket client
    const submitInputBtn = document.getElementById("submitInput");
    const cancelInputBtn = document.getElementById("cancelInput");
    const inputResponse = document.getElementById("inputResponse");

    if (submitInputBtn) {
      submitInputBtn.addEventListener("click", () => {
        const response = inputResponse.value.trim();
        if (response) {
          this.inputClient.submitResponse(response);
        } else {
          alert("Please enter a response");
        }
      });
    }

    if (cancelInputBtn) {
      cancelInputBtn.addEventListener("click", () => {
        this.inputClient.closeInputModal();
      });
    }

    if (inputResponse) {
      inputResponse.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          const response = inputResponse.value.trim();
          if (response) {
            this.inputClient.submitResponse(response);
          }
        }
      });
    }
  }

  attachModalListeners() {
    document.querySelectorAll(".modal-close").forEach((btn) => {
      btn.addEventListener("click", () => {
        btn.closest(".modal").classList.remove("active");
      });
    });

    document.querySelectorAll(".modal").forEach((modal) => {
      modal.addEventListener("click", (e) => {
        if (e.target === modal) {
          modal.classList.remove("active");
        }
      });
    });
  }

  openSidebar() {
    this.sidebar.classList.add("open");
    this.overlay.classList.add("active");
    document.body.style.overflow = "hidden";
  }

  closeSidebarMenu() {
    this.sidebar.classList.remove("open");
    this.overlay.classList.remove("active");
    document.body.style.overflow = "";
  }

  async sendMessage() {
    const message = this.messageInput.value.trim();
    if (!message) return;

    this.cancelAutoTrigger();
    this.messageInput.value = "";
    this.messageInput.style.height = "auto";

    this.addMessage("user", message);
    this.setStatus("processing");

    try {
      const response = await fetch(`${this.apiBase}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: message,
          session_id: this.sessionId,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (data.session_id) {
        this.sessionId = data.session_id;
        this.sessionIdEl.textContent = data.session_id.substring(0, 8) + "...";
      }

      // Add agent message with safety checks and proper field mapping
      this.addMessage("agent", data.response || "No response", {
        thought: data.agent_thought || null,
        toolCalls: Array.isArray(data.tool_calls)
          ? data.tool_calls.map((tc) => ({
              name: tc.tool || tc.name || "Unknown Tool",
              args: tc.args || {},
              result: tc.result || "",
            }))
          : [],
      });

      this.messageCount++;
      this.messageCountEl.textContent = this.messageCount;
      this.updateMemoryStatus();
      this.setStatus("ready");

      // Smart auto-trigger: fire immediately if agent used tools, else wait
      const hadToolCalls =
        Array.isArray(data.tool_calls) && data.tool_calls.length > 0;
      this.lastResponseHadToolCalls = hadToolCalls;
      this.startAutoTrigger(hadToolCalls);
    } catch (error) {
      console.error("Error sending message:", error);
      this.addMessage("system", `❌ Error: ${error.message}`);
      this.setStatus("ready");
    }
  }

  async sendNoMessage() {
    this.cancelAutoTrigger();
    this.messageInput.value = "";
    this.messageInput.style.height = "auto";

    this.addMessage("system", '⏭️ Sending "No Message" to agent...');
    this.setStatus("processing");

    try {
      const response = await fetch(`${this.apiBase}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: "No message",
          session_id: this.sessionId,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (data.session_id) {
        this.sessionId = data.session_id;
        this.sessionIdEl.textContent = data.session_id.substring(0, 8) + "...";
      }

      // Add agent message with safety checks and proper field mapping
      this.addMessage("agent", data.response || "No response", {
        thought: data.agent_thought || null,
        toolCalls: Array.isArray(data.tool_calls)
          ? data.tool_calls.map((tc) => ({
              name: tc.tool || tc.name || "Unknown Tool",
              args: tc.args || {},
              result: tc.result || "",
            }))
          : [],
      });

      this.messageCount++;
      this.messageCountEl.textContent = this.messageCount;
      this.updateMemoryStatus();
      this.setStatus("ready");

      // Smart auto-trigger: fire immediately if agent used tools, else wait
      const hadToolCalls =
        Array.isArray(data.tool_calls) && data.tool_calls.length > 0;
      this.lastResponseHadToolCalls = hadToolCalls;
      this.startAutoTrigger(hadToolCalls);
    } catch (error) {
      console.error("Error sending no message:", error);
      this.addMessage("system", `❌ Error: ${error.message}`);
      this.setStatus("ready");
    }
  }

  addMessage(type, content, options = {}) {
    // Remove welcome message on first user message
    if (type === "user") {
      const welcomeMsg = this.chatMessages.querySelector(".welcome-message");
      if (welcomeMsg) {
        welcomeMsg.remove();
      }
    }

    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${type}-message`;

    let avatarHtml = "";
    if (type === "user") {
      avatarHtml = '<div class="message-avatar">U</div>';
    } else if (type === "agent") {
      avatarHtml = '<div class="message-avatar">AI</div>';
    }

    let thoughtHtml = "";
    if (options.thought) {
      thoughtHtml = `<div class="agent-thought">💭 ${this.escapeHtml(options.thought)}</div>`;
    }

    let toolCallsHtml = "";
    if (
      options.toolCalls &&
      Array.isArray(options.toolCalls) &&
      options.toolCalls.length > 0
    ) {
      const toolsContent = options.toolCalls
        .map((tool) => {
          const argsStr =
            Object.keys(tool.args || {}).length > 0
              ? JSON.stringify(tool.args, null, 2)
              : "No arguments";
          const resultStr = tool.result
            ? typeof tool.result === "string"
              ? tool.result
              : JSON.stringify(tool.result, null, 2)
            : "No result";

          return `<div class="tool-call">
          <div class="tool-call-header">
            <span class="tool-call-name">🔧 ${tool.name || "Unknown Tool"}</span>
          </div>
          <details class="tool-details">
            <summary>View Details</summary>
            <div class="tool-args">
              <strong>Arguments:</strong>
              <pre>${this.escapeHtml(argsStr)}</pre>
            </div>
            <div class="tool-result">
              <strong>Result:</strong>
              <pre>${this.escapeHtml(resultStr)}</pre>
            </div>
          </details>
        </div>`;
        })
        .join("");
      toolCallsHtml = `<div class="tool-calls">${toolsContent}</div>`;
    }

    messageDiv.innerHTML = `
      ${avatarHtml}
      <div class="message-content">
        ${this.formatContent(content)}
        ${thoughtHtml}
        ${toolCallsHtml}
      </div>
    `;

    this.chatMessages.appendChild(messageDiv);
    this.scrollToBottom();
  }

  formatContent(content) {
    return this.escapeHtml(content).replace(/\n/g, "<br>");
  }

  escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  scrollToBottom() {
    this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
  }

  setStatus(status) {
    if (status === "processing") {
      this.statusBadge.textContent = "Processing";
      this.statusBadge.classList.add("processing");
    } else {
      this.statusBadge.textContent = "Ready";
      this.statusBadge.classList.remove("processing");
    }
  }

  updatePauseBtn() {
    const pauseIcon = document.getElementById("pauseIcon");
    const resumeIcon = document.getElementById("resumeIcon");
    if (pauseIcon) pauseIcon.style.display = this.isPaused ? "none" : "inline";
    if (resumeIcon)
      resumeIcon.style.display = this.isPaused ? "inline" : "none";
  }

  startAutoTrigger(immediateIfToolCall = false) {
    // Only run if autonomous mode is enabled and not paused
    const autoEnabled = localStorage.getItem("autoTrigger") === "true";
    if (!autoEnabled || this.isPaused) return;

    this.cancelAutoTrigger();
    this.lastAgentReplyTime = Date.now();

    if (immediateIfToolCall) {
      // Agent used tools — chain immediately with a tiny delay just to let
      // the UI render the previous response before firing again.
      console.log("⚡ Auto-trigger: Tool call detected — firing immediately");
      this.updateAutoTriggerStatus("⚡ Tool call detected — triggering now...");
      this.autoTriggerTimer = setTimeout(() => {
        this.sendNoMessage();
      }, 300); // 300 ms — enough for UI to paint
    } else {
      // No tool calls — use normal 60-second idle delay
      console.log("⏰ Auto-trigger: No tool call — waiting 60s");
      this.updateAutoTriggerStatus("⏳ Idle — next trigger in 60s");
      this.autoTriggerTimer = setTimeout(() => {
        console.log('⏰ Auto-trigger: Sending "No Message"');
        this.updateAutoTriggerStatus("");
        this.sendNoMessage();
      }, this.autoTriggerDelay);
    }
  }

  updateAutoTriggerStatus(msg) {
    // Update a small status label in the UI if it exists
    const el = document.getElementById("autoTriggerStatus");
    if (el) el.textContent = msg;
  }

  resetAutoTrigger() {
    if (this.autoTriggerTimer) {
      clearTimeout(this.autoTriggerTimer);
      if (this.lastAgentReplyTime) {
        this.startAutoTrigger(false);
      }
    }
  }

  cancelAutoTrigger() {
    if (this.autoTriggerTimer) {
      clearTimeout(this.autoTriggerTimer);
      this.autoTriggerTimer = null;
    }
    this.updateAutoTriggerStatus("");
  }

  async updateMemoryStatus() {
    try {
      const response = await fetch(`${this.apiBase}/api/memory/status`);
      const data = await response.json();

      this.memoryCountEl.textContent = data.memory_count;
      this.historyCountEl.textContent = data.history_count;
    } catch (error) {
      console.error("Error updating memory status:", error);
    }
  }

  async loadTools() {
    try {
      const response = await fetch(`${this.apiBase}/api/tools`);
      const data = await response.json();
      this.tools = data.tools;
      console.log(`✅ Loaded ${this.tools.length} tools`);
    } catch (error) {
      console.error("Error loading tools:", error);
    }
  }

  async showToolsModal() {
    const modal = document.getElementById("toolsModal");
    const toolsList = document.getElementById("toolsList");

    if (!this.tools) {
      await this.loadTools();
    }

    toolsList.innerHTML = "";

    this.tools.forEach((tool) => {
      const toolDiv = document.createElement("div");
      toolDiv.className = "tool-item";
      toolDiv.innerHTML = `
        <h3>🔧 ${tool.name}</h3>
        <p>${tool.description}</p>
        <details>
          <summary>View Parameters</summary>
          <pre>${JSON.stringify(tool.parameters, null, 2)}</pre>
        </details>
      `;
      toolsList.appendChild(toolDiv);
    });

    modal.classList.add("active");
  }

  async showMemoryModal() {
    const modal = document.getElementById("memoryModal");
    const memoryDetails = document.getElementById("memoryDetails");

    memoryDetails.innerHTML =
      '<div class="loading-spinner"></div><p class="loading-text">Loading memory...</p>';
    modal.classList.add("active");

    try {
      const response = await fetch(`${this.apiBase}/api/memory`);
      const data = await response.json();

      memoryDetails.innerHTML = `
        <div style="margin-bottom: 1.5rem;">
          <h3>📊 Statistics</h3>
          <p><strong>Memory Entries:</strong> ${data.memory_count}</p>
          <p><strong>History Entries:</strong> ${data.history_count}</p>
          <p><strong>Summaries:</strong> ${data.summaries.length}</p>
        </div>
        
        <div style="margin-bottom: 1.5rem;">
          <h3>📝 Recent Entries</h3>
          ${data.recent_entries
            .map(
              (entry) => `
            <div style="padding: 0.75rem; margin-bottom: 0.5rem; background: var(--bg-tertiary); border-radius: var(--radius);">
              <strong>${entry.type}</strong> - ${new Date(entry.timestamp).toLocaleTimeString()}
              ${entry.content ? `<p style="margin-top: 0.25rem; font-size: 0.875rem;">${entry.content.substring(0, 100)}...</p>` : ""}
              ${entry.tool_name ? `<p style="margin-top: 0.25rem; font-size: 0.875rem;">Tool: ${entry.tool_name}</p>` : ""}
            </div>
          `,
            )
            .join("")}
        </div>
      `;
    } catch (error) {
      memoryDetails.innerHTML = `<p class="error">Error loading memory: ${error.message}</p>`;
    }
  }

  async clearMemory() {
    if (
      !confirm(
        "Are you sure you want to clear all memory? This cannot be undone.",
      )
    ) {
      return;
    }

    try {
      const response = await fetch(`${this.apiBase}/api/memory/clear`, {
        method: "POST",
      });

      const data = await response.json();
      alert(data.message);
      this.updateMemoryStatus();
    } catch (error) {
      alert(`Error clearing memory: ${error.message}`);
    }
  }

  async summarizeMemory() {
    try {
      this.setStatus("processing");

      const response = await fetch(`${this.apiBase}/api/memory/summarize`, {
        method: "POST",
      });

      const data = await response.json();
      alert(data.message);
      this.updateMemoryStatus();
      this.setStatus("ready");
    } catch (error) {
      alert(`Error summarizing memory: ${error.message}`);
      this.setStatus("ready");
    }
  }

  toggleTheme() {
    this.theme = this.theme === "light" ? "dark" : "light";
    this.applyTheme();
    localStorage.setItem("theme", this.theme);
  }

  applyTheme() {
    document.documentElement.setAttribute("data-theme", this.theme);
  }
}

// Initialize client
document.addEventListener("DOMContentLoaded", () => {
  window.seekerClient = new SeekerClient();
});
