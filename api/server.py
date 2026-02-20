"""FastAPI server for Seeker agent web interface."""
import sys
from pathlib import Path
from typing import Dict, Any, Set
from datetime import datetime
import asyncio
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

from api.models import (
    ChatRequest, ChatResponse, ToolCall, ToolInfo, ToolsResponse,
    MemoryResponse, MemoryEntry, SessionsResponse, SessionInfo, StatusResponse,
    InputRequestInfo, InputRequestsResponse, InputResponseRequest
)
from core.agent import SeekerAgent
from core.input_manager import input_manager
from core.tool_queue import tool_queue
from config.settings import Settings


# Initialize FastAPI app
app = FastAPI(
    title="Seeker Agent API",
    description="Web interface for Seeker AI Agent",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket clients tracking
websocket_clients: Set[WebSocket] = set()

# Active agent sessions
active_sessions: Dict[str, SeekerAgent] = {}

# Import and setup approvals endpoint
from api.approvals_endpoint import setup_approval_websocket, sync_broadcast_pending_tool
tool_queue.on_new_pending = sync_broadcast_pending_tool


# Global agent instance
agent: SeekerAgent = None


def get_or_create_agent(session_id: str = None) -> SeekerAgent:
    """Get existing agent or create new one."""
    global agent, active_sessions
    
    if session_id and session_id in active_sessions:
        return active_sessions[session_id]
    
    if agent is None:
        agent = SeekerAgent()
    
    if session_id:
        active_sessions[session_id] = agent
    
    return agent


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    print("🚀 Starting Seeker Agent API Server...")
    print("🔍 Discovering tools...")
    
    # Setup approvals WebSocket endpoint
    await setup_approval_websocket(app, websocket_clients)
    print("✅ Approvals WebSocket endpoint ready")
    print("✅ Agent initialized and ready!")


@app.get("/")
async def root():
    """Serve the main web interface."""
    web_dir = Path(__file__).parent.parent / "web"
    index_file = web_dir / "index.html"
    
    if index_file.exists():
        return FileResponse(index_file)
    else:
        return HTMLResponse(content="<h1>Seeker Agent API</h1><p>Web interface not found. Please check web/ directory.</p>")


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a chat message from the user.
    
    Args:
        request: ChatRequest with message and optional session_id
        
    Returns:
        ChatResponse with agent's response and tool calls
    """
    try:
        # Get or create agent for this session
        current_agent = get_or_create_agent(request.session_id)
        
        # Process the task
        result = current_agent.process_task(request.message)
        
        # Extract tool calls
        tool_calls = []
        if result.get('tool_results'):
            # Get tool call data from session logger if available
            if hasattr(current_agent, 'session_logger') and current_agent.session_logger.interactions:
                last_interaction = current_agent.session_logger.interactions[-1]
                for tool_data in last_interaction.get('tool_calls', []):
                    print(tool_data)
                    tool_calls.append(ToolCall(
                        tool=tool_data['tool'],
                        args=tool_data.get('args', {}),
                        result=tool_data.get('result', '')
                    ))
        
        # Get session ID
        session_id = request.session_id or current_agent.session_logger.session_id
        
        # Extract response text
        response_text = ""
        if result.get('response'):
            resp = result['response']
            if hasattr(resp, 'message') and hasattr(resp.message, 'content'):
                response_text = resp.message.content or ""
        
        return ChatResponse(
            response=response_text,
            tool_calls=tool_calls,
            agent_thought=result.get('agent_thought', ''),
            session_id=session_id,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        print(f"❌ Error in chat endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tools", response_model=ToolsResponse)
async def get_tools():
    """
    Get list of available tools.
    
    Returns:
        ToolsResponse with list of all available tools
    """
    try:
        current_agent = get_or_create_agent()
        tools = []
        
        for tool_name in current_agent.tool_registry.get_tool_names():
            tool = current_agent.tool_registry.get_tool(tool_name)
            tools.append(ToolInfo(
                name=tool.name,
                description=tool.description,
                parameters=tool.parameters
            ))
        
        return ToolsResponse(tools=tools)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/memory", response_model=MemoryResponse)
async def get_memory():
    """
    Get current memory status.
    
    Returns:
        MemoryResponse with memory statistics and recent entries
    """
    try:
        current_agent = get_or_create_agent()
        
        # Get recent memory entries
        recent = current_agent.memory.get_recent_memory(20)
        entries = []
        
        for entry in recent:
            entries.append(MemoryEntry(
                type=entry.get('type', 'unknown'),
                timestamp=entry.get('timestamp', ''),
                content=entry.get('content'),
                tool_name=entry.get('tool_name'),
                result=entry.get('result', '')[:200] if entry.get('result') else None
            ))
        
        return MemoryResponse(
            memory_count=len(current_agent.memory.memory),
            history_count=len(current_agent.memory.history),
            recent_entries=entries,
            summaries=current_agent.memory.summaries
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/memory/clear", response_model=StatusResponse)
async def clear_memory():
    """Clear agent's memory."""
    try:
        current_agent = get_or_create_agent()
        current_agent.memory.memory.clear()
        current_agent.memory.history.clear()
        
        return StatusResponse(
            status="success",
            message="Memory cleared successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/memory/summarize", response_model=StatusResponse)
async def summarize_memory():
    """Summarize agent's memory."""
    try:
        current_agent = get_or_create_agent()
        summary = current_agent._summarize_memory(save_to_file=True)
        
        return StatusResponse(
            status="success",
            message=f"Memory summarized: {summary[:100]}..."
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/input/pending", response_model=InputRequestsResponse)
async def get_pending_inputs():
    """
    Get all pending input requests.
    
    Returns:
        InputRequestsResponse with list of pending requests
    """
    try:
        pending = input_manager.get_pending_requests()
        requests = [
            InputRequestInfo(
                id=req['id'],
                prompt=req['prompt'],
                timestamp=req['timestamp']
            )
            for req in pending
        ]
        
        return InputRequestsResponse(requests=requests)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/input/respond", response_model=StatusResponse)
async def respond_to_input(request: InputResponseRequest):
    """
    Submit a response to a pending input request.
    
    Args:
        request: InputResponseRequest with request_id and response
        
    Returns:
        StatusResponse indicating success or failure
    """
    try:
        success = input_manager.submit_response(
            request.request_id,
            request.response,
            source="web"
        )
        
        if success:
            return StatusResponse(
                status="success",
                message="Response submitted successfully"
            )
        else:
            return StatusResponse(
                status="error",
                message="Request not found or already answered"
            )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/input")
async def websocket_input_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time input request notifications."""
    await websocket.accept()
    websocket_clients.add(websocket)
    
    print(f"🔌 WebSocket client connected (total: {len(websocket_clients)})")
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "response":
                success = input_manager.submit_response(
                    data["request_id"],
                    data["response"],
                    source="web"
                )
                
                await websocket.send_json({
                    "type": "ack",
                    "success": success
                })
                
    except WebSocketDisconnect:
        websocket_clients.remove(websocket)
        print(f"🔌 WebSocket disconnected (total: {len(websocket_clients)})")
    except Exception as e:
        print(f"⚠️ WebSocket error: {e}")
        if websocket in websocket_clients:
            websocket_clients.remove(websocket)


async def broadcast_input_request(request_data: dict):
    """Broadcast input request to all connected WebSocket clients."""
    if not websocket_clients:
        print(f"⚠️ No WebSocket clients connected to broadcast to")
        return
    
    message = {
        "type": "input_request",
        "data": request_data
    }
    
    print(f"📡 Broadcasting to {len(websocket_clients)} WebSocket client(s)")
    print(f"   Message: {message}")
    
    disconnected = set()
    sent_count = 0
    for client in websocket_clients:
        try:
            await client.send_json(message)
            sent_count += 1
            print(f"   ✅ Sent to client")
        except Exception as e:
            print(f"   ❌ Failed to send to client: {e}")
            disconnected.add(client)
    
    for client in disconnected:
        websocket_clients.remove(client)
    
    print(f"📡 Broadcast complete: {sent_count}/{len(websocket_clients) + len(disconnected)} successful")


# Set the broadcast callback with sync/async bridge
def sync_broadcast_input(request_data: dict):
    """
    Bridge function to call async broadcast from sync InputManager.
    
    This uses call_soon_threadsafe to schedule the coroutine on the event loop
    from a synchronous context (potentially different thread).
    """
    try:
        # Get the running event loop
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            print("⚠️ No running event loop for WebSocket broadcast")
            return
        
        # Create a wrapper to schedule the coroutine
        def schedule_broadcast():
            asyncio.ensure_future(broadcast_input_request(request_data), loop=loop)
        
        # Schedule it on the event loop thread-safely
        loop.call_soon_threadsafe(schedule_broadcast)
        print(f"✅ Scheduled WebSocket broadcast for request {request_data.get('id', 'unknown')[:8]}")
        
    except Exception as e:
        print(f"⚠️ Error scheduling WebSocket broadcast: {e}")
        import traceback
        traceback.print_exc()


# Set the callback on input_manager
input_manager.on_new_request = sync_broadcast_input


@app.get("/api/sessions", response_model=SessionsResponse)
async def get_sessions():
    """Get list of active sessions."""
    try:
        sessions = []
        
        for session_id, session_agent in active_sessions.items():
            sessions.append(SessionInfo(
                session_id=session_id,
                start_time=session_agent.session_logger.start_time,
                interaction_count=len(session_agent.session_logger.interactions)
            ))
        
        return SessionsResponse(sessions=sessions)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint for real-time chat.
    
    Allows bidirectional communication for streaming responses.
    """
    await websocket.accept()
    session_id = f"ws_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Get agent for this session
            current_agent = get_or_create_agent(session_id)
            
            # Send acknowledgment
            await websocket.send_json({
                "type": "processing",
                "message": "Processing your request..."
            })
            
            # Process task
            result = current_agent.process_task(message_data.get('message', ''))
            
            # Send response
            response_text = ""
            if result.get('response'):
                resp = result['response']
                if hasattr(resp, 'message') and hasattr(resp.message, 'content'):
                    response_text = resp.message.content or ""
            
            await websocket.send_json({
                "type": "response",
                "response": response_text,
                "agent_thought": result.get('agent_thought', ''),
                "tool_calls": len(result.get('tool_results', [])),
                "timestamp": datetime.now().isoformat()
            })
            
    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })


# Mount static files (CSS, JS)
web_dir = Path(__file__).parent.parent / "web"
if web_dir.exists():
    app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")


if __name__ == "__main__":
    import uvicorn
    print("=" * 70)
    print("🌐 Starting Seeker Agent Web Server")
    print("=" * 70)
    print("📍 Server will be available at: http://localhost:8000")
    print("📍 API docs at: http://localhost:8000/docs")
    print("=" * 70)
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
