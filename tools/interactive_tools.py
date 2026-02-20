"""Example tool demonstrating remote user input."""
from .base import BaseTool
from core.input_manager import get_user_input


class InteractiveQuestionTool(BaseTool):
    """Tool that asks user questions and gets responses."""
    
    name = "ask_user"
    description = "Ask the user a question and get their response (works from terminal or web)"
    parameters = {
        "question": {
            "type": "string",
            "description": "The question to ask the user"
        },
        "timeout": {
            "type": "integer",
            "description": "Timeout in seconds (default 300)",
            "default": 300
        }
    }
    
    def execute(self, question: str, timeout: int = 300) -> str:
        """Ask user a question and return their response."""
        try:
            response = get_user_input(question, timeout=timeout)
            return f"User responded: {response}"
        except TimeoutError:
            return f"No response received within {timeout} seconds"
        except Exception as e:
            return f"Error getting user input: {e}"


class ConfirmActionTool(BaseTool):
    """Tool for confirming dangerous actions."""
    
    name = "confirm_action"
    description = "Ask user to confirm a potentially dangerous action"
    parameters = {
        "action": {
            "type": "string",
            "description": "Description of the action to confirm"
        }
    }
    
    def execute(self, action: str) -> bool:
        """Ask user to confirm an action."""
        try:
            response = get_user_input(
                f"⚠️ Confirm: {action}\nProceed? (yes/no): ",
                timeout=60
            )
            return response.lower() in ['yes', 'y']
        except TimeoutError:
            print("⏱️ Confirmation timeout - defaulting to NO")
            return False
        except Exception as e:
            print(f"❌ Error getting confirmation: {e}")
            return False
