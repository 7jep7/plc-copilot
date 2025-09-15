"""API v1 router configuration."""

from fastapi import APIRouter

from app.api.api_v1.endpoints import documents, plc_code, digital_twin

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    documents.router, 
    prefix="/documents", 
    tags=["documents"]
)
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