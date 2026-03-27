#!/usr/bin/env python3
"""
SDK Client - Main client class for programmatic OS creation
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass

from sdk.sandbox import Sandbox
from sdk.build import BuildManager
from sdk.types import OSRecipe, BuildConfig, BuildResult, Template, Project


@dataclass
class ClientConfig:
    """SDK Client Configuration"""
    api_url: str = "http://localhost:8080"
    api_key: Optional[str] = None
    sandbox_type: str = "docker"
    sandbox_image: str = "debian:bookworm-slim"
    output_dir: str = "./takax-output"
    timeout: int = 3600


class TakaxClient:
    """
    Main SDK client for creating Linux operating systems programmatically.
    
    Example usage:
        from takax import TakaxClient
        
        client = TakaxClient()
        result = client.create_os(
            description="Minimal Debian with Python",
            output_format="chroot"
        )
        print(f"Build complete: {result.output_path}")
    """
    
    def __init__(self, config: Optional[ClientConfig] = None):
        """Initialize Takax client"""
        self.config = config or ClientConfig()
        self.sandbox = Sandbox(self.config.sandbox_type, self.config.sandbox_image)
        self.build_manager = BuildManager(self.sandbox)
        self._callbacks: Dict[str, List[Callable]] = {
            "on_build_start": [],
            "on_build_progress": [],
            "on_build_complete": [],
            "on_build_error": []
        }
        
    # ==================== Core Methods ====================
    
    def create_os(
        self,
        description: str,
        output_format: str = "chroot",
        packages: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None,
        callback: Optional[Callable] = None
    ) -> BuildResult:
        """
        Create a Linux OS from natural language description.
        
        Args:
            description: Natural language description of the OS
            output_format: Output format (chroot, tarball, iso)
            packages: Optional list of specific packages
            config: Optional configuration dictionary
            callback: Optional progress callback function
            
        Returns:
            BuildResult with build information and output path
        """
        # Create recipe from description
        recipe = self._parse_description(description)
        
        if packages:
            recipe.packages.extend(packages)
            
        if config:
            recipe.config.update(config)
            
        # Set output format
        recipe.output_format = output_format
        
        # Register callback if provided
        if callback:
            self.on_build_progress(callback)
            
        # Execute build
        return self.build_manager.build(recipe, self.config.output_dir)
        
    def create_from_template(
        self,
        template_name: str,
        output_dir: str = "./takax-output",
        custom_config: Optional[Dict[str, Any]] = None
    ) -> BuildResult:
        """
        Create OS from a pre-defined template.
        
        Args:
            template_name: Name of the template to use
            output_dir: Output directory for build artifacts
            custom_config: Optional custom configuration
            
        Returns:
            BuildResult with build information
        """
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
            
        # Create recipe from template
        recipe = OSRecipe(
            name=template.name,
            base_image=template.base_image,
            packages=template.packages.copy(),
            config=template.config.copy()
        )
        
        if custom_config:
            recipe.config.update(custom_config)
            
        return self.build_manager.build(recipe, output_dir)
        
    def create_from_recipe(
        self,
        recipe: OSRecipe,
        output_dir: str = "./takax-output"
    ) -> BuildResult:
        """
        Create OS from a detailed recipe.
        
        Args:
            recipe: OSRecipe object with full configuration
            output_dir: Output directory for build artifacts
            
        Returns:
            BuildResult with build information
        """
        return self.build_manager.build(recipe, output_dir)
        
    # ==================== Template Methods ====================
    
    def list_templates(self) -> List[Template]:
        """List available OS templates"""
        templates = [
            Template(
                name="debian-minimal",
                description="Minimal Debian base system",
                base_image="debian:bookworm-slim",
                packages=[],
                config={"type": "minimal"}
            ),
            Template(
                name="ubuntu-server",
                description="Ubuntu Server with common tools",
                base_image="ubuntu:22.04",
                packages=["openssh-server", "curl", "vim"],
                config={"type": "server", "ssh": True}
            ),
            Template(
                name="debian-python",
                description="Debian with Python development",
                base_image="debian:bookworm-slim",
                packages=["python3", "python3-pip", "build-essential"],
                config={"type": "development", "python": "3.11"}
            ),
            Template(
                name="alpine-minimal",
                description="Ultra-minimal Alpine Linux",
                base_image="alpine:latest",
                packages=["bash"],
                config={"type": "minimal"}
            ),
            Template(
                name="docker-host",
                description="System with Docker support",
                base_image="debian:bookworm-slim",
                packages=["docker.io", "docker-compose"],
                config={"type": "container-host", "docker": True}
            ),
        ]
        return templates
        
    def get_template(self, name: str) -> Optional[Template]:
        """Get specific template by name"""
        for template in self.list_templates():
            if template.name == name:
                return template
        return None
        
    # ==================== Project Methods ====================
    
    def create_project(
        self,
        name: str,
        description: str = "",
        config: Optional[Dict[str, Any]] = None
    ) -> Project:
        """
        Create a new project.
        
        Args:
            name: Project name
            description: Project description
            config: Optional project configuration
            
        Returns:
            Project object
        """
        project = Project(
            id=self._generate_id(),
            name=name,
            description=description,
            config=config or {},
            created_at=self._get_timestamp()
        )
        return project
        
    def save_project(self, project: Project, path: str):
        """Save project to file"""
        project_file = Path(path) / f"{project.id}.json"
        project_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(project_file, 'w') as f:
            json.dump(project.to_dict(), f, indent=2)
            
    def load_project(self, path: str) -> Project:
        """Load project from file"""
        with open(path) as f:
            data = json.load(f)
        return Project.from_dict(data)
        
    # ==================== Event Callbacks ====================
    
    def on_build_start(self, callback: Callable):
        """Register build start callback"""
        self._callbacks["on_build_start"].append(callback)
        
    def on_build_progress(self, callback: Callable):
        """Register build progress callback"""
        self._callbacks["on_build_progress"].append(callback)
        
    def on_build_complete(self, callback: Callable):
        """Register build complete callback"""
        self._callbacks["on_build_complete"].append(callback)
        
    def on_build_error(self, callback: Callable):
        """Register build error callback"""
        self._callbacks["on_build_error"].append(callback)
        
    def _trigger_callback(self, event: str, *args, **kwargs):
        """Trigger registered callbacks"""
        for callback in self._callbacks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                print(f"Callback error: {e}")
                
    # ==================== Helper Methods ====================
    
    def _parse_description(self, description: str) -> OSRecipe:
        """Parse natural language description into recipe"""
        desc_lower = description.lower()
        
        # Detect distro
        distro = "debian"
        for d in ["ubuntu", "debian", "arch", "fedora", "alpine"]:
            if d in desc_lower:
                distro = d
                break
                
        # Detect type
        os_type = "minimal"
        if "server" in desc_lower:
            os_type = "server"
        elif "desktop" in desc_lower or "gui" in desc_lower:
            os_type = "desktop"
        elif "development" in desc_lower or "dev" in desc_lower:
            os_type = "development"
            
        # Detect packages
        packages = []
        package_map = {
            "python": "python3",
            "python3": "python3",
            "nodejs": "nodejs",
            "node": "nodejs",
            "docker": "docker.io",
            "ssh": "openssh-server",
            "nginx": "nginx",
            "apache": "apache2",
            "mysql": "mariadb-server",
            "postgres": "postgresql",
            "redis": "redis-server",
        }
        
        for keyword, package in package_map.items():
            if keyword in desc_lower and package not in packages:
                packages.append(package)
                
        # Create recipe
        base_images = {
            "debian": "debian:bookworm-slim",
            "ubuntu": "ubuntu:22.04",
            "arch": "archlinux:latest",
            "fedora": "fedora:39",
            "alpine": "alpine:latest"
        }
        
        return OSRecipe(
            name="Custom OS",
            base_image=base_images.get(distro, "debian:bookworm-slim"),
            packages=packages,
            config={
                "type": os_type,
                "distro": distro
            }
        )
        
    def _generate_id(self) -> str:
        """Generate unique ID"""
        import uuid
        return str(uuid.uuid4())[:8]
        
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()


# Convenience function
def create_os(description: str, **kwargs) -> BuildResult:
    """
    Convenience function to create OS from description.
    
    Example:
        from takax import create_os
        
        result = create_os("Minimal Debian with Python and SSH")
        print(result.output_path)
    """
    client = TakaxClient()
    return client.create_os(description, **kwargs)