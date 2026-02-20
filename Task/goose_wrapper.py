#!/usr/bin/env python3
"""
Goose AI Wrapper for Seeker Integration
=====================================

This module provides a Python interface to interact with the Goose AI agent,
enabling seamless integration with the Seeker AI framework.

Author: Seeker AI Agent
Date: February 16, 2026
"""

import subprocess
import json
import os
from typing import Optional, List, Dict, Any


class GooseWrapper:
    """A wrapper class for interacting with the Goose AI agent."""
    
    def __init__(self, provider: str = "ollama"):
        """
        Initialize the Goose wrapper.
        
        Args:
            provider (str): The LLM provider to use (default: "ollama")
        """
        self.provider = provider
        self.current_session = None
        self.session_name = None
    
    def _run_command(self, command: List[str], input_text: Optional[str] = None) -> tuple:
        """
        Execute a Goose command and return the result.
        
        Args:
            command (List[str]): The command to execute
            input_text (str, optional): Input text to send to the command
            
        Returns:
            tuple: (stdout, stderr, return_code)
        """
        try:
            if input_text:
                proc = subprocess.Popen(
                    command,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = proc.communicate(input=input_text)
            else:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True
                )
                stdout, stderr = result.stdout, result.stderr
            
            return stdout, stderr, result.returncode if 'result' in locals() else proc.returncode
        except Exception as e:
            return "", str(e), -1
    
    def start_session(self, session_name: Optional[str] = None) -> bool:
        """
        Start a new Goose session.
        
        Args:
            session_name (str, optional): Name for the session
            
        Returns:
            bool: True if successful, False otherwise
        """
        command = ["goose", "session", "start"]
        if session_name:
            command.extend(["--name", session_name])
            
        stdout, stderr, return_code = self._run_command(command)
        
        if return_code == 0:
            self.current_session = True
            # Extract session name from output if not provided
            if session_name:
                self.session_name = session_name
            else:
                # Try to extract session name from stdout
                lines = stdout.split('\n')
                for line in lines:
                    if 'starting session' in line.lower():
                        parts = line.split('|')
                        for part in parts:
                            if 'name:' in part:
                                self.session_name = part.split(':')[1].strip()
                                break
            return True
        else:
            print(f"Error starting session: {stderr}")
            return False
    
    def send_message(self, message: str) -> Optional[str]:
        """
        Send a message to the current Goose session.
        
        Args:
            message (str): The message to send
            
        Returns:
            str: Response from Goose, or None if failed
        """
        if not self.current_session:
            print("No active session. Please start a session first.")
            return None
            
        # For now, we'll use the run command for single messages
        command = ["goose", "run", message]
        stdout, stderr, return_code = self._run_command(command)
        
        if return_code == 0:
            return stdout
        else:
            print(f"Error sending message: {stderr}")
            return None
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all Goose sessions.
        
        Returns:
            List[Dict]: List of session information
        """
        command = ["goose", "session", "list"]
        stdout, stderr, return_code = self._run_command(command)
        
        if return_code == 0:
            # Parse session list (this is a simplified parser)
            sessions = []
            lines = stdout.split('\n')
            for line in lines:
                if line.strip() and not line.startswith('starting session'):
                    # Simple parsing - in reality, you might want to parse JSON or structured output
                    sessions.append({"info": line.strip()})
            return sessions
        else:
            print(f"Error listing sessions: {stderr}")
            return []
    
    def resume_session(self, session_name: str) -> bool:
        """
        Resume an existing Goose session.
        
        Args:
            session_name (str): Name of the session to resume
            
        Returns:
            bool: True if successful, False otherwise
        """
        command = ["goose", "session", "resume", session_name]
        stdout, stderr, return_code = self._run_command(command)
        
        if return_code == 0:
            self.current_session = True
            self.session_name = session_name
            return True
        else:
            print(f"Error resuming session: {stderr}")
            return False
    
    def end_session(self) -> bool:
        """
        End the current session.
        
        Returns:
            bool: True if successful, False otherwise
        """
        # Since Goose sessions are persistent, we just mark that we're not actively using one
        self.current_session = None
        self.session_name = None
        return True
    
    def get_providers(self) -> List[str]:
        """
        Get list of available providers.
        
        Returns:
            List[str]: List of provider names
        """
        command = ["goose", "providers", "list"]
        stdout, stderr, return_code = self._run_command(command)
        
        if return_code == 0:
            # Parse providers from output
            providers = []
            lines = stdout.split('\n')
            for line in lines:
                if line.strip() and not line.startswith('Name') and '|' in line:
                    provider = line.split('|')[0].strip()
                    if provider:
                        providers.append(provider)
            return providers
        else:
            print(f"Error getting providers: {stderr}")
            return []


def main():
    """Example usage of the GooseWrapper class."""
    # Create Goose wrapper instance
    goose = GooseWrapper()
    
    # Get available providers
    print("Available providers:")
    providers = goose.get_providers()
    for provider in providers:
        print(f"  - {provider}")
    
    # List existing sessions
    print("\nExisting sessions:")
    sessions = goose.list_sessions()
    for session in sessions:
        print(f"  - {session}")
    
    # Example of starting a session and sending a message
    print("\nStarting new session...")
    if goose.start_session("seeker-test-session"):
        print(f"Session started with name: {goose.session_name}")
        
        # Send a test message
        response = goose.send_message("Hello Goose! Can you tell me about your capabilities?")
        if response:
            print(f"Goose response: {response}")
        
        # End session
        goose.end_session()
        print("Session ended.")
    else:
        print("Failed to start session.")


if __name__ == "__main__":
    main()