"""
Takax CLI - Command Line Interface for creating Linux OS via chat
"""

__version__ = "1.0.0"
__author__ = "Takax Team"
__license__ = "MIT"

from .main import main
from .chat import ChatHandler
from .terminal import TerminalDisplay
from .config import ConfigManager

__all__ = ["main", "ChatHandler", "TerminalDisplay", "ConfigManager"]