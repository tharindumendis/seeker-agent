"""Conversation history tracking for ReAct-style prompting."""
from typing import List, Dict, Any, Optional
from datetime import datetime


class ConversationTurn:
    """Represents a single turn in the conversation."""
    
    def __init__(self):
        self.turn_number: int = 0
        self.timestamp: str = datetime.now().isoformat()
        self.user_input: Optional[str] = None
        self.agent_thought: Optional[str] = None  # Agent's reasoning before action
        self.tool_calls: List[Dict[str, Any]] = []  # List of {tool, args, result}
        self.agent_response: Optional[str] = None  # Final response (if any)
    
    def add_tool_call(self, tool_name: str, args: Dict[str, Any], result: Any):
        """Add a tool call to this turn."""
        self.tool_calls.append({
            'tool': tool_name,
            'args': args,
            'result': str(result)[:2000]  # Increased from 500 to 2000
        })
    
    def format_for_prompt(self) -> str:
        """Format this turn for inclusion in prompt."""
        lines = []
        lines.append(f"Turn {self.turn_number}:")
        
        if self.user_input:
            lines.append(f"  User: {self.user_input}")
        
        if self.agent_thought:
            lines.append(f"  Agent Thought: {self.agent_thought}")
        
        for tool_call in self.tool_calls:
            tool = tool_call['tool']
            args = tool_call['args']
            result = tool_call['result']
            
            # Format args nicely
            if args:
                args_str = ', '.join([f"{k}={v}" for k, v in args.items()])
                lines.append(f"  Action: {tool}({args_str})")
            else:
                lines.append(f"  Action: {tool}()")
            
            lines.append(f"  Observation: {result}")
        
        if self.agent_response:
            lines.append(f"  Agent: {self.agent_response}")
        
        return "\n".join(lines)


class ConversationHistory:
    """Manages conversation history with ReAct-style formatting."""
    
    def __init__(self, max_turns: int = 7):
        self.turns: List[ConversationTurn] = []
        self.max_turns = max_turns
        self.current_turn: Optional[ConversationTurn] = None
        self.turn_counter = 0
    
    def start_turn(self, user_input: Optional[str] = None) -> ConversationTurn:
        """Start a new conversation turn."""
        self.turn_counter += 1
        self.current_turn = ConversationTurn()
        self.current_turn.turn_number = self.turn_counter
        self.current_turn.user_input = user_input
        return self.current_turn
    
    def end_turn(self):
        """End the current turn and add it to history."""
        if self.current_turn:
            self.turns.append(self.current_turn)
            
            # Keep only last N turns
            if len(self.turns) > self.max_turns:
                self.turns.pop(0)
            
            self.current_turn = None
    
    def add_agent_thought(self, thought: str):
        """Add agent's reasoning to current turn."""
        if self.current_turn:
            self.current_turn.agent_thought = thought
    
    def add_tool_call(self, tool_name: str, args: Dict[str, Any], result: Any):
        """Add a tool call to current turn."""
        if self.current_turn:
            self.current_turn.add_tool_call(tool_name, args, result)
    
    def add_agent_response(self, response: str):
        """Add agent's final response to current turn."""
        if self.current_turn:
            self.current_turn.agent_response = response
    
    def format_for_prompt(self) -> str:
        """Format conversation history for prompt."""
        if not self.turns:
            return "No previous conversation."
        
        formatted_turns = [turn.format_for_prompt() for turn in self.turns]
        return "\n\n".join(formatted_turns)
    
    def get_last_n_turns(self, n: int) -> List[ConversationTurn]:
        """Get the last N turns."""
        return self.turns[-n:] if self.turns else []
    
    def get_tool_summary(self) -> str:
        """Get a summary of all tools used."""
        tool_calls = []
        for turn in self.turns:
            for tc in turn.tool_calls:
                tool_calls.append(f"{tc['tool']}({', '.join([f'{k}={v}' for k, v in tc['args'].items()])})")
        
        if not tool_calls:
            return "No tools used yet."
        
        return "Tools used: " + ", ".join(tool_calls[-10:])  # Last 10 tool calls
    
    def clear(self):
        """Clear all conversation history."""
        self.turns = []
        self.current_turn = None
        self.turn_counter = 0
