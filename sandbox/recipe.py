#!/usr/bin/env python3
"""
Recipe Parser - Parse natural language and YAML recipes into build recipes
"""

import re
import yaml
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class RecipeStep:
    """Single step in build recipe"""
    name: str
    description: str
    commands: List[str] = field(default_factory=list)
    

@dataclass
class BuildRecipe:
    """
    Build Recipe - Complete recipe for building an OS.
    
    Attributes:
        name: OS name
        base_image: Base distribution image
        type: OS type (minimal, server, desktop, etc.)
        packages: List of packages to install
        steps: Custom build steps
        config: Additional configuration
        output_format: Output format
    """
    name: str = "Custom OS"
    base_image: str = "debian:bookworm-slim"
    type: str = "minimal"
    packages: List[str] = field(default_factory=list)
    steps: List[RecipeStep] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    output_format: str = "chroot"
    
    def add_step(self, name: str, description: str, commands: List[str]):
        """Add a build step."""
        self.steps.append(RecipeStep(
            name=name,
            description=description,
            commands=commands
        ))
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "base_image": self.base_image,
            "type": self.type,
            "packages": self.packages,
            "steps": [
                {"name": s.name, "description": s.description, "commands": s.commands}
                for s in self.steps
            ],
            "config": self.config,
            "output_format": self.output_format
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BuildRecipe":
        """Create from dictionary."""
        recipe = cls(
            name=data.get("name", "Custom OS"),
            base_image=data.get("base_image", "debian:bookworm-slim"),
            type=data.get("type", "minimal"),
            packages=data.get("packages", []),
            config=data.get("config", {}),
            output_format=data.get("output_format", "chroot")
        )
        
        for step_data in data.get("steps", []):
            recipe.add_step(
                step_data["name"],
                step_data["description"],
                step_data.get("commands", [])
            )
            
        return recipe


