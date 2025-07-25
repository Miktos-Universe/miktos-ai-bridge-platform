#!/usr/bin/env python3
"""
Miktos AI Bridge Platform Server
Provides HTTP API for desktop app integration
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from main import MiktosPlatform


# Request models
class CommandRequest(BaseModel):
    command: str
    context: Optional[Dict[str, Any]] = None


class CameraRequest(BaseModel):
    position: list[float]
    target: list[float]


# Global platform instance
platform: Optional[MiktosPlatform] = None

# FastAPI app
app = FastAPI(
    title="Miktos AI Bridge Platform API",
    description="REST API for AI-driven 3D workflow automation",
    version="1.0.0"
)

# Enable CORS for desktop app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize the platform on startup"""
    global platform
    platform = MiktosPlatform()
    success = await platform.start()
    if not success:
        raise RuntimeError("Failed to start Miktos platform")
    
    # Start a session automatically
    await platform.start_session()
    logging.info("Miktos AI Bridge Platform API server started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global platform
    if platform:
        await platform.shutdown()
    logging.info("Miktos AI Bridge Platform API server stopped")


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Miktos AI Bridge Platform API", "version": "1.0.0"}


@app.get("/api/status")
async def get_status():
    """Get platform status"""
    if not platform:
        raise HTTPException(status_code=500, detail="Platform not initialized")
    
    status = await platform.get_status()
    return {"success": True, "data": status}


@app.get("/api/skills")
async def get_skills():
    """Get available skills"""
    if not platform or not platform.agent:
        raise HTTPException(status_code=500, detail="Platform not initialized")
    
    # Get skills from agent
    skills = []
    if platform.agent.skill_manager:
        skills = [skill.name for skill in platform.agent.skill_manager.skills.values()]
    
    return {"success": True, "data": skills}


@app.post("/api/execute")
async def execute_command(request: CommandRequest):
    """Execute a natural language command"""
    if not platform:
        raise HTTPException(status_code=500, detail="Platform not initialized")
    
    try:
        result = await platform.execute_command(request.command, request.context)
        return {"success": True, "data": result}
    
    except Exception as e:
        logging.error(f"Command execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/viewer/url")
async def get_viewer_url():
    """Get the 3D viewer URL"""
    if not platform or not platform.viewer:
        return {"success": False, "message": "Viewer not available"}
    
    # Try to start viewer if not running
    if platform.viewer and not hasattr(platform.viewer, 'is_running'):
        await platform.viewer.start()
    
    return {
        "success": True, 
        "data": {
            "url": "http://localhost:8082",
            "websocket": "ws://localhost:8083"
        }
    }


@app.post("/api/viewer/open")
async def open_viewer():
    """Open/start the 3D viewer"""
    if not platform or not platform.viewer:
        return {"success": False, "message": "Viewer not available"}
    
    try:
        await platform.viewer.start()
        return {"success": True, "message": "Viewer started successfully"}
    
    except Exception as e:
        logging.error(f"Failed to start viewer: {e}")
        return {"success": False, "message": str(e)}


@app.post("/api/viewer/camera")
async def set_camera(request: CameraRequest):
    """Set viewer camera position"""
    if not platform:
        raise HTTPException(status_code=500, detail="Platform not initialized")
    
    try:
        await platform.set_viewer_camera(request.position, request.target)
        return {"success": True, "message": "Camera position updated"}
    
    except Exception as e:
        logging.error(f"Failed to set camera: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/screenshot")
async def take_screenshot():
    """Take a screenshot of the 3D view"""
    if not platform:
        raise HTTPException(status_code=500, detail="Platform not initialized")
    
    try:
        screenshot = await platform.take_screenshot()
        return {"success": True, "data": {"screenshot": screenshot}}
    
    except Exception as e:
        logging.error(f"Failed to take screenshot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/suggestions")
async def get_suggestions(q: str = ""):
    """Get command suggestions"""
    if not platform:
        raise HTTPException(status_code=500, detail="Platform not initialized")
    
    try:
        suggestions = await platform.get_suggestions(q)
        return {"success": True, "data": suggestions}
    
    except Exception as e:
        logging.error(f"Failed to get suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
