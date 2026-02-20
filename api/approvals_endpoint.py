
"""WebSocket endpoint for pending tool approvals."""
import asyncio
import subprocess
from fastapi import WebSocket, WebSocketDisconnect
from core.tool_queue import tool_queue


async def setup_approval_websocket(app, websocket_clients):
    """Setup approval WebSocket endpoint on the FastAPI app."""
    
    @app.websocket("/ws/approvals")
    async def approval_websocket(websocket: WebSocket):
        """WebSocket endpoint for real-time pending tool notifications and approvals."""
        await websocket.accept()
        websocket_clients.add(websocket)
        
        print(f"🔌 Approval WebSocket connected (total: {len(websocket_clients)})")
        
        try:
            # Send current pending tools on connection
            pending = tool_queue.get_pending()
            if pending:
                await websocket.send_json({
                    "type": "pending_tools",
                    "data": pending
                })
            
            # Listen for approve/deny messages
            while True:
                data = await websocket.receive_json()
                
                if data.get("type") == "approve":
                    tool_id = data.get("tool_id")
                    user_response = data.get("user_response")
                    
                    if tool_queue.approve_tool(tool_id, user_response):
                        # Execute the approved tool
                        await execute_approved_tool(tool_id)
                        
                        # Notify all clients
                        await broadcast_tool_update(tool_id, "approved", websocket_clients)
                        
                        await websocket.send_json({
                            "type": "ack",
                            "success": True,
                            "tool_id": tool_id
                        })
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Failed to approve tool"
                        })
                
                elif data.get("type") == "deny":
                    tool_id = data.get("tool_id")
                    reason = data.get("reason", "User denied")
                    
                    if tool_queue.deny_tool(tool_id, reason):
                        await broadcast_tool_update(tool_id, "denied", websocket_clients)
                        
                        await websocket.send_json({
                            "type": "ack",
                            "success": True,
                            "tool_id": tool_id
                        })
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Failed to deny tool"
                        })
                    
        except WebSocketDisconnect:
            websocket_clients.remove(websocket)
            print(f"🔌 Approval WebSocket disconnected (total: {len(websocket_clients)})")
        except Exception as e:
            print(f"⚠️ Approval WebSocket error: {e}")
            if websocket in websocket_clients:
                websocket_clients.remove(websocket)


async def execute_approved_tool(tool_id: str):
    """Execute an approved tool and store the result."""
    import subprocess
    
    tool = tool_queue.get_tool(tool_id)
    if not tool or tool.status != 'approved':
        return
    
    try:
        if tool.tool_name == "execute_command":
            command = tool.args.get("command")
            
            print(f"🔧 Executing approved command: {command}")
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                output = result.stdout if result.stdout else "✅ Command completed successfully (no output)"
                tool_queue.set_result(tool_id, output)
                
                # Add to pending results list - will be injected into next prompt
                from core.pending_results import pending_tool_results
                pending_tool_results.add_result(tool_id, tool.tool_name, tool.args, output)
                
                print(f"✅ Result added to pending results queue")
            else:
                error = f"❌ Command failed with error:\n{result.stderr}"
                tool_queue.set_result(tool_id, None, error)
        
        else:
            tool_queue.set_result(tool_id, None, "Unknown tool type")
            
    except subprocess.TimeoutExpired:
        tool_queue.set_result(tool_id, None, "⏱️ Command timed out after 30 seconds")
    except Exception as e:
        tool_queue.set_result(tool_id, None, f"❌ Error executing tool: {e}")


async def broadcast_tool_update(tool_id: str, status: str, websocket_clients):
    """Broadcast tool status update to all connected clients."""
    if not websocket_clients:
        return
    
    tool = tool_queue.get_tool(tool_id)
    if not tool:
        return
    
    message = {
        "type": "tool_update",
        "data": tool.to_dict()
    }
    
    disconnected = set()
    for client in websocket_clients:
        try:
            await client.send_json(message)
        except Exception:
            disconnected.add(client)
    
    for client in disconnected:
        websocket_clients.remove(client)


async def broadcast_new_pending_tool(tool_data: dict, websocket_clients):
    """Broadcast new pending tool to all connected clients."""
    if not websocket_clients:
        print(f"⚠️ No WebSocket clients connected to broadcast to")
        return
    
    message = {
        "type": "new_pending_tool",
        "data": tool_data
    }
    
    print(f"📡 Broadcasting new pending tool to {len(websocket_clients)} client(s)")
    
    disconnected = set()
    sent_count = 0
    for client in websocket_clients:
        try:
            await client.send_json(message)
            sent_count += 1
        except Exception as e:
            print(f"   ❌ Failed to send to client: {e}")
            disconnected.add(client)
    
    for client in disconnected:
        websocket_clients.remove(client)
    
    print(f"📡 Broadcast complete: {sent_count}/{len(websocket_clients) + len(disconnected)} successful")


# Set the broadcast callback with sync/async bridge
def sync_broadcast_pending_tool(tool_data: dict):
    """Bridge function to call async broadcast from sync tool_queue."""
    # Import here to avoid circular dependency
    from api.server import websocket_clients
    
    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            print("⚠️ No running event loop for WebSocket broadcast")
            return
        
        def schedule_broadcast():
            asyncio.ensure_future(broadcast_new_pending_tool(tool_data, websocket_clients), loop=loop)
        
        loop.call_soon_threadsafe(schedule_broadcast)
        print(f"✅ Scheduled WebSocket broadcast for pending tool {tool_data.get('id', 'unknown')[:8]}")
        
    except Exception as e:
        print(f"⚠️ Error scheduling WebSocket broadcast: {e}")
        import traceback
        traceback.print_exc()


# Set the callback on tool_queue
tool_queue.on_new_pending = sync_broadcast_pending_tool

