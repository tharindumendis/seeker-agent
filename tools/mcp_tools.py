"""
MCP (Model Context Protocol) plug-and-play integration for Seeker.
-------------------------------------------------------------------
Reads  config/mcp_servers.json  and dynamically exposes every tool
from every enabled MCP server as a native Seeker BaseTool.

Adding a new MCP server requires ONLY a JSON entry in the config:

  config/mcp_servers.json
  ─────────────────────────────────────────────────────────────────
  {
    "mcpServers": {
      "MyServer": {
        "command": "python",
        "args":    ["path/to/server.py"],
        "env":     {},
        "description": "optional human label",
        "enabled": true
      }
    }
  }

Uses a lightweight raw JSON-RPC stdio transport (no mcp/fastmcp
client library required) for maximum compatibility.
"""

from __future__ import annotations

import sys as _sys

import json
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import BaseTool


# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────

def _load_mcp_config() -> Dict[str, Any]:
    """Return the 'mcpServers' dict from config/mcp_servers.json."""
    config_path = Path(__file__).parent.parent / "config" / "mcp_servers.json"
    if not config_path.exists():
        return {}
    with open(config_path, "r", encoding="utf-8") as fh:
        return json.load(fh).get("mcpServers", {})


# ─────────────────────────────────────────────────────────────────────────────
# Raw JSON-RPC stdio MCP client
# ─────────────────────────────────────────────────────────────────────────────

