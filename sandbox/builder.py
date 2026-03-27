#!/usr/bin/env python3
"""
Build Engine - Executes OS build process
"""

import os
import time
import json
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from sandbox.recipe import BuildRecipe, RecipeStep
from sandbox.manager import SandboxManager, SandboxConfig


@dataclass
class BuildProgress:
    """Build progress information"""
    step: str
    progress: float
    message: str
    logs: List[str]


class BuildEngine:
    """
    Executes the OS build process in sandbox environment.
    
    Handles recipe parsing, step execution, and output generation.
    """
    
    def __init__(self, config: Optional[Dict] = None, terminal=None):
        self.config = config or {}
        self.terminal = terminal
        self.current_build: Optional[Dict] = None
        
    def build_from_recipe(
        self,
        recipe: BuildRecipe,
        output_dir: str
    ) -> bool:
        """
        Build OS from recipe.
        
        Args:
            recipe: Build recipe
            output_dir: Output directory
            
        Returns:
            True if successful
        """
        self._log(f"Starting build: {recipe.name}")
        
        # Initialize sandbox
        sandbox_config = SandboxConfig(
            image=recipe.base_image,
            type=self.config.get("sandbox_type", "docker")
        )
        manager = SandboxManager(sandbox_config)
        
        # Create sandbox
        sandbox_id = manager.create_sandbox(recipe.name.lower().replace(" ", "-"))
        manager.start_sandbox(sandbox_id)
        
        try:
            # Execute build steps
            for i, step in enumerate(recipe.steps):
                progress = (i + 1) / len(recipe.steps) * 100
                self._log(f"[{int(progress)}%] {step.description}")
                
                # Execute step
                self._execute_step(manager, sandbox_id, step)
                
            # Generate output
            self._create_output(manager, sandbox_id, recipe, output_dir)
            
            self._log("Build completed successfully!")
            return True
            
        except Exception as e:
            self._log(f"Build failed: {str(e)}")
            return False
            
        finally:
            # Cleanup
            manager.delete_sandbox(sandbox_id)
            
    def _execute_step(
        self,
        manager: SandboxManager,
        sandbox_id: str,
        step: RecipeStep
    ):
        """Execute a single build step."""
        for command in step.commands:
            output, code = manager.execute_command(sandbox_id, command)
            
            if code != 0:
                raise Exception(f"Command failed: {command}\n{output}")
                
            if output:
                self._log(f"  {output.strip()}")
                
    def _create_output(
        self,
        manager: SandboxManager,
        sandbox_id: str,
        recipe: BuildRecipe,
        output_dir: str
    ):
        """Create final output artifacts."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Copy files from sandbox
        # In real implementation, would copy from container
        
        # Create metadata
        metadata = {
            "name": recipe.name,
            "base_image": recipe.base_image,
            "type": recipe.type,
            "packages": recipe.packages,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open(output_path / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
            
        # Create README
        readme = f"""# {recipe.name}

Built with Takax Framework

## Configuration

- Base: {recipe.base_image}
- Type: {recipe.type}
- Packages: {', '.join(recipe.packages) if recipe.packages else 'None'}

## Usage

Extract and use the root filesystem:

    tar -xzf {recipe.name.lower().replace(' ', '-')}.tar.gz -C /path/to/root
"""
        
        with open(output_path / "README.md", "w") as f:
            f.write(readme)
            
        self._log(f"Output created: {output_dir}")
        
    def _log(self, message: str):
        """Log message to terminal or print."""
        if self.terminal:
            self.terminal.print_info(message)
        else:
            print(f"  ℹ {message}")
            
    # Quick build methods for CLI
    def quick_build(
        self,
        distro: str,
        packages: List[str],
        output_dir: str,
        os_type: str = "minimal"
    ) -> bool:
        """Quick build with simple parameters."""
        
        recipe = BuildRecipe(
            name=f"Custom {distro.title()} OS",
            base_image=self._get_base_image(distro),
            type=os_type,
            packages=packages
        )
        
        return self.build_from_recipe(recipe, output_dir)
        
    def _get_base_image(self, distro: str) -> str:
        """Get base image for distribution."""
        images = {
            "debian": "debian:bookworm-slim",
            "ubuntu": "ubuntu:22.04",
            "arch": "archlinux:latest",
            "fedora": "fedora:39",
            "alpine": "alpine:latest"
        }
        return images.get(distro.lower(), "debian:bookworm-slim")


class MockBuildEngine:
    """Mock build engine for testing without Docker."""
    
    def __init__(self, config: Optional[Dict] = None, terminal=None):
        self.config = config or {}
        self.terminal = terminal
        self.steps_completed = []
        
    def build_from_recipe(
        self,
        recipe: BuildRecipe,
        output_dir: str
    ) -> bool:
        """Mock build execution."""
        self._log(f"Mock build: {recipe.name}")
        
        steps = [
            "Preparing environment",
            "Downloading base system",
            "Extracting packages",
            "Installing packages",
            "Configuring system",
            "Creating output"
        ]
        
        for i, step in enumerate(steps):
            time.sleep(0.3)  # Simulate work
            progress = (i + 1) / len(steps) * 100
            self._log(f"[{int(progress)}%] {step}")
            
        # Create output
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        metadata = {
            "name": recipe.name,
            "base_image": recipe.base_image,
            "type": recipe.type,
            "packages": recipe.packages
        }
        
        with open(output_path / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
            
        self._log("Mock build completed!")
        return True
        
    def quick_build(
        self,
        distro: str,
        packages: List[str],
        output_dir: str,
        os_type: str = "minimal"
    ) -> bool:
        """Quick mock build."""
        self._log(f"Building {distro} {os_type} with {packages}")
        time.sleep(1)
        return True
        
    def _log(self, message: str):
        """Log message."""
        if self.terminal:
            self.terminal.print_info(message)
        else:
            print(f"  ℹ {message}")


def create_engine(use_mock: bool = False, config: Optional[Dict] = None, terminal=None):
    """Factory function to create build engine."""
    if use_mock:
        return MockBuildEngine(config, terminal)
    return BuildEngine(config, terminal)