class RecipeParser:
    """
    Parse natural language and YAML into build recipes.
    
    Example:
        parser = RecipeParser()
        recipe = parser.parse_description("Minimal Debian with Python and SSH")
    """
    
    # Keywords mapping
    DISTRO_KEYWORDS = {
        "debian": "debian:bookworm-slim",
        "ubuntu": "ubuntu:22.04",
        "arch": "archlinux:latest",
        "arch linux": "archlinux:latest",
        "fedora": "fedora:39",
        "alpine": "alpine:latest"
    }
    
    PACKAGE_KEYWORDS = {
        "python": "python3",
        "python3": "python3",
        "python 3": "python3",
        "nodejs": "nodejs",
        "node": "nodejs",
        "node.js": "nodejs",
        "docker": "docker.io",
        "ssh": "openssh-server",
        "openssh": "openssh-server",
        "nginx": "nginx",
        "apache": "apache2",
        "mysql": "mariadb-server",
        "maria": "mariadb-server",
        "postgres": "postgresql",
        "postgresql": "postgresql",
        "redis": "redis-server",
        "golang": "golang",
        "go": "golang",
        "rust": "rustc",
        "vim": "vim",
        "git": "git",
        "curl": "curl",
        "wget": "wget",
        "vim": "vim",
        "emacs": "emacs",
        "java": "default-jdk",
        "php": "php",
        "ruby": "ruby",
        "perl": "perl",
        "gcc": "build-essential",
        "build-essential": "build-essential",
    }
    
    TYPE_KEYWORDS = {
        "minimal": "minimal",
        "basic": "minimal",
        "server": "server",
        "desktop": "desktop",
        "gui": "desktop",
        "development": "development",
        "dev": "development",
    }
    
    def parse_description(self, description: str) -> BuildRecipe:
        """
        Parse natural language description into build recipe.
        
        Args:
            description: Natural language description
            
        Returns:
            BuildRecipe object
        """
        desc_lower = description.lower()
        
        # Detect distribution
        distro = "debian"
        for keyword, image in self.DISTRO_KEYWORDS.items():
            if keyword in desc_lower:
                distro = keyword.split()[0]  # Get distro name
                break
                
        # Get base image
        base_image = self.DISTRO_KEYWORDS.get(distro, "debian:bookworm-slim")
        
        # Detect OS type
        os_type = "minimal"
        for keyword, os_type_value in self.TYPE_KEYWORDS.items():
            if keyword in desc_lower:
                os_type = os_type_value
                break
                
        # Detect packages
        packages = []
        for keyword, package in self.PACKAGE_KEYWORDS.items():
            if keyword in desc_lower and package not in packages:
                packages.append(package)
                
        # Create recipe
        recipe = BuildRecipe(
            name=f"Custom {distro.title()} OS",
            base_image=base_image,
            type=os_type,
            packages=packages,
            config={
                "distro": distro,
                "os_type": os_type,
                "original_description": description
            }
        )
        
        # Add default build steps based on OS type
        self._add_default_steps(recipe, distro)
        
        return recipe
        
    def _add_default_steps(self, recipe: BuildRecipe, distro: str):
        """Add default build steps based on distribution."""
        
        if distro in ["debian", "ubuntu"]:
            recipe.add_step(
                "update",
                "Update package lists",
                ["apt-get update"]
            )
            
            if recipe.packages:
                recipe.add_step(
                    "install_packages",
                    f"Install packages: {', '.join(recipe.packages)}",
                    [f"apt-get install -y -qq {' '.join(recipe.packages)}"]
                )
                
        elif distro == "arch":
            recipe.add_step(
                "update",
                "Update package database",
                ["pacman -Sy --noconfirm"]
            )
            
            if recipe.packages:
                recipe.add_step(
                    "install_packages",
                    f"Install packages: {', '.join(recipe.packages)}",
                    [f"pacman -S --noconfirm {' '.join(recipe.packages)}"]
                )
                
        elif distro == "fedora":
            recipe.add_step(
                "update",
                "Update package metadata",
                ["dnf check-update || true"]
            )
            
            if recipe.packages:
                recipe.add_step(
                    "install_packages",
                    f"Install packages: {', '.join(recipe.packages)}",
                    [f"dnf install -y {' '.join(recipe.packages)}"]
                )
                
        elif distro == "alpine":
            recipe.add_step(
                "update",
                "Update package index",
                ["apk update"]
            )
            
            if recipe.packages:
                recipe.add_step(
                    "install_packages",
                    f"Install packages: {', '.join(recipe.packages)}",
                    [f"apk add {' '.join(recipe.packages)}"]
                )
                
        # Final configuration step
        recipe.add_step(
            "configure",
            "Final system configuration",
            [
                "# Set hostname",
                "echo 'takax' > /etc/hostname",
                "# Create build complete marker",
                "touch /takax-built"
            ]
        )
        
    def parse_yaml(self, yaml_content: str) -> BuildRecipe:
        """Parse YAML recipe content."""
        try:
            data = yaml.safe_load(yaml_content)
            return BuildRecipe.from_dict(data)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML: {str(e)}")
            
    def parse_file(self, filepath: str) -> BuildRecipe:
        """Parse recipe from file."""
        with open(filepath, 'r') as f:
            content = f.read()
            
        if filepath.endswith('.yaml') or filepath.endswith('.yml'):
            return self.parse_yaml(content)
        else:
            # Try as description
            return self.parse_description(content)
            
    def generate_yaml(self, recipe: BuildRecipe) -> str:
        """Generate YAML from recipe."""
        return yaml.dump(recipe.to_dict(), default_flow_style=False)


class RecipeValidator:
    """Validate recipe before building."""
    
    @staticmethod
    def validate(recipe: BuildRecipe) -> tuple[bool, List[str]]:
        """Validate recipe and return errors."""
        errors = []
        
        # Check name
        if not recipe.name:
            errors.append("Recipe name is required")
            
        # Check base image
        if not recipe.base_image:
            errors.append("Base image is required")
            
        # Check packages
        if recipe.packages:
            # Basic validation - no special characters
            for pkg in recipe.packages:
                if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9._+-]*$', pkg):
                    errors.append(f"Invalid package name: {pkg}")
                    
        # Check output format
        valid_formats = ["chroot", "tarball", "iso", "docker"]
        if recipe.output_format not in valid_formats:
            errors.append(f"Invalid output format: {recipe.output_format}")
            
        return len(errors) == 0, errors