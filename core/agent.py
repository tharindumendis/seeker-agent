"""Main Seeker agent implementation."""
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.llm_client import LLMClient
from core.memory import MemoryManager
from core.insight_loader import InsightLoader
from core.session_logger import SessionLogger
from core.conversation import ConversationHistory
from plugins.registry import ToolRegistry
from config.settings import Settings


class SeekerAgent:
    """
    Main Seeker agent class.
    
    Coordinates between LLM, tools, and memory to process user tasks.
    """
    
    def __init__(self, config: Optional[Settings] = None):
        """
        Initialize the Seeker agent.
        
        Args:
            config: Optional settings object. If None, uses default settings.
        """
        # Load configuration
        self.config = config or Settings()
        
        # Initialize components
        self.llm_client = LLMClient(
            model_name=self.config.model_name,
            temperature=self.config.temperature,
            max_retries=self.config.max_retries
        )
        
        self.memory = MemoryManager(
            memory_limit=self.config.memory_limit,
            history_limit=self.config.history_limit
        )
        
        self.tool_registry = ToolRegistry()
        
        # Auto-discover and register tools
        print("🔍 Discovering tools...")
        self.tool_registry.auto_discover_tools()
        print(f"✓ Loaded {len(self.tool_registry.get_tool_names())} tools\n")
        
        # Load agent insights
        insight_dir = self.config.project_root / "Agent_Insight"
        self.insight_loader = InsightLoader(insight_dir)
        print("📚 Loading agent insights...")
        self.insight_loader.load_insights()
        if self.insight_loader.insights:
            print(f"✓ Loaded {len(self.insight_loader.list_insights())} insight file(s)\n")
        else:
            print("⚠️  No insights found\n")
        
        # Initialize session logger
        self.session_logger = SessionLogger(
            session_dir=self.config.sessions_dir,
            model_name=self.config.model_name,
            config={
                'temperature': self.config.temperature,
                'memory_limit': self.config.memory_limit,
                'history_limit': self.config.history_limit
            }
        )
        
        # Initialize conversation history for ReAct-style prompting
        self.conversation = ConversationHistory(max_turns=7)
        print("💬 Conversation tracking initialized\n")
    
    def process_task(self, user_input: str) -> Dict[str, Any]:
        """
        Process a user task.
        
        Args:
            user_input: The task description from the user
            
        Returns:
            Dict containing response and metadata
        """
        try:
            # Start a new conversation turn
            turn = self.conversation.start_turn(user_input)
            
            # Build prompt with conversation history
            prompt = self._build_prompt(user_input)
            
            # Get tool schemas for LLM
            tool_schemas = self.tool_registry.get_tool_schemas()
            
            # Get LLM response using chat() method
            print(f"\n🤔 Processing: {user_input[:100]}...")
            response = self.llm_client.chat(
                prompt=prompt,
                tools=tool_schemas,
                expect_json=False
            )
            
            # Extract agent's thought/reasoning from response content
            agent_thought = response.message.content if hasattr(response, 'message') and hasattr(response.message, 'content') else ''
            if agent_thought:
                self.conversation.add_agent_thought(agent_thought)
                print(f"\n💭 Agent: {agent_thought[:150]}...")
            
            # Check if this is a "no message" input - skip memory storage if so
            is_no_message = user_input.lower().strip() in ['no message', '']
            
            # Store user input in memory ONLY if it's not "no message"
            if not is_no_message:
                self.memory.add_history({
                    'type': 'user_input',
                    'content': user_input
                })
            else:
                print(f"\n⏭️ Skipping memory storage for 'no message' input")
            
            # Process tool calls if any
            tool_calls = response.message.tool_calls if hasattr(response, 'message') and hasattr(response.message, 'tool_calls') else []
            results = []
            tool_calls_data = []
            
            if tool_calls:
                print(f"\n🔧 Executing {len(tool_calls)} tool(s)...")
                
                for tool_call in tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = tool_call.function.arguments or {}
                    
                    print(f"\n   → {tool_name}({', '.join([f'{k}={v}' for k, v in tool_args.items()])})")
                    
                    # Execute tool
                    result = self.tool_registry.execute_tool(tool_name, **tool_args)
                    results.append(result)
                    
                    # Add to conversation turn
                    self.conversation.add_tool_call(tool_name, tool_args, result)
                    
                    # Store tool execution in memory (with full result - 2000 chars)
                    self.memory.add_memory({
                        'type': 'tool_execution',
                        'tool_name': tool_name,
                        'args': tool_args,
                        'result': str(result)[:2000]  # Increased from 500 to 2000 chars
                    })
                    
                    print(f"   ✓ Result: {str(result)[:200]}...")
                    
                    # Track for session log (include result!)
                    tool_calls_data.append({
                        'tool': tool_name,
                        'args': tool_args,
                        'result': result  # Add the result here!
                    })
            
            # End conversation turn
            self.conversation.end_turn()
            
            # Log this interaction to session
            self.session_logger.log_interaction(
                user_input=user_input,
                raw_prompt=prompt,
                raw_response=response,
                tool_calls=tool_calls_data,
                tool_results=[{
                    'tool': tc['tool'],
                    'args': tc['args'],
                    'result': results[i] if i < len(results) else None
                } for i, tc in enumerate(tool_calls_data)]
            )
            
            return {
                'response': response,
                'tool_results': results,
                'agent_thought': agent_thought,
                'is_no_message': is_no_message
            }
            
        except Exception as e:
            print(f"\n❌ Error processing task: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'error': str(e),
                'response': None,
                'tool_results': []
            }
    
    def _build_prompt(self, user_input: str) -> str:
        """Build ReAct-style prompt with conversation history and context."""
        
        # Get conversation history
        conversation_history = self.conversation.format_for_prompt()
        
        # Get tool summary
        tool_summary = self.conversation.get_tool_summary()
        
        # Get formatted insights
        insights = self.insight_loader.format_for_prompt()
        
        # Get pending tool results (from async queue execution)
        from core.pending_results import pending_tool_results
        unadded_results = pending_tool_results.get_unadded_results()
        
        if unadded_results:
            pending_results_text = "The following tool executions completed after your last response:\n\n"
            for result in unadded_results:
                pending_results_text += f"Tool: {result.tool_name}\n"
                pending_results_text += f"Arguments: {result.args}\n"
                pending_results_text += f"Result: {result.result[:500]}...\n"
                pending_results_text += f"---\n"
            
            # Mark all as added
            pending_tool_results.mark_all_as_added([r.tool_id for r in unadded_results])
            print(f"📋 Injected {len(unadded_results)} pending tool results into prompt")
        else:
            pending_results_text = "No pending tool results."
        
        # Build explicit tool list so the LLM is aware of every callable tool
        tool_list_lines = []
        native_tools = []
        mcp_tools = []
        for name in sorted(self.tool_registry.get_tool_names()):
            tool = self.tool_registry.get_tool(name)
            if name.startswith('mcp_'):
                mcp_tools.append((name, tool.description))
            else:
                native_tools.append((name, tool.description))
        
        if native_tools:
            tool_list_lines.append("[Native Tools]")
            for name, desc in native_tools:
                tool_list_lines.append(f"  • {name}: {desc}")
        if mcp_tools:
            tool_list_lines.append("[MCP Tools — external AI/service tools]")
            for name, desc in mcp_tools:
                tool_list_lines.append(f"  • {name}: {desc}")
        available_tools_text = "\n".join(tool_list_lines)
        
        prompt = f"""=== SYSTEM INSTRUCTIONS ===
You are Seeker, an advanced Autonomous AI Agent NOT A CHAT BOT. if you want to interact wth user use interactive tools
You work using the ReAct pattern: Reasoning → Acting → Observing → Reasoning → ...

{insights}

=== CRITICAL GUIDELINES ===
1. **ALWAYS check conversation history before calling tools**
2. **NEVER call the same tool with the same arguments twice**
3. **Think step-by-step about what you've learned**
4. **If you've already gathered information, USE it - don't re-fetch**
5. **Make progress toward your goals with each action**
6. **Explain your reasoning BEFORE calling tools**

=== AVAILABLE TOOLS ({len(native_tools)} native, {len(mcp_tools)} MCP) ===
{available_tools_text}

=== CONVERSATION HISTORY ===
{conversation_history}

=== TOOL USAGE SUMMARY ===
{tool_summary}

=== CURRENT TIME ===
{datetime.now().isoformat()}

=== PENDING TOOL RESULTS ===
{pending_results_text}

=== CURRENT TASK ===
Supervisor: {user_input or "Continue your investigation"}

=== YOUR RESPONSE ===
Before responding, think through these questions:
1. What have I already discovered from previous tool calls?
2. What information do I still need to accomplish my goal?
3. Should I call a tool, or can I answer based on what I already know?

If calling a tool:
- Explain WHY you're calling it
- If you've called this tool before, explain why you need to call it AGAIN with different arguments
- Make sure you're not repeating a previous tool call

Your response:
"""
        return prompt
    
    def _summarize_memory(self, save_to_file: bool = False, filename: Optional[str] = None) -> str:
        """
        Summarize memory using LLM.
        
        Args:
            save_to_file: Whether to save summary to Agent_Insight folder
            filename: Optional filename for saving
            
        Returns:
            The generated summary
        """
        # Build summary prompt
        memory_entries = self.memory.get_recent_memory(10)
        summary_prompt = "Summarize the following interactions concisely:\n\n"
        
        for entry in memory_entries:
            if entry.get('type') == 'user_input':
                summary_prompt += f"User: {entry.get('content', '')}\n"
            elif entry.get('type') == 'tool_execution':
                summary_prompt += f"Tool: {entry.get('tool_name', '')} - {entry.get('result', '')[:100]}\n"
        
        summary_prompt += "\nProvide a brief summary of what was accomplished."
        
        try:
            response = self.llm_client.chat(summary_prompt, expect_json=False)
            summary = response.message.content if hasattr(response, 'message') else str(response)
            
            # Save to memory
            self.memory.create_summary(summary)
            print(f"✓ Memory summarized\n")
            
            # Optionally save to file
            if save_to_file:
                if not filename:
                    filename = f"memory_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                
                insight_dir = self.config.project_root / "Agent_Insight"
                insight_dir.mkdir(exist_ok=True)
                
                filepath = insight_dir / filename
                filepath.write_text(f"# Memory Summary\n\n{summary}\n\nGenerated: {datetime.now().isoformat()}", 
                                   encoding='utf-8')
                print(f"✓ Summary saved to Agent_Insight/{filename}\n")
            
            return summary
            
        except Exception as e:
            print(f"⚠️  Failed to summarize memory: {e}")
            return f"Error: {e}"
    
    def run_interactive(self):
        """Run the agent in interactive mode."""
        print("=" * 60)
        print("🚀 Seeker Agent - Interactive Mode")
        print("=" * 60)
        print(f"Model: {self.config.model_name}")
        print(f"Tools: {len(self.tool_registry.get_tool_names())}")
        print("\nType 'exit' to quit, 'tools' to list available tools")
        print("=" * 60)
        
        while True:
            try:
                user_input = input("\n📝 You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() == 'exit':
                    print("\n👋 Goodbye!")
                    break
                if user_input.lower() == 'clear':
                    self.memory.clear()
                    print("\n💾 Memory cleared")
                    continue
                if user_input.lower() == 'save':
                    self.save_session()
                    print("\n💾 Session saved")
                    continue
                if user_input.lower() == '.':
                    user_input = 'No message'
                    

                if user_input.lower() == 'tools':
                    print("\n🔧 Available tools:")
                    for tool_name in self.tool_registry.get_tool_names():
                        tool = self.tool_registry.get_tool(tool_name)
                        print(f"  • {tool_name}: {tool.description}")
                    continue
                
                if user_input.lower() == 'memory':
                    print(f"\n💾 Memory status: {self.memory}")
                    continue
                
                # Process the task
                result = self.process_task(user_input)
                
                # Display response
                response = result['response']
                if hasattr(response, 'message') and hasattr(response.message, 'content'):
                    if response.message.content:
                        print(f"\n🤖 Seeker: {response.message.content}")
                
                # Display tool results
                if result['tool_results']:
                    print(f"\n📊 Executed {len(result['tool_results'])} tool(s)")
            
            except KeyboardInterrupt:
                print("\n\n⚠️  Interrupted by user")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
        
        # Close session on exit
        self.session_logger.close_session()
    
    def save_session(self, filepath: Optional[str] = None):
        """Save current session to file."""
        if filepath is None:
            filepath = self.config.logs_dir / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.memory.save_to_file(str(filepath))
        print(f"💾 Session saved to {filepath}")
    
    def load_session(self, filepath: str):
        """Load session from file."""
        self.memory.load_from_file(filepath)
        print(f"📂 Session loaded from {filepath}")
    
    def __repr__(self):
        return (
            f"SeekerAgent(model={self.config.model_name}, "
            f"tools={len(self.tool_registry.get_tool_names())}, "
            f"session={self.session_logger.session_id[:8]}...)"
        )
