"""
Web Interface for Young Aletheia

This module provides the REST API and web interface for Young Aletheia,
allowing parents to interact with the child persona through a web browser.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Request, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import json
from datetime import datetime
import asyncio
import random
from pathlib import Path

class MessageRequest(BaseModel):
    """Request model for sending messages to the child"""
    content: str
    language: Optional[str] = "english"
    parent_name: Optional[str] = None

class MessageResponse(BaseModel):
    """Response model for child messages"""
    content: str
    timestamp: str
    language: str
    sleep_status: bool

class ChildStatusResponse(BaseModel):
    """Response model for child status"""
    name: str
    age: int
    mood: Dict[str, float]
    sleep_status: bool
    learning_stats: Dict[str, Any]
    recent_learnings: List[Dict[str, Any]]
    last_interaction: Optional[str] = None

class YoungAletheiaRouter:
    """Handles API routes for the Young Aletheia interface"""
    
    def __init__(self, app, persona_manager, dev_model, message_generator, learning_engine):
        """
        Initialize the router
        
        Args:
            app: FastAPI application
            persona_manager: The persona manager instance
            dev_model: The developmental model instance
            message_generator: The message generator instance
            learning_engine: The learning engine instance
        """
        self.app = app
        self.persona_manager = persona_manager
        self.dev_model = dev_model
        self.message_generator = message_generator
        self.learning_engine = learning_engine
        
        # Create router
        self.router = APIRouter()
        self.setup_routes()
        
        # WebSocket connections
        self.active_connections: List[WebSocket] = []
        
        # Setup templates
        self.templates = Jinja2Templates(directory=Path(__file__).resolve().parent / "templates")
        
        # Setup static files
        static_dir = Path(__file__).resolve().parent / "static"
        static_dir.mkdir(exist_ok=True)
        self.app.mount("/young/static", StaticFiles(directory=static_dir), name="young_static")
    
    def setup_routes(self):
        """Setup all routes for the Young Aletheia interface"""
        # API routes
        self.router.post("/message", response_model=MessageResponse)(self.send_message)
        self.router.get("/status", response_model=ChildStatusResponse)(self.get_child_status)
        self.router.post("/update", response_model=ChildStatusResponse)(self.update_child)
        
        # WebSocket route
        self.router.websocket("/ws")(self.websocket_endpoint)
        
        # Web interface routes
        self.router.get("/", response_class=HTMLResponse)(self.web_interface)
        self.router.get("/customization", response_class=HTMLResponse)(self.customization_interface)
        
        # Register router with app
        self.app.include_router(self.router, prefix="/young", tags=["Young Aletheia"])
    
    async def send_message(self, request: MessageRequest) -> MessageResponse:
        """
        Handle parent message to child
        
        Args:
            request: Message request
            
        Returns:
            Message response
        """
        try:
            # Check if child is sleeping
            sleep_status = self.persona_manager.is_sleeping()
            
            # Process parent name if provided
            if request.parent_name:
                parent_role = "mom" if request.parent_name.lower() in ["mom", "mama", "mother", "mommy"] else "dad"
                self.persona_manager.persona.parent_relationship["parent_names"][parent_role] = request.parent_name
                self.persona_manager.save_persona()
            
            # Prepare context with parent message
            context = {
                "parent_message": request.content,
                "language": request.language
            }
            
            # Generate child's response
            response = self.message_generator.generate_message(context, "response")
            
            # Process interaction for developmental model
            self.dev_model.process_interaction("conversation", request.content, 0.7)
            
            # Return formatted response
            return MessageResponse(
                content=response,
                timestamp=datetime.now().isoformat(),
                language=request.language,
                sleep_status=sleep_status
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_child_status(self) -> ChildStatusResponse:
        """
        Get current status of the child
        
        Returns:
            Child status response
        """
        try:
            persona = self.persona_manager.persona
            
            # Prepare learning stats
            dev_state = self.dev_model.state
            learning_stats = {
                "vocabulary_size": dev_state["language_development"]["vocabulary_size"],
                "attention_span": dev_state["cognitive_development"]["attention_span_minutes"],
                "total_learnings": len(persona.recent_learnings),
                "favorite_topics": dev_state["learning_stats"].get("favorite_topics", [])[:3]
            }
            
            # Get last interaction if available
            last_interaction = None
            if persona.parent_relationship["recent_interactions"]:
                last_interaction = persona.parent_relationship["recent_interactions"][-1]["timestamp"]
            
            return ChildStatusResponse(
                name=persona.name,
                age=persona.age,
                mood=persona.emotional_state,
                sleep_status=self.persona_manager.is_sleeping(),
                learning_stats=learning_stats,
                recent_learnings=persona.recent_learnings[:5],
                last_interaction=last_interaction
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def update_child(self, request: Dict[str, Any]) -> ChildStatusResponse:
        """
        Update child parameters
        
        Args:
            request: Update data
            
        Returns:
            Updated child status
        """
        try:
            # Update persona with provided values
            self.persona_manager.update_persona(request)
            
            # Return updated status
            return await self.get_child_status()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def websocket_endpoint(self, websocket: WebSocket):
        """
        WebSocket endpoint for real-time communication
        
        Args:
            websocket: WebSocket connection
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        
        try:
            while True:
                # Receive and process messages
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Handle different message types
                if message_data["type"] == "parent_message":
                    # Process parent message
                    context = {
                        "parent_message": message_data["content"],
                        "language": message_data.get("language", "english")
                    }
                    
                    # Generate response
                    response = self.message_generator.generate_message(context, "response")
                    
                    # Send response
                    await websocket.send_json({
                        "type": "child_response",
                        "content": response,
                        "timestamp": datetime.now().isoformat(),
                        "sleep_status": self.persona_manager.is_sleeping()
                    })
                
                elif message_data["type"] == "status_request":
                    # Send current status
                    status = await self.get_child_status()
                    await websocket.send_json({
                        "type": "status_update",
                        "status": status.dict()
                    })
        
        except WebSocketDisconnect:
            self.active_connections.remove(websocket)
        except Exception as e:
            print(f"WebSocket error: {e}")
            try:
                self.active_connections.remove(websocket)
            except:
                pass
    
    async def web_interface(self, request: Request) -> HTMLResponse:
        """
        Render the web interface for interaction
        
        Args:
            request: HTTP request
            
        Returns:
            HTML response
        """
        persona = self.persona_manager.persona
        status = await self.get_child_status()
        
        return self.templates.TemplateResponse(
            "young_interface.html",
            {
                "request": request,
                "persona": persona,
                "status": status,
                "sleep_status": status.sleep_status
            }
        )
    
    async def customization_interface(self, request: Request) -> HTMLResponse:
        """
        Render the customization interface
        
        Args:
            request: HTTP request
            
        Returns:
            HTML response
        """
        persona = self.persona_manager.persona
        
        return self.templates.TemplateResponse(
            "customization.html",
            {
                "request": request,
                "persona": persona.dict()
            }
        )
    
    async def broadcast_message(self, message: Dict[str, Any]):
        """
        Broadcast message to all connected WebSocket clients
        
        Args:
            message: Message to broadcast
        """
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                # Remove failed connections
                try:
                    self.active_connections.remove(connection)
                except:
                    pass