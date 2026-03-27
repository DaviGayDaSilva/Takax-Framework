#!/usr/bin/env python3
"""
WebSocket Manager - Handles real-time WebSocket connections for terminal and chat
"""

import asyncio
import uuid
from typing import Dict, Optional, Any
from fastapi import WebSocket
import json


class WebSocketManager:
    """Manages WebSocket connections and message routing"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}
        self.terminal_sessions: Dict[str, Any] = {}
        
    def create_session(self, websocket: WebSocket, is_chat: bool = False) -> str:
        """Create a new WebSocket session"""
        session_id = str(uuid.uuid4())[:8]
        
        self.sessions[session_id] = {
            "websocket": websocket,
            "is_chat": is_chat,
            "created_at": asyncio.get_event_loop().time(),
            "last_activity": asyncio.get_event_loop().time()
        }
        
        return session_id
        
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session by ID"""
        return self.sessions.get(session_id)
        
    def close_session(self, session_id: str):
        """Close and remove a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            
    async def send_to_session(self, session_id: str, message: Dict):
        """Send message to specific session"""
        session = self.get_session(session_id)
        if session and session["websocket"]:
            try:
                await session["websocket"].send_json(message)
            except Exception as e:
                print(f"Error sending message: {e}")
                self.close_session(session_id)
                
    async def broadcast(self, message: Dict, exclude: Optional[str] = None):
        """Broadcast message to all sessions"""
        for sid, session in self.sessions.items():
            if sid != exclude:
                await self.send_to_session(sid, message)
                
    async def handle_message(self, session_id: str, data: Dict, terminal: Any):
        """Handle incoming message from terminal session"""
        session = self.get_session(session_id)
        if not session:
            return
            
        msg_type = data.get("type", "")
        content = data.get("content", "")
        
        if msg_type == "input":
            # Process terminal input
            await self.process_terminal_input(session_id, content, terminal)
        elif msg_type == "resize":
            # Handle terminal resize
            await self.process_terminal_resize(content, terminal)
        elif msg_type == "command":
            # Execute command
            await self.process_command(session_id, content, terminal)
            
    async def process_terminal_input(self, session_id: str, input_data: str, terminal: Any):
        """Process terminal input"""
        # In a real implementation, this would send to a PTY
        response = {
            "type": "output",
            "content": f"Received: {input_data}\n"
        }
        await self.send_to_session(session_id, response)
        
    async def process_terminal_resize(self, data: Dict, terminal: Any):
        """Handle terminal resize event"""
        # Resize the PTY
        pass
        
    async def process_command(self, session_id: str, command: str, terminal: Any):
        """Process and execute command"""
        # Send command to sandbox
        response = {
            "type": "output",
            "content": f"$ {command}\n"
        }
        await self.send_to_session(session_id, response)
        
        # Simulate command execution
        await asyncio.sleep(0.5)
        
        if command.strip() == "ls":
            output = "bin  boot  dev  etc  home  lib  media  mnt  opt  proc  root  run  sbin  srv  sys  tmp  usr  var\n"
        elif command.strip() == "whoami":
            output = "takax\n"
        elif command.strip() == "uname -a":
            output = "Linux takax-build 5.10.0-21-amd64 #1 SMP Debian 5.10.21-1 x86_64 GNU/Linux\n"
        elif command.startswith("echo"):
            output = command[5:] + "\n"
        else:
            output = f"Command not found: {command}\n"
            
        response = {
            "type": "output",
            "content": output
        }
        await self.send_to_session(session_id, response)
        
    def get_active_sessions(self) -> int:
        """Get count of active sessions"""
        return len(self.sessions)
        
    def get_terminal_sessions(self) -> int:
        """Get count of terminal sessions"""
        return sum(1 for s in self.sessions.values() if not s.get("is_chat", False))
        
    def get_chat_sessions(self) -> int:
        """Get count of chat sessions"""
        return sum(1 for s in self.sessions.values() if s.get("is_chat", False))


class ChatSession:
    """Manages chat session state"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.messages = []
        self.current_project = None
        self.build_in_progress = False
        
    def add_message(self, role: str, content: str):
        """Add message to chat history"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": asyncio.get_event_loop().time()
        })
        
    def get_history(self) -> list:
        """Get chat history"""
        return self.messages
        
    def clear_history(self):
        """Clear chat history"""
        self.messages = []
        
    def set_project(self, project_id: str):
        """Set current project"""
        self.current_project = project_id
        
    def start_build(self):
        """Mark build as started"""
        self.build_in_progress = True
        
    def end_build(self):
        """Mark build as completed"""
        self.build_in_progress = False


# Global WebSocket manager instance
ws_manager = WebSocketManager()