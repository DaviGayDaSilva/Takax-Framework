"""
Takax Cloud - Web Interface Module
"""

__version__ = "1.0.0"
__author__ = "Takax Team"
__license__ = "MIT"

from .app import app
from .routes import router
from .websocket import WebSocketHandler
from .terminal import CloudTerminal

__all__ = ["app", "router", "WebSocketHandler", "CloudTerminal"]