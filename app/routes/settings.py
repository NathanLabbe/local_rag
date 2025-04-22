# app/routes/settings.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.config import settings as app_settings
import os

router = APIRouter(
    prefix="/api/settings",
    tags=["settings"],
)

class SettingsUpdate(BaseModel):
    system_prompt: Optional[str] = None
    llm_model: Optional[str] = None

class SettingsResponse(BaseModel):
    system_prompt: Optional[str] = None
    llm_model: Optional[str] = None

@router.get("/", response_model=SettingsResponse)
async def get_settings():
    """Get current settings"""
    return {
        "system_prompt": app_settings.system_prompt or "",  # Convert None to empty string
        "llm_model": app_settings.ollama_model
    }

@router.post("/", response_model=SettingsResponse)
async def update_settings(settings_update: SettingsUpdate):
    """Update settings"""
    try:
        if settings_update.system_prompt is not None:
            # In a real application, this should modify environment variables or save to a database
            # For simplicity, we're just updating the settings object in memory
            app_settings.system_prompt = settings_update.system_prompt
            os.environ["SYSTEM_PROMPT"] = settings_update.system_prompt
        
        if settings_update.llm_model is not None:
            app_settings.ollama_model = settings_update.llm_model
            os.environ["OLLAMA_MODEL"] = settings_update.llm_model
        
        return {
            "system_prompt": app_settings.system_prompt or "",  # Convert None to empty string
            "llm_model": app_settings.ollama_model
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")