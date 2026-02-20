"""Session logging system for capturing raw prompts and responses."""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional


class SessionLogger:
    """Logs raw prompts and responses for each agent session."""
    
    def __init__(self, session_dir: Path, model_name: str, config: Dict[str, Any]):
        """
        Initialize a new session logger.
        
        Args:
            session_dir: Directory to save session logs
            model_name: Name of the LLM model being used
            config: Agent configuration dictionary
        """
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Session metadata
        self.session_id = str(uuid.uuid4())
        self.start_time = datetime.now()
        self.model_name = model_name
        self.config = config
        
        # Interaction tracking
        self.interactions: List[Dict[str, Any]] = []
        self.interaction_counter = 0
        
        # Session file path
        timestamp = self.start_time.strftime('%Y%m%d_%H%M%S')
        self.session_file = self.session_dir / f"session_{timestamp}.json"
        
        print(f"📝 Session logging started: {self.session_file.name}")
    
    def log_interaction(
        self,
        user_input: str,
        raw_prompt: str,
        raw_response: Any,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        tool_results: Optional[List[Dict[str, Any]]] = None
    ):
        """
        Log a single interaction (prompt + response).
        
        Args:
            user_input: Original user message
            raw_prompt: Complete system prompt sent to LLM
            raw_response: Raw LLM response object
            tool_calls: List of tool calls made (if any)
            tool_results: List of tool execution results (if any)
        """
        self.interaction_counter += 1
        
        # Convert response to serializable format
        response_data = self._serialize_response(raw_response)
        
        interaction = {
            'interaction_id': self.interaction_counter,
            'timestamp': datetime.now().isoformat(),
            'user_input': user_input,
            'raw_prompt': raw_prompt,
            'raw_response': response_data,
            'tool_calls': tool_calls or [],
            'tool_results': tool_results or []
        }
        
        self.interactions.append(interaction)
        
        # Auto-save after each interaction
        self.save_session()
    
    def _serialize_response(self, response: Any) -> Dict[str, Any]:
        """
        Convert LLM response object to JSON-serializable format.
        
        Args:
            response: Raw response object from LLM
            
        Returns:
            Dictionary representation of response
        """
        try:
            # Handle different response types
            if hasattr(response, '__dict__'):
                # Object with attributes
                result = {}
                for key, value in response.__dict__.items():
                    if not key.startswith('_'):
                        result[key] = self._serialize_value(value)
                return result
            elif isinstance(response, (dict, list, str, int, float, bool, type(None))):
                # Already serializable
                return response
            else:
                # Fallback to string representation
                return {'_raw': str(response)}
        except Exception as e:
            return {'_error': f'Serialization failed: {str(e)}', '_raw': str(response)}
    
    def _serialize_value(self, value: Any) -> Any:
        """Recursively serialize nested values."""
        if isinstance(value, (str, int, float, bool, type(None))):
            return value
        elif isinstance(value, (list, tuple)):
            return [self._serialize_value(v) for v in value]
        elif isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        elif hasattr(value, '__dict__'):
            return self._serialize_response(value)
        else:
            return str(value)
    
    def save_session(self):
        """Save current session data to JSON file."""
        session_data = {
            'session_id': self.session_id,
            'start_time': self.start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'model': self.model_name,
            'config': self.config,
            'total_interactions': self.interaction_counter,
            'interactions': self.interactions
        }
        
        try:
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️  Failed to save session log: {e}")
    
    def get_session_data(self) -> Dict[str, Any]:
        """
        Get current session data.
        
        Returns:
            Dictionary containing session metadata and interactions
        """
        return {
            'session_id': self.session_id,
            'start_time': self.start_time.isoformat(),
            'model': self.model_name,
            'total_interactions': self.interaction_counter,
            'session_file': str(self.session_file)
        }
    
    def close_session(self):
        """Finalize and save the session."""
        self.save_session()
        print(f"💾 Session log saved: {self.session_file}")
        print(f"   Total interactions: {self.interaction_counter}")
    
    def __repr__(self):
        return (
            f"SessionLogger(session_id={self.session_id[:8]}..., "
            f"interactions={self.interaction_counter})"
        )