class _MCPSession:
    """
    Lightweight MCP client that speaks JSON-RPC 2.0 over stdio.
    Works with any MCP-compliant server regardless of library version.
    """

    MCP_VERSION = "2024-11-05"

    def __init__(self, command: str, args: List[str], env: Optional[Dict] = None):
        merged_env = {**os.environ, **(env or {})}

        # Always use the same Python interpreter as the running process so that
        # venv packages (fastmcp, ollama, etc.) are available in the subprocess.
        resolved_cmd = command
        if command.lower() in ("python", "python3"):
            resolved_cmd = _sys.executable

        self._proc = subprocess.Popen(
            [resolved_cmd] + args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,      # capture for diagnostics
            env=merged_env,
        )
        self._lock = threading.Lock()
        self._req_id = 0
        self._initialized = False

    # ── low-level JSON-RPC ────────────────────────────────────────────────────

    def _next_id(self) -> int:
        self._req_id += 1
        return self._req_id

    def _send(self, method: str, params: Any = None, req_id: Any = None) -> None:
        msg: Dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if req_id is not None:
            msg["id"] = req_id
        if params is not None:
            msg["params"] = params
        line = json.dumps(msg, separators=(",", ":")) + "\n"
        self._proc.stdin.write(line.encode())
        self._proc.stdin.flush()

    def _recv(self, timeout: float = 30.0) -> Dict[str, Any]:
        """Read the next complete JSON-RPC message from stdout."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            # Check process is alive
            if self._proc.poll() is not None:
                # Drain stderr for a useful error message
                stderr_out = ""
                try:
                    stderr_out = self._proc.stderr.read().decode(errors="replace").strip()
                except Exception:
                    pass
                hint = f"\n  stderr: {stderr_out[-400:]}" if stderr_out else ""
                raise RuntimeError(f"MCP server process has exited (code {self._proc.returncode}){hint}")
            line = self._proc.stdout.readline()
            if line:
                line = line.strip()
                if line:
                    return json.loads(line)
        raise TimeoutError("Timed out waiting for MCP server response")

    def _request(self, method: str, params: Any = None, timeout: float = 30.0) -> Any:
        """Send a request and return result (raises on error)."""
        with self._lock:
            rid = self._next_id()
            self._send(method, params, req_id=rid)
            while True:
                msg = self._recv(timeout)
                # Skip notifications (no id field)
                if "id" not in msg:
                    continue
                if msg["id"] != rid:
                    continue
                if "error" in msg:
                    raise RuntimeError(f"MCP error: {msg['error']}")
                return msg.get("result")

    # ── MCP lifecycle ─────────────────────────────────────────────────────────

    def initialize(self) -> None:
        if self._initialized:
            return
        params = {
            "protocolVersion": self.MCP_VERSION,
            "capabilities": {"roots": {"listChanged": False}},
            "clientInfo": {"name": "seeker-agent", "version": "1.0.0"},
        }
        self._request("initialize", params)
        # Send initialized notification (required by MCP spec)
        self._send("notifications/initialized")
        self._initialized = True

    # ── Tool operations ────────────────────────────────────────────────────────

    def list_tools(self) -> List[Dict[str, Any]]:
        result = self._request("tools/list")
        return result.get("tools", [])

    def call_tool(self, name: str, arguments: Dict[str, Any],
                  timeout: float = 120.0) -> str:
        result = self._request(
            "tools/call",
            {"name": name, "arguments": arguments},
            timeout=timeout,
        )
        parts: List[str] = []
        for block in result.get("content", []):
            if block.get("type") == "text":
                parts.append(block["text"])
            else:
                parts.append(str(block))
        return "\n".join(parts) if parts else "(no output)"

    # ── Cleanup ───────────────────────────────────────────────────────────────

    def close(self) -> None:
        try:
            self._proc.stdin.close()
        except Exception:
            pass
        try:
            self._proc.stderr.close()
        except Exception:
            pass
        try:
            self._proc.terminate()
            self._proc.wait(timeout=3)
        except Exception:
            pass

    def __enter__(self):
        self.initialize()
        return self

    def __exit__(self, *_):
        self.close()


# ─────────────────────────────────────────────────────────────────────────────
# Dynamic BaseTool wrapper — one per MCP tool per server
# ─────────────────────────────────────────────────────────────────────────────

class MCPToolWrapper(BaseTool):
    """Proxies a single tool from a remote MCP server as a Seeker BaseTool."""

    # Set via dynamic subclass (required by BaseTool)
    name: str = ""
    description: str = ""

    def __init__(
        self,
        server_name: str,
        server_config: Dict[str, Any],
        tool_name: str,
        tool_description: str,
        tool_input_schema: Dict[str, Any],
    ):
        self._server_name = server_name
        self._server_config = server_config
        self._tool_name = tool_name          # raw upstream name (no prefix)
        self._input_schema = tool_input_schema
        super().__init__()

    # ── Schema ────────────────────────────────────────────────────────────────

    def get_schema(self) -> Dict[str, Any]:
        props = self._input_schema.get("properties", {})
        required = self._input_schema.get("required", [])
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": props,
                    "required": required,
                },
            },
        }

    # ── Execution ─────────────────────────────────────────────────────────────

    def execute(self, **kwargs) -> str:
        cfg = self._server_config
        env = cfg.get("env") or {}
        try:
            with _MCPSession(cfg["command"], cfg.get("args", []), env) as sess:
                return sess.call_tool(self._tool_name, kwargs)
        except Exception as exc:
            return f"[MCP:{self._server_name}] Error calling '{self._tool_name}': {exc}"


# ─────────────────────────────────────────────────────────────────────────────
# Discovery
# ─────────────────────────────────────────────────────────────────────────────

def _discover_server_tools(
    server_name: str,
    server_config: Dict[str, Any],
) -> List[MCPToolWrapper]:
    """Spawn the server, list its tools, return wrappers."""
    env = server_config.get("env") or {}
    wrappers: List[MCPToolWrapper] = []
    try:
        with _MCPSession(server_config["command"], server_config.get("args", []), env) as sess:
            tools = sess.list_tools()

        for tool in tools:
            tool_name: str = tool["name"]
            desc: str = tool.get("description") or f"MCP tool '{tool_name}' from {server_name}"
            schema: Dict = tool.get("inputSchema") or {}

            # Prefix to avoid name collisions between servers
            seeker_name = f"mcp_{server_name.lower()}_{tool_name}"

            # Unique subclass so BaseTool sees name/description as class attrs
            wrapper_cls = type(
                f"MCP_{server_name}_{tool_name}",
                (MCPToolWrapper,),
                {"name": seeker_name, "description": desc},
            )
            instance = wrapper_cls(
                server_name=server_name,
                server_config=server_config,
                tool_name=tool_name,
                tool_description=desc,
                tool_input_schema=schema,
            )
            wrappers.append(instance)
            print(f"   ↳ [{server_name}] {tool_name} → {seeker_name}")

    except Exception as exc:
        print(f"   ✗ Could not connect to MCP server '{server_name}': {exc}")

    return wrappers


def discover_mcp_tools() -> List[MCPToolWrapper]:
    """
    Called by ToolRegistry.auto_discover_tools().

    Reads config/mcp_servers.json and returns all tool wrappers from
    all enabled servers, ready to register with Seeker.
    """
    servers = _load_mcp_config()
    if not servers:
        return []

    all_tools: List[MCPToolWrapper] = []
    for server_name, server_cfg in servers.items():
        if not server_cfg.get("enabled", True):
            print(f"   ⊘ Skipping disabled MCP server: {server_name}")
            continue

        print(f"   🔌 Connecting to MCP server: {server_name}")
        found = _discover_server_tools(server_name, server_cfg)
        all_tools.extend(found)

    return all_tools
