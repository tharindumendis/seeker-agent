// Approvals Manager - WebSocket client for pending tool approvals

class ApprovalsManager {
  constructor(apiBase) {
    this.apiBase = apiBase;
    this.ws = null;
    this.pendingTools = new Map();
    this.reconnectDelay = 1000;
    this.maxReconnectDelay = 30000;

    this.connectWebSocket();
  }

  connectWebSocket() {
    const wsUrl = this.apiBase.replace("http", "ws") + "/ws/approvals";

    console.log(`🔌 Connecting to Approvals WebSocket: ${wsUrl}`);

    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log("✅ Approvals WebSocket connected");
      this.reconnectDelay = 1000;
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      if (message.type === "pending_tools") {
        // Initial pending tools on connection
        console.log("📋 Received pending tools:", message.data);
        message.data.forEach((tool) => this.addPendingTool(tool));
      } else if (message.type === "new_pending_tool") {
        // New tool added to queue
        console.log("🔔 New pending tool:", message.data);
        this.addPendingTool(message.data);
      } else if (message.type === "tool_update") {
        // Tool status updated
        console.log("🔄 Tool updated:", message.data);
        this.updateTool(message.data);
      } else if (message.type === "ack") {
        console.log("✅ Action acknowledged:", message);
      } else if (message.type === "error") {
        console.error("❌ Error:", message.message);
      }
    };

    this.ws.onclose = () => {
      console.log(
        `🔌 Approvals WebSocket closed. Reconnecting in ${this.reconnectDelay / 1000}s...`,
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
      console.error("⚠️ Approvals WebSocket error:", error);
    };
  }

  addPendingTool(tool) {
    this.pendingTools.set(tool.id, tool);
    this.renderPendingTools();
  }

  updateTool(tool) {
    if (
      tool.status === "completed" ||
      tool.status === "denied" ||
      tool.status === "error"
    ) {
      // Show result in chat
      if (window.seekerClient) {
        let message = "";
        if (tool.status === "completed") {
          message = `✅ **Tool Executed:** ${tool.tool_name}\n\n**Result:**\n\`\`\`\n${tool.result}\n\`\`\``;
        } else if (tool.status === "denied") {
          message = `❌ **Tool Denied:** ${tool.tool_name}\n\n${tool.error || "User denied execution"}`;
        } else if (tool.status === "error") {
          message = `⚠️ **Tool Error:** ${tool.tool_name}\n\n${tool.error}`;
        }

        window.seekerClient.addMessage("agent", message);
      }

      // Remove from pending list after short delay
      setTimeout(() => {
        this.pendingTools.delete(tool.id);
        this.renderPendingTools();
      }, 3000);
    } else {
      this.pendingTools.set(tool.id, tool);
    }
    this.renderPendingTools();
  }

  renderPendingTools() {
    const container = document.getElementById("pendingApprovals");
    if (!container) return;

    const pending = Array.from(this.pendingTools.values())
      .filter((tool) => tool.status === "pending")
      .sort((a, b) => b.timestamp - a.timestamp);

    if (pending.length === 0) {
      container.innerHTML =
        '<div class="no-pending">No pending approvals</div>';
      return;
    }

    container.innerHTML = pending
      .map(
        (tool) => `
      <div class="pending-tool" data-tool-id="${tool.id}">
        <div class="tool-header">
          <span class="tool-name">🔧 ${tool.tool_name}</span>
          <span class="tool-time">${this.formatTime(tool.timestamp)}</span>
        </div>
        <div class="tool-args">
          <strong>Command:</strong>
          <code>${this.escapeHtml(tool.args.command || JSON.stringify(tool.args))}</code>
        </div>
        <div class="tool-actions">
          <button class="btn-approve" onclick="window.approvalsManager.approve('${tool.id}')">
            ✅ Approve
          </button>
          <button class="btn-deny" onclick="window.approvalsManager.deny('${tool.id}')">
            ❌ Deny
          </button>
        </div>
      </div>
    `,
      )
      .join("");
  }

  approve(toolId) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.error("❌ WebSocket not connected");
      return;
    }

    this.ws.send(
      JSON.stringify({
        type: "approve",
        tool_id: toolId,
        user_response: "yes",
      }),
    );

    console.log(`✅ Approved tool: ${toolId.substring(0, 8)}...`);
  }

  deny(toolId) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.error("❌ WebSocket not connected");
      return;
    }

    this.ws.send(
      JSON.stringify({
        type: "deny",
        tool_id: toolId,
        reason: "User denied",
      }),
    );

    console.log(`❌ Denied tool: ${toolId.substring(0, 8)}...`);
  }

  formatTime(timestamp) {
    const date = new Date(timestamp * 1000);
    const now = new Date();
    const diff = Math.floor((now - date) / 1000);

    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    return date.toLocaleTimeString();
  }

  escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }
}

// Export for use in main app
window.ApprovalsManager = ApprovalsManager;
