"""API v1 router configuration."""

from fastapi import APIRouter

from app.api.api_v1.endpoints import context

api_router = APIRouter()

# Context API - Main endpoint using OpenAI Assistant
api_router.include_router(
    context.router,
    prefix="/context",
    tags=["context"]
)