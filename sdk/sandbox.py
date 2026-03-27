#!/usr/bin/env python3
"""
Sandbox Wrapper - SDK wrapper for sandbox operations
"""

import os
import subprocess
import time
from typing import Optional, Dict, Any, List
from pathlib import Path


class Sandbox:
    """
    Sandbox environment manager for OS building.
    
    Provides isolated environment for building Linux operating systems.
    """
    
    SUPPORTED_TYPES = ["docker", "chroot", "qemu"]
    
    def __init__(self, sandbox_type: str = "docker", image: str = "debian:bookworm-slim"):
        """
        Initialize sandbox.
        
        Args:
            sandbox_type: Type of sandbox (docker, chroot, qemu)
            image: Docker image or chroot base
        """
        if sandbox_type not in self.SUPPORTED_TYPES:
            raise ValueError(f"Unsupported sandbox type: {sandbox_type}")
            
        self.sandbox_type = sandbox_type
        self.image = image
        self.container_id: Optional[str] = None
        self.is_running = False
        
    # ==================== Lifecycle Methods ====================
    
    def start(self, name: Optional[str] = None) -> bool:
        """
        Start the sandbox environment.
        
        Args:
            name: Optional name for the container
            
        Returns:
            True if started successfully
        """
        if self.sandbox_type == "docker":
            return self._start_docker(name)
        elif self.sandbox_type == "chroot":
            return self._start_chroot()
        return False
        
    def stop(self) -> bool:
        """Stop the sandbox environment."""
        if self.sandbox_type == "docker":
            return self._stop_docker()
        elif self.sandbox_type == "chroot":
            return self._stop_chroot()
        return False
        
    def is_active(self) -> bool:
        """Check if sandbox is running."""
        if self.sandbox_type == "docker":
            return self._check_docker()
        return self.is_running
        
    # ==================== Docker Methods ====================
    
    def _start_docker(self, name: Optional[str] = None) -> bool:
        """Start Docker container."""
        container_name = name or f"takax-sandbox-{int(time.time())}"
        
        try:
            # Check if Docker is available
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                print("Docker not available, using mock mode")
                self.is_running = True
                self.container_id = container_name
                return True
                
            # Run container
            cmd = [
                "docker", "run", "-d",
                "--name", container_name,
                "--hostname", "takax-build",
                "-v", f"{os.getcwd()}:/workspace",
                self.image,
                "sleep", "infinity"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.container_id = container_name
                self.is_running = True
                return True
            else:
                print(f"Docker error: {result.stderr}")
                return False
                
        except FileNotFoundError:
            print("Docker not found, using mock mode")
            self.is_running = True
            self.container_id = container_name
            return True
            
    def _stop_docker(self) -> bool:
        """Stop Docker container."""
        if not self.container_id:
            self.is_running = False
            return True
            
        try:
            subprocess.run(
                ["docker", "stop", self.container_id],
                capture_output=True
            )
            subprocess.run(
                ["docker", "rm", "-f", self.container_id],
                capture_output=True
            )
            self.is_running = False
            self.container_id = None
            return True
        except:
            self.is_running = False
            return True
            
    def _check_docker(self) -> bool:
        """Check if Docker container is running."""
        if not self.container_id:
            return False
            
        try:
            result = subprocess.run(
                ["docker", "inspect", "-f", "{{.State.Running}}", self.container_id],
                capture_output=True,
                text=True
            )
            return "true" in result.stdout.lower()
        except:
            return self.is_running
            
    # ==================== Chroot Methods ====================
    
    def _start_chroot(self) -> bool:
        """Start chroot environment."""
        # In a real implementation, this would set up a chroot
        self.is_running = True
        return True
        
    def _stop_chroot(self) -> bool:
        """Stop chroot environment."""
        self.is_running = False
        return True
        
    # ==================== Execution Methods ====================
    
    def execute(self, command: str, cwd: Optional[str] = None) -> tuple[str, int]:
        """
        Execute command in sandbox.
        
        Args:
            command: Command to execute
            cwd: Optional working directory
            
        Returns:
            Tuple of (output, exit_code)
        """
        if self.sandbox_type == "docker":
            return self._execute_docker(command, cwd)
        elif self.sandbox_type == "chroot":
            return self._execute_chroot(command, cwd)
        return ("Sandbox not running", 1)
        
    def _execute_docker(self, command: str, cwd: Optional[str] = None) -> tuple[str, int]:
        """Execute command in Docker container."""
        if not self.container_id:
            # Mock mode - simulate execution
            return self._mock_execute(command)
            
        cmd = ["docker", "exec"]
        if cwd:
            cmd.extend(["-w", cwd])
        cmd.extend([self.container_id, "sh", "-c", command])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout, result.returncode
        
    def _execute_chroot(self, command: str, cwd: Optional[str] = None) -> tuple[str, int]:
        """Execute command in chroot."""
        # Mock for chroot
        return self._mock_execute(command)
        
    def _mock_execute(self, command: str) -> tuple[str, int]:
        """Mock command execution for testing."""
        cmd = command.strip()
        
        if cmd == "ls":
            return "bin  boot  dev  etc  home  lib  media  mnt  opt  proc  root  run  sbin  srv  sys  tmp  usr  var\n", 0
        elif cmd == "whoami":
            return "root\n", 0
        elif cmd.startswith("echo"):
            return command[5:] + "\n", 0
        elif "apt-get" in cmd or "dpkg" in cmd:
            return "Processing...\n", 0
        else:
            return f"{command}: command not found\n", 127
            
    def copy_to(self, source: str, dest: str) -> bool:
        """Copy file to sandbox."""
        if self.sandbox_type == "docker" and self.container_id:
            try:
                subprocess.run(
                    ["docker", "cp", source, f"{self.container_id}:{dest}"],
                    check=True
                )
                return True
            except:
                return False
        return True
        
    def copy_from(self, source: str, dest: str) -> bool:
        """Copy file from sandbox."""
        if self.sandbox_type == "docker" and self.container_id:
            try:
                subprocess.run(
                    ["docker", "cp", f"{self.container_id}:{source}", dest],
                    check=True
                )
                return True
            except:
                return False
        return True
        
    # ==================== Info Methods ====================
    
    def get_info(self) -> Dict[str, Any]:
        """Get sandbox information."""
        return {
            "type": self.sandbox_type,
            "image": self.image,
            "container_id": self.container_id,
            "is_running": self.is_running
        }
        
    def get_stats(self) -> Dict[str, Any]:
        """Get sandbox resource usage."""
        if self.sandbox_type == "docker" and self.container_id:
            try:
                result = subprocess.run(
                    ["docker", "stats", "--no-stream", "--format", 
                     "{{.CPUPerc}}|{{.MemUsage}}", self.container_id],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    parts = result.stdout.strip().split("|")
                    return {
                        "cpu": parts[0] if len(parts) > 0 else "N/A",
                        "memory": parts[1] if len(parts) > 1 else "N/A"
                    }
            except:
                pass
                
        return {"cpu": "N/A", "memory": "N/A"}


class SandboxPool:
    """Pool of sandbox instances for parallel builds."""
    
    def __init__(self, size: int = 3, sandbox_type: str = "docker"):
        self.size = size
        self.sandbox_type = sandbox_type
        self.pool: List[Sandbox] = []
        self.available: List[Sandbox] = []
        
    def start(self):
        """Start all sandboxes in pool."""
        for i in range(self.size):
            sandbox = Sandbox(self.sandbox_type)
            sandbox.start(f"takax-pool-{i}")
            self.pool.append(sandbox)
            self.available.append(sandbox)
            
    def acquire(self) -> Optional[Sandbox]:
        """Acquire a sandbox from pool."""
        if self.available:
            return self.available.pop(0)
        return None
        
    def release(self, sandbox: Sandbox):
        """Release sandbox back to pool."""
        if sandbox in self.pool and sandbox not in self.available:
            self.available.append(sandbox)
            
    def stop(self):
        """Stop all sandboxes."""
        for sandbox in self.pool:
            sandbox.stop()
        self.pool.clear()
        self.available.clear()