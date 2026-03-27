"""
Takax SDK - Software Development Kit for programmatic OS creation
"""

__version__ = "1.0.0"
__author__ = "Takax Team"
__license__ = "MIT"

from .client import TakaxClient
from .sandbox import Sandbox
from .build import BuildManager
from .types import (
    OSRecipe,
    BuildConfig,
    BuildResult,
    Template,
    Project
)

__all__ = [
    "TakaxClient",
    "Sandbox",
    "BuildManager",
    "OSRecipe",
    "BuildConfig", 
    "BuildResult",
    "Template",
    "Project"
]