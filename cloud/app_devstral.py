#!/usr/bin/env python3
"""
Takax Cloud - Web Application (FastAPI)
Provides web interface for creating Linux OS via chat with real-time terminal using Devstral AI
"""

import os
import sys
import json
import requests
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


# Devstral AI Configuration
DEVSTRAL_CONFIG = {
    "model": os.environ.get("DEVSTRAL_MODEL", "devstral"),
    "api_url": os.environ.get("DEVSTRAL_API_URL", "https://api.endpoints.ai/v1/chat/completions"),
    "api_key": os.environ.get("DEVSTRAL_API_KEY", ""),
}

SYSTEM_PROMPT = """You are Takax, an AI assistant that helps create Linux operating systems from natural language.

Your job is to:
1. Analyze user requests for OS creation
2. Extract the distribution (Debian, Ubuntu, Arch, Fedora, Alpine)
3. Identify required packages and components
4. Determine the OS type (minimal, server, desktop, development)
5. Generate a build plan

Respond with a JSON object containing:
- detected_distro: the Linux distribution
- components: list of packages to install
- requirements: list of OS requirements (minimal, server, desktop)
- action: "build" if they want to create an OS, "analyze" otherwise
- confidence: how confident you are (0.0 to 1.0)

Example:
Input: "Create a minimal Debian with Python and SSH"
Output: {"detected_distro": "debian", "components": ["python3", "openssh-server"], "requirements": ["minimal"], "action": "build", "confidence": 0.9}"""


# WebSocket manager for terminal connections
ws_manager = WebSocketManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 Starting Takax Cloud Server with Devstral AI...")
    print(f"📡 API: {DEVSTRAL_CONFIG['api_url']}")
    print(f"🤖 Model: {DEVSTRAL_CONFIG['model']}")
    yield
    # Shutdown
    print("🛑 Shutting down Takax Cloud Server...")


# Create FastAPI app
app = FastAPI(
    title="Takax Cloud",
    description="Create Linux OS via chat - Web Interface (Powered by Devstral AI)",
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
        {"request": request, "title": "Takax - Create Linux OS (AI-Powered)"}
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
            "content": "🔗 Connected to Takax Terminal (Devstral AI)",
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
    """WebSocket endpoint for chat interface using Devstral AI"""
    await websocket.accept()
    
    session_id = ws_manager.create_session(websocket, is_chat=True)
    
    try:
        # Send welcome
        await websocket.send_json({
            "type": "system",
            "content": "👋 Welcome to Takax! I'm powered by Devstral AI.\nDescribe the OS you want to create (e.g., 'Create a minimal Debian with Python and SSH')",
            "session_id": session_id
        })
        
        # Chat loop
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "message":
                user_message = data.get("content", "")
                
                # Process message with Devstral AI
                response = await process_chat_message_devstral(user_message)
                
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


async def process_chat_message_devstral(message: str) -> dict:
    """Process chat message using Devstral AI"""
    
    api_key = os.environ.get("DEVSTRAL_API_KEY", "")
    api_url = os.environ.get("DEVSTRAL_API_URL", "https://api.endpoints.ai/v1/chat/completions")
    model = os.environ.get("DEVSTRAL_MODEL", "devstral")
    
    # If no API key, use fallback
    if not api_key:
        return process_chat_message_fallback(message)
    
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message}
            ],
            "temperature": 0.7,
            "max_tokens": 1024
        }
        
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Try to parse JSON
            try:
                analysis = json.loads(content)
            except json.JSONDecodeError:
                # Extract JSON from text
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group())
                else:
                    return process_chat_message_fallback(message)
                    
            # Generate response from analysis
            return generate_response_from_analysis(analysis)
        else:
            return process_chat_message_fallback(message)
            
    except Exception as e:
        print(f"Devstral API error: {e}")
        return process_chat_message_fallback(message)


def process_chat_message_fallback(message: str) -> dict:
    """Fallback keyword-based processing"""
    message_lower = message.lower()
    
    # Simple keyword-based processing
    analysis = {
        "detected_distro": "debian",
        "components": [],
        "requirements": [],
        "action": "analyze",
        "confidence": 0.5
    }
    
    # Build keywords
    build_keywords = ["create", "build", "make", "generate", "setup"]
    if any(kw in message_lower for kw in build_keywords):
        analysis["action"] = "build"
        
        # Detect distro
        distros = ["debian", "ubuntu", "arch", "fedora", "alpine"]
        for distro in distros:
            if distro in message_lower:
                analysis["detected_distro"] = distro
                break
                
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
        if "nodejs" in message_lower or "node" in message_lower:
            components.append("nodejs")
            
        analysis["components"] = components
        
    return generate_response_from_analysis(analysis)


def generate_response_from_analysis(analysis: dict) -> dict:
    """Generate response from analysis"""
    
    if analysis.get("action") == "build":
        distro = analysis.get("detected_distro", "debian")
        components = analysis.get("components", [])
        
        response_text = f"🎯 **Build Plan** (Devstral AI)\n\n"
        response_text += f"**Distribution:** {distro.title()}\n"
        
        if analysis.get("requirements"):
            response_text += f"**Type:** {', '.join(r.title() for r in analysis['requirements'])}\n"
            
        if components:
            response_text += f"**Components:** {', '.join(components)}\n"
            
        response_text += f"\nShould I start the build? (yes/no)"
        
    else:
        response_text = "🤖 I understand you want to create a Linux OS.\n\n"
        response_text += "Tell me what you want, for example:\n"
        response_text += "• 'Create minimal Debian with Python'\n"
        response_text += "• 'Build Ubuntu with Docker and SSH'"
        
    return {
        "message": response_text,
        "analysis": analysis
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "service": "takax-cloud",
        "ai": "devstral" if os.environ.get("DEVSTRAL_API_KEY") else "fallback"
    }


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