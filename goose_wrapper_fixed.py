#!/usr/bin/env python3
"""
Goose AI Wrapper Script for Seeker AI Integration
Created by Seeker AI Agent on February 16, 2026

This script provides a Python interface to interact with the Goose AI agent,
enabling communication between Seeker and Goose for collaborative task execution.
"""

import subprocess
import sys
import os
import json

def run_goose_command(command_args):
    """Execute a Goose command and return the result"""
    try:
        # Construct the full command
        cmd = ['goose'] + command_args
        
        # Execute the command
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
        
        # Return structured result
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'return_code': result.returncode
        }
    except FileNotFoundError:
        return {
            'success': False,
            'stdout': '',
            'stderr': 'Goose command not found. Please ensure Goose AI is properly installed.',
            'return_code': -1
        }
    except Exception as e:
        return {
            'success': False,
            'stdout': '',
            'stderr': f'Error executing command: {str(e)}',
            'return_code': -1
        }

def get_version():
    """Get Goose AI version"""
    return run_goose_command(['--version'])

def list_providers():
    """List available LLM providers"""
    return run_goose_command(['providers', 'list'])

def list_sessions():
    """List existing Goose sessions"""
    return run_goose_command(['session', 'list'])

def start_session(session_name, provider=None):
    """Start a new Goose session"""
    cmd = ['session', 'new', session_name]
    if provider:
        cmd.extend(['--provider', provider])
    return run_goose_command(cmd)

def send_message(message):
    """Send a message to Goose"""
    return run_goose_command([message])

def end_session(session_name):
    """End a Goose session"""
    return run_goose_command(['session', 'stop', session_name])

def run_session_task(session_name, task):
    """Run a task in a specific session"""
    cmd = ['session', 'run', session_name, task]
    return run_goose_command(cmd)

# Example usage functions
def example_list_providers():
    """Example of how to list providers"""
    result = list_providers()
    if result['success']:
        print("Available providers:")
        print(result['stdout'])
    else:
        print("Error listing providers:")
        print(result['stderr'])

def example_start_session():
    """Example of how to start a session"""
    result = start_session("test-session", "openai")
    if result['success']:
        print("Session started successfully")
        print(result['stdout'])
    else:
        print("Error starting session:")
        print(result['stderr'])

if __name__ == "__main__":
    # If script is run directly, show help
    if len(sys.argv) < 2:
        print("Goose AI Wrapper Script")
        print("Usage: python goose_wrapper.py [function] [arguments]")
        print("Available functions: list_providers, start_session, list_sessions")
        sys.exit(1)
    
    # Simple command router
    if sys.argv[1] == "list_providers":
        example_list_providers()
    elif sys.argv[1] == "start_session" and len(sys.argv) > 2:
        example_start_session(sys.argv[2])
    else:
        print("Invalid command or missing arguments")