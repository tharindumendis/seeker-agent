// WebSocket-based Input Client (replaces polling)

class SeekerInputClient {
  constructor(apiBase) {
    this.apiBase = apiBase;
    this.ws = null;
    this.currentInputRequestId = null;
    this.reconnectDelay = 1000;
    this.maxReconnectDelay = 30000;

    this.connectWebSocket();
  }

  connectWebSocket() {
    const wsUrl = this.apiBase.replace("http", "ws") + "/ws/input";

    console.log(`🔌 Connecting to WebSocket: ${wsUrl}`);

    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log("✅ WebSocket connected");
      this.reconnectDelay = 1000; // Reset delay on successful connection
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      if (message.type === "input_request") {
        console.log("🔔 Instant input request received:", message.data);
        this.showInputModal(message.data);
      } else if (message.type === "ack") {
        console.log("✅ Response acknowledged:", message.success);
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

  showInputModal(request) {
    if (this.currentInputRequestId === request.id) {
      return;
    }

    this.currentInputRequestId = request.id;

    // Notify parent app to pause auto-trigger
    if (window.seekerClient) {
      console.log("⏸️ Pausing auto-trigger - waiting for user input");
      window.seekerClient.cancelAutoTrigger();
    }

    const modal = document.getElementById("inputModal");
    const promptEl = document.getElementById("inputPrompt");
    const responseInput = document.getElementById("inputResponse");

    promptEl.textContent = request.prompt;
    responseInput.value = "";
    modal.classList.add("active");

    // Focus after animation
    setTimeout(() => responseInput.focus(), 300);

    console.log(`🔔 Input request: ${request.prompt}`);
  }

  submitResponse(response) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.error("❌ WebSocket not connected");
      return false;
    }

    this.ws.send(
      JSON.stringify({
        type: "response",
        request_id: this.currentInputRequestId,
        response: response,
      }),
    );

    this.closeInputModal();
    return true;
  }

  closeInputModal() {
    const modal = document.getElementById("inputModal");
    modal.classList.remove("active");
    this.currentInputRequestId = null;

    // Resume auto-trigger
    if (window.seekerClient && window.seekerClient.lastAgentReplyTime) {
      console.log("▶️ Resuming auto-trigger after input handled");
      window.seekerClient.startAutoTrigger();
    }
  }
}

// Export for use in main app
window.SeekerInputClient = SeekerInputClient;
