#!/usr/bin/env python3
"""
Type Definitions - Type definitions for SDK
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional


class BuildStatus(Enum):
    """Build status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OutputFormat(Enum):
    """Output format enumeration"""
    CHROOT = "chroot"
    TARBALL = "tarball"
    ISO = "iso"
    DOCKER = "docker"


@dataclass
class OSRecipe:
    """
    OS Build Recipe - Configuration for building a Linux OS.
    
    Attributes:
        name: OS name
        base_image: Base image or distribution
        packages: List of packages to install
        config: Additional configuration
        output_format: Output format (chroot, tarball, iso)
    """
    name: str = "Custom OS"
    base_image: str = "debian:bookworm-slim"
    packages: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    output_format: str = "chroot"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "base_image": self.base_image,
            "packages": self.packages,
            "config": self.config,
            "output_format": self.output_format
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OSRecipe":
        """Create from dictionary"""
        return cls(
            name=data.get("name", "Custom OS"),
            base_image=data.get("base_image", "debian:bookworm-slim"),
            packages=data.get("packages", []),
            config=data.get("config", {}),
            output_format=data.get("output_format", "chroot")
        )


@dataclass
class BuildConfig:
    """
    Build Configuration - Advanced build options.
    """
    parallel: bool = True
    clean_after: bool = True
    compress_output: bool = True
    cache_enabled: bool = True
    timeout: int = 3600
    resources: Dict[str, Any] = field(default_factory=lambda: {
        "cpu": 2,
        "memory": "2g",
        "disk": "10g"
    })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "parallel": self.parallel,
            "clean_after": self.clean_after,
            "compress_output": self.compress_output,
            "cache_enabled": self.cache_enabled,
            "timeout": self.timeout,
            "resources": self.resources
        }


@dataclass
class BuildResult:
    """
    Build Result - Result of a build operation.
    
    Attributes:
        build_id: Unique build identifier
        status: Build status
        output_path: Path to output artifacts
        logs: Build logs
        duration: Build duration in seconds
        error: Error message if failed
    """
    build_id: str
    status: BuildStatus
    output_path: Optional[str] = None
    logs: List[str] = field(default_factory=list)
    duration: float = 0.0
    error: Optional[str] = None
    
    def is_success(self) -> bool:
        """Check if build was successful"""
        return self.status == BuildStatus.COMPLETED
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "build_id": self.build_id,
            "status": self.status.value,
            "output_path": self.output_path,
            "logs": self.logs,
            "duration": self.duration,
            "error": self.error
        }


@dataclass
class Template:
    """
    OS Template - Pre-defined build template.
    
    Attributes:
        name: Template name
        description: Template description
        base_image: Base image
        packages: Default packages
        config: Default configuration
    """
    name: str
    description: str
    base_image: str
    packages: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "base_image": self.base_image,
            "packages": self.packages,
            "config": self.config
        }


@dataclass
class Project:
    """
    Project - Manages OS build projects.
    
    Attributes:
        id: Project ID
        name: Project name
        description: Project description
        config: Project configuration
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    id: str
    name: str
    description: str = ""
    config: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "config": self.config,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Project":
        """Create from dictionary"""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            config=data.get("config", {}),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", "")
        )


@dataclass
class Component:
    """
    OS Component - Package or service to include in OS.
    
    Attributes:
        name: Component name
        type: Component type (package, service, config)
        version: Optional version
        config: Component configuration
    """
    name: str
    type: str = "package"
    version: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = {
            "name": self.name,
            "type": self.type
        }
        if self.version:
            data["version"] = self.version
        if self.config:
            data["config"] = self.config
        return data


@dataclass
class BuildLog:
    """
    Build Log - Detailed build log entry.
    
    Attributes:
        timestamp: Log timestamp
        level: Log level (info, warning, error)
        message: Log message
    """
    timestamp: str
    level: str
    message: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp,
            "level": self.level,
            "message": self.message
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BuildLog":
        """Create from dictionary"""
        return cls(
            timestamp=data["timestamp"],
            level=data["level"],
            message=data["message"]
        )


# Type aliases for convenience
RecipeDict = Dict[str, Any]
BuildCallback = callable
ProgressCallback = callable