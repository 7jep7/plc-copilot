"""API v1 router configuration."""

from fastapi import APIRouter

from app.api.api_v1.endpoints import plc_code, digital_twin, ai, code_library, context

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    plc_code.router, 
    prefix="/plc", 
    tags=["plc-code"]
)
api_router.include_router(
    digital_twin.router, 
    prefix="/digital-twin", 
    tags=["digital-twin"]
)

# AI endpoints
api_router.include_router(
    ai.router,
    prefix="/ai",
    tags=["ai"]
)

# Context API - New unified endpoint
api_router.include_router(
    context.router,
    prefix="/context",
    tags=["context"]
)

# Code library endpoints
api_router.include_router(
    code_library.router,
    prefix="/library",
    tags=["code-library"]
)