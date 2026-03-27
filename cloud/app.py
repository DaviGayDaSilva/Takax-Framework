#!/usr/bin/env python3
"""
Takax Cloud - Web Application (FastAPI)
Provides web interface for creating Linux OS via chat with real-time terminal
"""

import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cloud.routes import router
from cloud.websocket import WebSocketManager
from cloud.terminal import CloudTerminal


# WebSocket manager for terminal connections
ws_manager = WebSocketManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 Starting Takax Cloud Server...")
    yield
    # Shutdown
    print("🛑 Shutting down Takax Cloud Server...")


# Create FastAPI app
app = FastAPI(
    title="Takax Cloud",
    description="Create Linux OS via chat - Web Interface",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_path = Path(__file__).parent / 'static'
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Templates
templates_path = Path(__file__).parent / 'templates'
templates = Jinja2Templates(directory=str(templates_path))


# Include API routes
app.include_router(router, prefix="/api")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Main page - Chat interface"""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "Takax - Create Linux OS"}
    )


@app.get("/project/{project_id}", response_class=HTMLResponse)
async def project_page(request: Request, project_id: str):
    """Project details page"""
    return templates.TemplateResponse(
        "project.html",
        {"request": request, "title": f"Project - {project_id}", "project_id": project_id}
    )


@app.get("/terminal", response_class=HTMLResponse)
async def terminal_page(request: Request):
    """Standalone terminal page"""
    return templates.TemplateResponse(
        "terminal.html",
        {"request": request, "title": "Takax Terminal"}
    )


@app.websocket("/ws/terminal")
async def websocket_terminal(websocket: WebSocket):
    """WebSocket endpoint for real-time terminal"""
    await websocket.accept()
    
    # Create terminal session
    terminal = CloudTerminal()
    session_id = ws_manager.create_session(websocket)
    
    try:
        # Send welcome message
        await websocket.send_json({
            "type": "system",
            "content": "🔗 Connected to Takax Terminal",
            "session_id": session_id
        })
        
        # Handle messages
        while True:
            data = await websocket.receive_json()
            await ws_manager.handle_message(session_id, data, terminal)
            
    except WebSocketDisconnect:
        ws_manager.close_session(session_id)
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "content": f"Error: {str(e)}"
        })
        ws_manager.close_session(session_id)


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for chat interface"""
    await websocket.accept()
    
    session_id = ws_manager.create_session(websocket, is_chat=True)
    
    try:
        # Send welcome
        await websocket.send_json({
            "type": "system",
            "content": "👋 Welcome to Takax! Describe the OS you want to create.",
            "session_id": session_id
        })
        
        # Chat loop
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "message":
                user_message = data.get("content", "")
                
                # Process message (simulated - in real implementation, use LLM)
                response = await process_chat_message(user_message)
                
                await websocket.send_json({
                    "type": "response",
                    "content": response["message"],
                    "analysis": response.get("analysis", {})
                })
                
            elif data.get("type") == "build":
                # Execute build
                await websocket.send_json({
                    "type": "system",
                    "content": "🔧 Starting build process..."
                })
                
                # Simulate build steps
                for step in ["Preparing environment", "Downloading base packages", 
                            "Configuring system", "Installing packages", "Finalizing"]:
                    await websocket.send_json({
                        "type": "progress",
                        "content": step
                    })
                    
                await websocket.send_json({
                    "type": "system",
                    "content": "✅ Build completed!"
                })
                
    except WebSocketDisconnect:
        ws_manager.close_session(session_id)
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "content": f"Error: {str(e)}"
        })


async def process_chat_message(message: str) -> dict:
    """Process chat message and generate response"""
    message_lower = message.lower()
    
    # Simple keyword-based processing
    response = {
        "message": "",
        "analysis": {}
    }
    
    # Detect build keywords
    build_keywords = ["create", "build", "make", "generate", "setup"]
    if any(kw in message_lower for kw in build_keywords):
        response["analysis"]["action"] = "build"
        
        # Detect distribution
        distros = ["debian", "ubuntu", "arch", "fedora", "alpine"]
        for distro in distros:
            if distro in message_lower:
                response["analysis"]["detected_distro"] = distro
                break
        else:
            response["analysis"]["detected_distro"] = "debian"
            
        # Detect components
        components = []
        if "python" in message_lower:
            components.append("python3")
        if "docker" in message_lower:
            components.append("docker")
        if "ssh" in message_lower:
            components.append("openssh-server")
        if "nginx" in message_lower:
            components.append("nginx")
            
        response["analysis"]["components"] = components
        
        # Generate build plan message
        distro = response["analysis"]["detected_distro"]
        response["message"] = f"🎯 **Build Plan**\n\n"
        response["message"] += f"**Distribution:** {distro.title()}\n"
        if components:
            response["message"] += f"**Components:** {', '.join(components)}\n"
        response["message"] += f"\nShould I start the build? (yes/no)"
        
    else:
        response["message"] = "🤔 I understand you want to create a Linux OS.\n\n"
        response["message"] += "Please tell me what you want, for example:\n"
        response["message"] += "• 'Create a minimal Debian with Python'\n"
        response["message"] += "• 'Build Ubuntu server with Docker'\n"
        response["message"] += "• 'Generate Arch Linux with SSH'"
        
    return response


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "takax-cloud"}


def run_server(host: str = "0.0.0.0", port: int = 8080, reload: bool = False):
    """Run the cloud server"""
    uvicorn.run(
        "cloud.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Takax Cloud Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind")
    parser.add_argument("--reload", action="store_true", help="Auto-reload on changes")
    
    args = parser.parse_args()
    run_server(args.host, args.port, args.reload)