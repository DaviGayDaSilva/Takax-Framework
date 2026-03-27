#!/usr/bin/env python3
"""
API Routes - REST API endpoints for Takax Cloud
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import json
from pathlib import Path


router = APIRouter()


# In-memory storage (use database in production)
projects_storage = {}
builds_storage = {}


# Pydantic models
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    analysis: Dict[str, Any]
    session_id: str


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    created_at: str
    updated_at: str
    status: str


class BuildRequest(BaseModel):
    project_id: Optional[str] = None
    description: str
    config: Optional[Dict[str, Any]] = None


class BuildResponse(BaseModel):
    id: str
    project_id: Optional[str]
    status: str
    created_at: str
    output_path: Optional[str] = None
    logs: List[str] = []


class TemplateList(BaseModel):
    templates: List[Dict[str, str]]


# Chat endpoint
@router.post("/chat", response_model=ChatResponse)
async def send_chat_message(message: ChatMessage):
    """Send a chat message and get response"""
    
    session_id = message.session_id or str(uuid.uuid4())
    
    # Simple keyword-based processing (replace with LLM in production)
    message_lower = message.message.lower()
    analysis = {}
    response_text = ""
    
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
        else:
            analysis["detected_distro"] = "debian"
            
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
        
        # Response
        distro = analysis["detected_distro"]
        response_text = f"🎯 **Build Plan**\n\n"
        response_text += f"**Distribution:** {distro.title()}\n"
        if components:
            response_text += f"**Components:** {', '.join(components)}\n"
        response_text += f"\nSay 'yes' to start building or describe more requirements."
        
    else:
        response_text = "🤔 I understand you want to create a Linux OS.\n\n"
        response_text += "Tell me what you want, for example:\n"
        response_text += "• 'Create minimal Debian with Python'\n"
        response_text += "• 'Build Ubuntu with Docker and SSH'"
        
    return ChatResponse(
        response=response_text,
        analysis=analysis,
        session_id=session_id
    )


# Projects endpoints
@router.get("/projects", response_model=List[ProjectResponse])
async def list_projects():
    """List all projects"""
    return [
        ProjectResponse(
            id=pid,
            name=pdata["name"],
            description=pdata.get("description"),
            created_at=pdata["created_at"],
            updated_at=pdata.get("updated_at", pdata["created_at"]),
            status=pdata.get("status", "created")
        )
        for pid, pdata in projects_storage.items()
    ]


@router.post("/projects", response_model=ProjectResponse)
async def create_project(project: ProjectCreate):
    """Create a new project"""
    project_id = str(uuid.uuid4())[:8]
    now = datetime.now().isoformat()
    
    project_data = {
        "name": project.name,
        "description": project.description or "",
        "config": project.config or {},
        "created_at": now,
        "updated_at": now,
        "status": "created"
    }
    
    projects_storage[project_id] = project_data
    
    return ProjectResponse(
        id=project_id,
        name=project.name,
        description=project.description,
        created_at=now,
        updated_at=now,
        status="created"
    )


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str):
    """Get project details"""
    if project_id not in projects_storage:
        raise HTTPException(status_code=404, detail="Project not found")
        
    pdata = projects_storage[project_id]
    
    return ProjectResponse(
        id=project_id,
        name=pdata["name"],
        description=pdata.get("description"),
        created_at=pdata["created_at"],
        updated_at=pdata.get("updated_at", pdata["created_at"]),
        status=pdata.get("status", "created")
    )


@router.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project"""
    if project_id not in projects_storage:
        raise HTTPException(status_code=404, detail="Project not found")
        
    del projects_storage[project_id]
    return {"message": "Project deleted"}


# Build endpoints
@router.post("/build", response_model=BuildResponse)
async def start_build(build_request: BuildRequest):
    """Start a new build"""
    build_id = str(uuid.uuid4())[:8]
    now = datetime.now().isoformat()
    
    # Analyze the description
    desc_lower = build_request.description.lower()
    analysis = {
        "detected_distro": "debian",
        "components": []
    }
    
    # Detect distro
    distros = ["debian", "ubuntu", "arch", "fedora", "alpine"]
    for distro in distros:
        if distro in desc_lower:
            analysis["detected_distro"] = distro
            break
            
    # Detect components
    if "python" in desc_lower:
        analysis["components"].append("python3")
    if "docker" in desc_lower:
        analysis["components"].append("docker")
    if "ssh" in desc_lower:
        analysis["components"].append("openssh-server")
    if "nginx" in desc_lower:
        analysis["components"].append("nginx")
        
    build_data = {
        "project_id": build_request.project_id,
        "description": build_request.description,
        "config": build_request.config or {},
        "analysis": analysis,
        "status": "pending",
        "created_at": now,
        "output_path": None,
        "logs": []
    }
    
    builds_storage[build_id] = build_data
    
    # In a real implementation, trigger the build asynchronously
    # For now, just return the build info
    
    return BuildResponse(
        id=build_id,
        project_id=build_request.project_id,
        status="pending",
        created_at=now,
        output_path=None,
        logs=[]
    )


@router.get("/build/{build_id}/status")
async def get_build_status(build_id: str):
    """Get build status"""
    if build_id not in builds_storage:
        raise HTTPException(status_code=404, detail="Build not found")
        
    build = builds_storage[build_id]
    
    return {
        "id": build_id,
        "status": build["status"],
        "created_at": build["created_at"],
        "output_path": build["output_path"],
        "logs": build["logs"]
    }


@router.get("/builds")
async def list_builds():
    """List all builds"""
    return [
        {
            "id": bid,
            "project_id": bdata.get("project_id"),
            "description": bdata["description"],
            "status": bdata["status"],
            "created_at": bdata["created_at"]
        }
        for bid, bdata in builds_storage.items()
    ]


# Templates endpoint
@router.get("/templates", response_model=TemplateList)
async def list_templates():
    """List available OS templates"""
    templates = [
        {"name": "debian-minimal", "description": "Minimal Debian base system"},
        {"name": "ubuntu-server", "description": "Ubuntu Server with common tools"},
        {"name": "debian-python", "description": "Debian with Python development"},
        {"name": "alpine-minimal", "description": "Ultra-minimal Alpine Linux"},
        {"name": "arch-linux", "description": "Arch Linux base system"},
        {"name": "fedora-server", "description": "Fedora Server edition"},
        {"name": "docker-host", "description": "System with Docker support"},
        {"name": "dev-environment", "description": "Full development environment"},
        {"name": "web-server", "description": "Web hosting server with Nginx"},
        {"name": "security-hardened", "description": "Security-hardened minimal system"},
    ]
    
    return TemplateList(templates=templates)


# System info endpoint
@router.get("/info")
async def system_info():
    """Get system information"""
    return {
        "name": "Takax Cloud",
        "version": "1.0.0",
        "description": "Create Linux OS via chat",
        "features": [
            "Natural language OS creation",
            "Real-time terminal",
            "Project management",
            "Template system",
            "Build history"
        ]
    }