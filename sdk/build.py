#!/usr/bin/env python3
"""
Build Manager - SDK module for managing OS builds
"""

import os
import time
import json
from pathlib import Path
from typing import Optional, Callable, List, Dict, Any

from sdk.sandbox import Sandbox
from sdk.types import OSRecipe, BuildResult, BuildStatus


class BuildManager:
    """
    Manages the build process for creating Linux operating systems.
    """
    
    def __init__(self, sandbox: Sandbox):
        self.sandbox = sandbox
        self.active_builds: Dict[str, "Build"] = {}
        
    def build(
        self,
        recipe: OSRecipe,
        output_dir: str,
        progress_callback: Optional[Callable] = None
    ) -> BuildResult:
        """
        Build an OS from recipe.
        
        Args:
            recipe: OS recipe configuration
            output_dir: Output directory for build artifacts
            progress_callback: Optional progress callback
            
        Returns:
            BuildResult with build information
        """
        build_id = self._generate_id()
        build = Build(build_id, recipe, output_dir, progress_callback)
        
        self.active_builds[build_id] = build
        
        try:
            # Start sandbox
            if not self.sandbox.is_active():
                self.sandbox.start()
                
            # Execute build steps
            result = build.execute(self.sandbox)
            
            return result
            
        finally:
            del self.active_builds[build_id]
            
    def get_build_status(self, build_id: str) -> Optional[BuildStatus]:
        """Get status of a build."""
        build = self.active_builds.get(build_id)
        if build:
            return build.get_status()
        return None
        
    def cancel_build(self, build_id: str) -> bool:
        """Cancel a running build."""
        build = self.active_builds.get(build_id)
        if build:
            build.cancel()
            return True
        return False
        
    def _generate_id(self) -> str:
        """Generate unique build ID."""
        return f"build-{int(time.time())}"


