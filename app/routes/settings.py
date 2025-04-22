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
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None

class SettingsResponse(BaseModel):
    system_prompt: Optional[str] = None
    llm_model: Optional[str] = None
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 2000

@router.get("/", response_model=SettingsResponse)
async def get_settings():
    """Get current settings"""
    return {
        "system_prompt": app_settings.system_prompt or "",  # Convert None to empty string
        "llm_model": app_settings.ollama_model,
        "temperature": app_settings.temperature,
        "top_p": app_settings.top_p,
        "max_tokens": app_settings.max_tokens
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

         # New parameter updates
        if settings_update.temperature is not None:
            app_settings.temperature = settings_update.temperature
            os.environ["TEMPERATURE"] = str(settings_update.temperature)
        
        if settings_update.top_p is not None:
            app_settings.top_p = settings_update.top_p
            os.environ["TOP_P"] = str(settings_update.top_p)
        
        if settings_update.max_tokens is not None:
            app_settings.max_tokens = settings_update.max_tokens
            os.environ["MAX_TOKENS"] = str(settings_update.max_tokens)
        
        return {
            "system_prompt": app_settings.system_prompt or "",  # Convert None to empty string
            "llm_model": app_settings.ollama_model,
            "temperature": app_settings.temperature,
            "top_p": app_settings.top_p,
            "max_tokens": app_settings.max_tokens
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")