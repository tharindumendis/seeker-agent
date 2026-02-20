"""Pydantic models for API requests and responses."""
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str
    session_id: Optional[str] = None


class ToolCall(BaseModel):
    """Model for tool execution information."""
    tool: str
    args: Dict[str, Any]
    result: Any


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str
    tool_calls: List[ToolCall] = []
    agent_thought: Optional[str] = None
    session_id: str
    timestamp: str


class ToolInfo(BaseModel):
    """Model for tool information."""
    name: str
    description: str
    parameters: Dict[str, Any]


class ToolsResponse(BaseModel):
    """Response model for tools endpoint."""
    tools: List[ToolInfo]


class MemoryEntry(BaseModel):
    """Model for memory entry."""
    type: str
    timestamp: str
    content: Optional[str] = None
    tool_name: Optional[str] = None
    result: Optional[str] = None


class MemoryResponse(BaseModel):
    """Response model for memory endpoint."""
    memory_count: int
    history_count: int
    recent_entries: List[MemoryEntry]
    summaries: List[Dict[str, Any]]


class SessionInfo(BaseModel):
    """Model for session information."""
    session_id: str
    start_time: str
    interaction_count: int


class SessionsResponse(BaseModel):
    """Response model for sessions endpoint."""
    sessions: List[SessionInfo]


class StatusResponse(BaseModel):
    """Generic status response."""
    status: str
    message: str


class InputRequestInfo(BaseModel):
    """Model for input request information."""
    id: str
    prompt: str
    timestamp: float


class InputRequestsResponse(BaseModel):
    """Response model for pending input requests."""
    requests: List[InputRequestInfo]


class InputResponseRequest(BaseModel):
    """Request model for submitting input response."""
    request_id: str
    response: str
