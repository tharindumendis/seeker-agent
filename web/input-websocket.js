// WebSocket-based Input Client — queue-backed, thread-safe UI

class SeekerInputClient {
  constructor(apiBase) {
    this.apiBase = apiBase;
    this.ws = null;
    this.reconnectDelay = 1000;
    this.maxReconnectDelay = 30000;

    // ── Client-side FIFO queue of pending input_requests ──
    // Each entry: { id, prompt }
    // We only show one modal at a time; the next pops in when the current is answered.
    this._queue = [];
    this._activeRequest = null; // currently shown request

    this.connectWebSocket();
  }

  // ─── WebSocket connection ───────────────────────────────────────────────────

  connectWebSocket() {
    const wsUrl = this.apiBase.replace("http", "ws") + "/ws/input";
    console.log(`🔌 Connecting to WebSocket: ${wsUrl}`);

    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log("✅ WebSocket connected");
      this.reconnectDelay = 1000;
      // Note: server will replay any pending requests immediately on connect,
      // so we don't need to poll here.
    };

    this.ws.onmessage = (event) => {
      let message;
      try {
        message = JSON.parse(event.data);
      } catch (e) {
        console.error("⚠️ Invalid WS message:", event.data);
        return;
      }

      if (message.type === "input_request") {
        console.log("🔔 Input request received:", message.data);
        this._enqueue(message.data);
      } else if (message.type === "ack") {
        console.log("✅ Response acknowledged, success:", message.success);
      }
    };

    this.ws.onclose = () => {
      console.log(
        `🔌 WebSocket closed. Reconnecting in ${this.reconnectDelay / 1000}s...`,
      );
      setTimeout(() => {
        this.reconnectDelay = Math.min(
          this.reconnectDelay * 2,
          this.maxReconnectDelay,
        );
        this.connectWebSocket();
      }, this.reconnectDelay);
    };

    this.ws.onerror = (error) => {
      console.error("⚠️ WebSocket error:", error);
    };
  }

  // ─── Queue management ───────────────────────────────────────────────────────

  _enqueue(request) {
    // Deduplicate — server replays on reconnect, so the same request may arrive twice
    const alreadyQueued = this._queue.some((r) => r.id === request.id);
    const isActive =
      this._activeRequest && this._activeRequest.id === request.id;
    if (alreadyQueued || isActive) {
      console.log(
        `ℹ️ Skipping duplicate request: ${request.id.substring(0, 8)}`,
      );
      return;
    }

    this._queue.push(request);
    console.log(`📥 Queued request (queue size: ${this._queue.length})`);

    // If no modal is currently shown, pop immediately
    if (!this._activeRequest) {
      this._showNext();
    }
  }

  _showNext() {
    if (this._queue.length === 0) {
      this._activeRequest = null;
      return;
    }

    const request = this._queue.shift();
    this._activeRequest = request;
    this._renderModal(request);
  }

  // ─── Modal ──────────────────────────────────────────────────────────────────

  _renderModal(request) {
    // Pause auto-trigger while waiting for input
    if (window.seekerClient) {
      window.seekerClient.cancelAutoTrigger();
      window.seekerClient.updateAutoTriggerStatus(
        "⏸ Waiting for your input...",
      );
    }

    const modal = document.getElementById("inputModal");
    const promptEl = document.getElementById("inputPrompt");
    const responseInput = document.getElementById("inputResponse");
    const queueBadge = document.getElementById("inputQueueBadge");

    promptEl.textContent = request.prompt;
    responseInput.value = "";

    // Show how many more are waiting
    if (queueBadge) {
      const remaining = this._queue.length;
      queueBadge.textContent =
        remaining > 0 ? `+${remaining} more waiting` : "";
      queueBadge.style.display = remaining > 0 ? "inline-block" : "none";
    }

    modal.classList.add("active");
    setTimeout(() => responseInput.focus(), 300);

    console.log(
      `🔔 Showing input request: "${request.prompt}" (${this._queue.length} remaining in queue)`,
    );
  }

  // ─── Submit / close ─────────────────────────────────────────────────────────

  submitResponse(response) {
    if (!this._activeRequest) {
      console.error("❌ No active input request to respond to");
      return false;
    }

    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.error("❌ WebSocket not connected");
      return false;
    }

    this.ws.send(
      JSON.stringify({
        type: "response",
        request_id: this._activeRequest.id,
        response: response,
      }),
    );

    this._closeModal();
    return true;
  }

  closeInputModal() {
    // Called by cancel — we still need to clear the request so the queue advances
    this._closeModal();
  }

  _closeModal() {
    const modal = document.getElementById("inputModal");
    modal.classList.remove("active");
    this._activeRequest = null;

    // Show next queued request if any
    if (this._queue.length > 0) {
      console.log(
        `📤 Popping next queued request (${this._queue.length} remaining)`,
      );
      setTimeout(() => this._showNext(), 200); // tiny delay for UX
    } else {
      // Resume auto-trigger only when the queue is fully drained
      if (window.seekerClient && window.seekerClient.lastAgentReplyTime) {
        console.log("▶️ Resuming auto-trigger after all inputs handled");
        window.seekerClient.startAutoTrigger(
          window.seekerClient.lastResponseHadToolCalls,
        );
      }
    }
  }
}

// Export for use in main app
window.SeekerInputClient = SeekerInputClient;
