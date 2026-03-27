#!/usr/bin/env python3
"""
Cloud Terminal - Server-side terminal emulation for web interface
"""

import os
import pty
import select
import subprocess
import asyncio
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class TerminalSession:
    """Terminal session state"""
    pid: int
    fd: int
    shell: str
    cwd: str
    rows: int = 24
    cols: int = 80


class CloudTerminal:
    """Server-side terminal emulator"""
    
    def __init__(self, shell: str = "/bin/bash", cwd: str = "/"):
        self.shell = shell
        self.cwd = cwd
        self.sessions = {}
        
    async def create_session(self, session_id: str) -> TerminalSession:
        """Create a new PTY session"""
        pid, fd = pty.fork()
        
        if pid == 0:
            # Child process
            if self.cwd:
                os.chdir(self.cwd)
            os.execvp(self.shell, [self.shell])
        else:
            # Parent process
            session = TerminalSession(
                pid=pid,
                fd=fd,
                shell=self.shell,
                cwd=self.cwd
            )
            self.sessions[session_id] = session
            return session
            
    async def write(self, session_id: str, data: str) -> str:
        """Write to terminal and get output"""
        session = self.sessions.get(session_id)
        if not session:
            return "Session not found"
            
        # Write to PTY
        os.write(session.fd, data.encode())
        
        # Read output
        await asyncio.sleep(0.01)  # Small delay for output
        
        output = self._read_output(session)
        return output
        
    def _read_output(self, session: TerminalSession) -> str:
        """Read available output from PTY"""
        try:
            # Use select to check for available data
            ready, _, _ = select.select([session.fd], [], [], 0.1)
            if ready:
                return os.read(session.fd, 4096).decode('utf-8', errors='replace')
        except:
            pass
        return ""
        
    async def resize(self, session_id: str, rows: int, cols: int):
        """Resize terminal"""
        session = self.sessions.get(session_id)
        if session:
            session.rows = rows
            session.cols = cols
            # Set window size
            import fcntl
            import termios
            winsize = termios.struct_winsize(rows, cols)
            fcntl.ioctl(session.fd, termios.TIOCSWINSZ, winsize)
            
    async def close_session(self, session_id: str):
        """Close terminal session"""
        session = self.sessions.get(session_id)
        if session:
            os.close(session.fd)
            # Kill process group
            try:
                os.killpg(os.getpgid(session.pid), 9)
            except:
                pass
            del self.sessions[session_id]
            
    async def execute_command(self, session_id: str, command: str) -> Tuple[str, int]:
        """Execute a single command and return output"""
        session = self.sessions.get(session_id)
        if not session:
            return "Session not found", -1
            
        # Write command with newline
        os.write(session.fd, f"{command}\n".encode())
        
        # Wait for command to complete
        await asyncio.sleep(0.5)
        
        # Read output
        output = ""
        for _ in range(10):  # Try reading multiple times
            chunk = self._read_output(session)
            if chunk:
                output += chunk
            else:
                break
                
        # Check if process finished
        try:
            pid, status = os.waitpid(session.pid, os.WNOHANG)
            if pid == session.pid:
                # Process finished, need to respawn
                await self.create_session(session_id)
                return output + "\n[Process exited]\n", status
        except:
            pass
            
        return output, 0
        
    def get_session_info(self, session_id: str) -> Optional[dict]:
        """Get session information"""
        session = self.sessions.get(session_id)
        if session:
            return {
                "shell": session.shell,
                "cwd": session.cwd,
                "rows": session.rows,
                "cols": session.cols,
                "pid": session.pid
            }
        return None


class MockTerminal:
    """Mock terminal for testing without PTY"""
    
    def __init__(self):
        self.output_buffer = []
        self.command_history = []
        
    async def create_session(self, session_id: str) -> dict:
        """Create mock session"""
        return {
            "session_id": session_id,
            "shell": "/bin/bash",
            "cwd": "/",
            "created": True
        }
        
    async def write(self, session_id: str, data: str) -> str:
        """Process input and return mock output"""
        self.command_history.append(data.strip())
        
        # Generate mock responses
        if data.strip() == "ls":
            return "bin  boot  dev  etc  home  lib  media  mnt  opt  proc  root  run  sbin  srv  sys  tmp  usr  var\n"
        elif data.strip() == "whoami":
            return "takax\n"
        elif data.strip() == "uname -a":
            return "Linux takax-build 5.10.0-21-amd64 #1 SMP Debian 5.10.21-1 x86_64 GNU/Linux\n"
        elif data.strip() == "pwd":
            return "/home/takax\n"
        elif data.strip() == "date":
            from datetime import datetime
            return datetime.now().strftime("%a %b %d %H:%M:%S UTC %Y\n")
        elif data.strip().startswith("echo"):
            return data.strip()[5:] + "\n"
        elif data.strip() == "help":
            return """Available commands:
  ls, pwd, whoami, uname, date, echo, clear, help
  Custom Takax commands:
  takax-build    - Build custom Linux OS
  takax-templates - List available templates
  takax-status   - Show build status
"""
        elif data.strip() == "takax-build":
            return "🚀 Starting OS build process...\n"
        elif data.strip() == "takax-templates":
            return """Available templates:
  - debian-minimal
  - ubuntu-server
  - debian-python
  - alpine-minimal
  - arch-linux
  - docker-host
"""
        elif data.strip() == "takax-status":
            return "✅ System ready\n"
        elif data.strip() == "clear":
            self.output_buffer = []
            return ""
        else:
            return f"{data.strip():s}: command not found\n"
            
    async def resize(self, session_id: str, rows: int, cols: int):
        """Mock resize"""
        pass
        
    async def close_session(self, session_id: str):
        """Mock close"""
        pass
        
    async def execute_command(self, session_id: str, command: str) -> Tuple[str, int]:
        """Execute mock command"""
        output = await self.write(session_id, command)
        return output, 0


# Terminal factory
def create_terminal(use_mock: bool = False):
    """Create terminal instance"""
    if use_mock:
        return MockTerminal()
    return CloudTerminal()