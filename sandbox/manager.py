#!/usr/bin/env python3
"""
Sandbox Manager - Manages sandbox containers for OS building
"""

import os
import subprocess
import time
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SandboxConfig:
    """Sandbox configuration"""
    type: str = "docker"
    image: str = "debian:bookworm-slim"
    memory_limit: str = "2g"
    cpu_limit: int = 2
    disk_limit: str = "10g"
    network_enabled: bool = True


class SandboxManager:
    """
    Manages sandbox lifecycle for OS building.
    
    Provides isolated environments using Docker or chroot.
    """
    
    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()
        self.active_sandboxes: Dict[str, Dict] = {}
        
    def create_sandbox(self, name: str, image: Optional[str] = None) -> str:
        """
        Create a new sandbox environment.
        
        Args:
            name: Name for the sandbox
            image: Optional custom image
            
        Returns:
            Sandbox ID
        """
        sandbox_id = f"sandbox-{name}-{int(time.time())}"
        image = image or self.config.image
        
        if self.config.type == "docker":
            sandbox_id = self._create_docker(name, image)
        elif self.config.type == "chroot":
            sandbox_id = self._create_chroot(name)
            
        self.active_sandboxes[sandbox_id] = {
            "name": name,
            "image": image,
            "created_at": time.time(),
            "status": "created"
        }
        
        return sandbox_id
        
    def _create_docker(self, name: str, image: str) -> str:
        """Create Docker sandbox."""
        container_name = f"takax-{name}-{int(time.time())}"
        
        try:
            # Check if Docker is available
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print("Docker not available, using mock mode")
                return container_name
                
            # Create and start container
            cmd = [
                "docker", "run", "-d",
                "--name", container_name,
                "--hostname", "takax-build",
                "--memory", self.config.memory_limit,
                "--cpus", str(self.config.cpu_limit),
                "-e", "DEBIAN_FRONTEND=noninteractive",
                image,
                "sleep", "infinity"
            ]
            
            subprocess.run(cmd, capture_output=True)
            
        except FileNotFoundError:
            print("Docker not found, using mock mode")
            
        return container_name
        
    def _create_chroot(self, name: str) -> str:
        """Create chroot sandbox."""
        base_dir = Path("/tmp/takax") / name
        base_dir.mkdir(parents=True, exist_ok=True)
        return str(base_dir)
        
    def start_sandbox(self, sandbox_id: str) -> bool:
        """Start a sandbox."""
        if sandbox_id in self.active_sandboxes:
            self.active_sandboxes[sandbox_id]["status"] = "running"
            return True
        return False
        
    def stop_sandbox(self, sandbox_id: str) -> bool:
        """Stop a sandbox."""
        if self.config.type == "docker":
            try:
                subprocess.run(
                    ["docker", "stop", sandbox_id],
                    capture_output=True
                )
            except:
                pass
                
        if sandbox_id in self.active_sandboxes:
            self.active_sandboxes[sandbox_id]["status"] = "stopped"
            return True
        return False
        
    def delete_sandbox(self, sandbox_id: str) -> bool:
        """Delete a sandbox."""
        if self.config.type == "docker":
            try:
                subprocess.run(
                    ["docker", "rm", "-f", sandbox_id],
                    capture_output=True
                )
            except:
                pass
                
        if sandbox_id in self.active_sandboxes:
            del self.active_sandboxes[sandbox_id]
            return True
        return False
        
    def execute_command(
        self,
        sandbox_id: str,
        command: str,
        cwd: Optional[str] = None
    ) -> tuple[str, int]:
        """
        Execute command in sandbox.
        
        Args:
            sandbox_id: Sandbox ID
            command: Command to execute
            cwd: Optional working directory
            
        Returns:
            Tuple of (output, exit_code)
        """
        if self.config.type == "docker":
            return self._execute_docker(sandbox_id, command, cwd)
        elif self.config.type == "chroot":
            return self._execute_chroot(sandbox_id, command, cwd)
            
        return "Sandbox not found", 1
        
    def _execute_docker(
        self,
        sandbox_id: str,
        command: str,
        cwd: Optional[str] = None
    ) -> tuple[str, int]:
        """Execute command in Docker sandbox."""
        cmd = ["docker", "exec"]
        
        if cwd:
            cmd.extend(["-w", cwd])
            
        cmd.extend([sandbox_id, "sh", "-c", command])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        return result.stdout, result.returncode
        
    def _execute_chroot(
        self,
        sandbox_id: str,
        command: str,
        cwd: Optional[str] = None
    ) -> tuple[str, int]:
        """Execute command in chroot sandbox."""
        chroot_cmd = f"chroot {sandbox_id} {command}"
        
        result = subprocess.run(
            chroot_cmd,
            capture_output=True,
            text=True,
            shell=True
        )
        
        return result.stdout, result.returncode
        
    def get_sandbox_info(self, sandbox_id: str) -> Optional[Dict[str, Any]]:
        """Get sandbox information."""
        return self.active_sandboxes.get(sandbox_id)
        
    def list_sandboxes(self) -> List[Dict[str, Any]]:
        """List all sandboxes."""
        return list(self.active_sandboxes.values())
        
    def get_stats(self, sandbox_id: str) -> Dict[str, Any]:
        """Get sandbox resource usage."""
        if self.config.type == "docker":
            try:
                result = subprocess.run(
                    ["docker", "stats", "--no-stream", "--format",
                     "{{.CPUPerc}}|{{.MemUsage}}|{{.NetIO}}", sandbox_id],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    parts = result.stdout.strip().split("|")
                    return {
                        "cpu": parts[0] if len(parts) > 0 else "N/A",
                        "memory": parts[1] if len(parts) > 1 else "N/A",
                        "network": parts[2] if len(parts) > 2 else "N/A"
                    }
            except:
                pass
                
        return {"cpu": "N/A", "memory": "N/A", "network": "N/A"}
        
    def cleanup_all(self):
        """Clean up all sandboxes."""
        for sandbox_id in list(self.active_sandboxes.keys()):
            self.delete_sandbox(sandbox_id)


class SandboxPool:
    """Pool of sandbox instances for parallel builds."""
    
    def __init__(self, size: int = 3, config: Optional[SandboxConfig] = None):
        self.size = size
        self.config = config or SandboxConfig()
        self.manager = SandboxManager(self.config)
        self.available: List[str] = []
        self.in_use: Dict[str, str] = {}
        
    def acquire(self, name: str = "build") -> Optional[str]:
        """Acquire sandbox from pool."""
        if self.available:
            sandbox_id = self.available.pop()
            self.in_use[sandbox_id] = name
            return sandbox_id
            
        # Create new if pool not full
        if len(self.in_use) + len(self.available) < self.size:
            sandbox_id = self.manager.create_sandbox(name)
            self.in_use[sandbox_id] = name
            return sandbox_id
            
        return None
        
    def release(self, sandbox_id: str):
        """Release sandbox back to pool."""
        if sandbox_id in self.in_use:
            del self.in_use[sandbox_id]
            self.available.append(sandbox_id)
            
    def shutdown(self):
        """Shutdown the pool."""
        for sandbox_id in list(self.in_use.keys()):
            self.manager.delete_sandbox(sandbox_id)
        for sandbox_id in self.available:
            self.manager.delete_sandbox(sandbox_id)
        self.in_use.clear()
        self.available.clear()