class Build:
    """Represents a single build operation."""
    
    def __init__(
        self,
        build_id: str,
        recipe: OSRecipe,
        output_dir: str,
        callback: Optional[Callable] = None
    ):
        self.build_id = build_id
        self.recipe = recipe
        self.output_dir = Path(output_dir)
        self.callback = callback
        self.status = BuildStatus.PENDING
        self.logs: List[str] = []
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.progress = 0.0
        self.cancelled = False
        
    def execute(self, sandbox: Sandbox) -> BuildResult:
        """Execute the build."""
        self.start_time = time.time()
        self.status = BuildStatus.RUNNING
        
        self._log("Starting build...")
        self._trigger_callback("start")
        
        try:
            # Ensure output directory
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # Step 1: Prepare environment
            self._update_progress(10, "Preparing build environment...")
            self._prepare_environment(sandbox)
            
            # Step 2: Setup base system
            self._update_progress(20, "Setting up base system...")
            self._setup_base_system(sandbox)
            
            # Step 3: Install packages
            if self.recipe.packages:
                self._update_progress(40, "Installing packages...")
                self._install_packages(sandbox)
                
            # Step 4: Configure system
            self._update_progress(70, "Configuring system...")
            self._configure_system(sandbox)
            
            # Step 5: Create output
            self._update_progress(90, "Creating output artifacts...")
            output_path = self._create_output(sandbox)
            
            # Complete
            self._update_progress(100, "Build completed!")
            self.status = BuildStatus.COMPLETED
            
            self._log("Build completed successfully!")
            self._trigger_callback("complete")
            
            return BuildResult(
                build_id=self.build_id,
                status=self.status,
                output_path=str(output_path),
                logs=self.logs.copy(),
                duration=time.time() - self.start_time
            )
            
        except Exception as e:
            self.status = BuildStatus.FAILED
            self._log(f"Build failed: {str(e)}")
            self._trigger_callback("error", str(e))
            
            return BuildResult(
                build_id=self.build_id,
                status=self.status,
                output_path=None,
                logs=self.logs.copy(),
                error=str(e),
                duration=time.time() - self.start_time
            )
            
        finally:
            self.end_time = time.time()
            
    def _prepare_environment(self, sandbox: Sandbox):
        """Prepare build environment."""
        # Create necessary directories
        sandbox.execute(f"mkdir -p {self.output_dir}")
        self._log("Environment prepared")
        
    def _setup_base_system(self, sandbox: Sandbox):
        """Setup base system in sandbox."""
        # Simulate base system setup
        sandbox.execute("apt-get update -qq")
        sandbox.execute("apt-get install -y -qq debootstrap")
        
        # Run debootstrap
        distro = self.recipe.config.get("distro", "debian")
        if distro == "debian":
            codename = "bookworm"
            cmd = f"debootstrap --variant=minetest {codename} {self.output_dir}/chroot http://deb.debian.org/debian"
            sandbox.execute(cmd)
        else:
            # Mock for other distros
            sandbox.execute(f"mkdir -p {self.output_dir}/chroot")
            
        self._log(f"Base system setup complete ({distro})")
        
    def _install_packages(self, sandbox: Sandbox):
        """Install packages in sandbox."""
        if not self.recipe.packages:
            return
            
        total = len(self.recipe.packages)
        
        for i, package in enumerate(self.recipe.packages):
            if self.cancelled:
                break
                
            self._log(f"Installing: {package}")
            sandbox.execute(f"apt-get install -y -qq {package}")
            
            progress = 40 + int((i + 1) / total * 30)
            self._update_progress(progress, f"Installing {package}...")
            
        self._log(f"Installed {total} packages")
        
    def _configure_system(self, sandbox: Sandbox):
        """Configure the system."""
        config = self.recipe.config
        
        # Set hostname
        hostname = config.get("hostname", "takax")
        sandbox.execute(f"echo {hostname} > {self.output_dir}/chroot/etc/hostname")
        
        # Configure locale
        sandbox.execute("echo 'en_US.UTF-8 UTF-8' > /etc/locale.gen")
        sandbox.execute("locale-gen")
        
        # Configure network
        sandbox.execute("echo '127.0.0.1 localhost' > /etc/hosts")
        
        # Create root user
        sandbox.execute("echo 'root:root' | chpasswd")
        
        self._log("System configuration complete")
        
    def _create_output(self, sandbox: Sandbox) -> Path:
        """Create output artifacts."""
        output_path = self.output_dir / f"{self.recipe.name.lower().replace(' ', '-')}.tar.gz"
        
        # Create tarball
        chroot_path = self.output_dir / "chroot"
        if chroot_path.exists():
            import tarfile
            with tarfile.open(output_path, "w:gz") as tar:
                tar.add(chroot_path, arcname=".")
                
        # Create metadata
        metadata = {
            "name": self.recipe.name,
            "base_image": self.recipe.base_image,
            "packages": self.recipe.packages,
            "config": self.recipe.config,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open(self.output_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
            
        self._log(f"Output created: {output_path}")
        return output_path
        
    def _update_progress(self, progress: float, message: str):
        """Update build progress."""
        self.progress = progress
        self._log(message)
        self._trigger_callback("progress", progress, message)
        
    def _log(self, message: str):
        """Add log entry."""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        
    def _trigger_callback(self, event: str, *args, **kwargs):
        """Trigger callback if registered."""
        if self.callback:
            try:
                self.callback(event, *args, **kwargs)
            except Exception as e:
                print(f"Callback error: {e}")
                
    def get_status(self) -> BuildStatus:
        """Get current build status."""
        return self.status
        
    def cancel(self):
        """Cancel the build."""
        self.cancelled = True
        self.status = BuildStatus.CANCELLED


class BuildHistory:
    """Track build history."""
    
    def __init__(self, storage_path: str = ".takax/builds"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
    def save(self, result: BuildResult):
        """Save build result."""
        filepath = self.storage_path / f"{result.build_id}.json"
        
        with open(filepath, 'w') as f:
            json.dump({
                "build_id": result.build_id,
                "status": result.status.value,
                "output_path": result.output_path,
                "logs": result.logs,
                "duration": result.duration,
                "error": result.error
            }, f, indent=2)
            
    def list(self) -> List[Dict]:
        """List all builds."""
        builds = []
        for filepath in self.storage_path.glob("*.json"):
            with open(filepath) as f:
                builds.append(json.load(f))
        return sorted(builds, key=lambda x: x.get("build_id", ""), reverse=True)