"""Input Manager for unified terminal and web input handling."""
import threading
import time
import uuid
from typing import Optional, Dict, List
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class InputRequest:
    """Represents a pending input request."""
    id: str
    prompt: str
    timestamp: float
    response: Optional[str] = None
    source: Optional[str] = None  # 'terminal' or 'web'
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'prompt': self.prompt,
            'timestamp': self.timestamp,
            'response': self.response,
            'source': self.source
        }


class InputManager:
    """
    Manages user input requests from multiple sources (terminal, web).
    Whichever source responds first wins.
    """
    
    def __init__(self):
        self.pending_requests: Dict[str, InputRequest] = {}
        self.lock = threading.Lock()
        self.cleanup_interval = 60  # Clean up old requests every 60 seconds
        self._start_cleanup_thread()
    
    def request_input(self, prompt: str, timeout: int = 300) -> str:
        """
        Request input from web interface only.
        
        NOTE: Terminal input() is disabled because it blocks the web server.
        Use the web interface to respond to input requests.
        
        Args:
            prompt: The prompt to show the user
            timeout: Maximum seconds to wait (default 5 minutes)
            
        Returns:
            User's response string, or "no input" if timeout
        """
        # Create request
        request = InputRequest(
            id=str(uuid.uuid4()),
            prompt=prompt,
            timestamp=time.time()
        )
        
        # Add to pending requests
        with self.lock:
            self.pending_requests[request.id] = request
        
        print(f"\n🔔 Input requested: {prompt}")
        print(f"   Request ID: {request.id[:8]}...")
        print(f"   ⚠️  Please respond via WEB INTERFACE at http://localhost:8000")
        print(f"   (Terminal input disabled to prevent server blocking)")
        
        # Notify callback (e.g., WebSocket broadcast)
        if hasattr(self, 'on_new_request') and self.on_new_request:
            try:
                result = self.on_new_request(request.to_dict())
                # If the callback returns a coroutine, we can't await it here (sync context)
                # The callback itself should handle scheduling it on the event loop
                if hasattr(result, '__await__'):
                    print("⚠️ Callback returned coroutine - ensure callback handles async scheduling")
            except Exception as e:
                print(f"⚠️ Failed to notify WebSocket clients: {e}")
        
        # Wait for web response only
        start_time = time.time()
        while time.time() - start_time < timeout:
            with self.lock:
                if request.response is not None:
                    response = request.response
                    source = request.source
                    del self.pending_requests[request.id]
                    print(f"   ✅ Response from {source}: {response}")
                    return response
            time.sleep(0.1)  # Non-blocking sleep
        
        # Timeout - return default
        print(f"   ⏱️ No response after {timeout}s - using default 'no'")
        with self.lock:
            if request.id in self.pending_requests:
                del self.pending_requests[request.id]
        return "no input"
    
    def _try_terminal_input(self, request: InputRequest, timeout: int) -> Optional[str]:
        """
        DEPRECATED: Terminal input disabled to prevent server blocking.
        """
        return None
    
    def _wait_for_web_input(self, request: InputRequest, timeout: int) -> Optional[str]:
        """
        DEPRECATED: Web input handled in main request_input loop.
        """
        return None
    
    def submit_response(self, request_id: str, response: str, source: str = "unknown") -> bool:
        """
        Submit a response to a pending input request.
        
        Args:
            request_id: ID of the request to respond to
            response: The user's response
            source: Source of response ('terminal' or 'web')
            
        Returns:
            True if response was accepted, False if request not found or already answered
        """
        with self.lock:
            if request_id not in self.pending_requests:
                return False
            
            request = self.pending_requests[request_id]
            
            # Check if already answered
            if request.response is not None:
                return False
            
            # Set response
            request.response = response
            request.source = source
            return True
    
    def get_pending_requests(self) -> List[Dict]:
        """
        Get all pending input requests.
        
        Returns:
            List of pending requests as dictionaries
        """
        with self.lock:
            return [req.to_dict() for req in self.pending_requests.values()]
    
    def _cleanup_old_requests(self):
        """Remove requests older than 10 minutes."""
        current_time = time.time()
        max_age = 600  # 10 minutes
        
        with self.lock:
            expired_ids = [
                req_id for req_id, req in self.pending_requests.items()
                if current_time - req.timestamp > max_age
            ]
            
            for req_id in expired_ids:
                print(f"   🗑️ Cleaning up expired request: {req_id[:8]}...")
                del self.pending_requests[req_id]
    
    def _start_cleanup_thread(self):
        """Start background thread to clean up old requests."""
        def cleanup_loop():
            while True:
                time.sleep(self.cleanup_interval)
                self._cleanup_old_requests()
        
        cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        cleanup_thread.start()


# Global instance
input_manager = InputManager()


def get_user_input(prompt: str, timeout: int = 300) -> str:
    """
    Get user input from terminal or web interface.
    Whichever responds first wins.
    
    This is the main function to use in tools and agent code.
    
    Args:
        prompt: The prompt to show user
        timeout: Max seconds to wait (default 5 minutes)
        
    Returns:
        User's response string
        
    Raises:
        TimeoutError: If no response within timeout
        
    Example:
        >>> response = get_user_input("Do you want to proceed? (y/n)")
        >>> if response.lower() == 'y':
        >>>     # proceed
    """
    return input_manager.request_input(prompt, timeout)
