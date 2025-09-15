"""Minimal FastAPI app for Render.com deployment with reduced memory footprint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Create app with minimal configuration
app = FastAPI(
    title="PLC Copilot Backend",
    description="A FastAPI backend for automating PLC programming and testing",
    version="1.0.0",
)

# Add CORS middleware with permissive settings for free tier
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "PLC Copilot Backend", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

# Lazy import and include routes only when needed
@app.on_event("startup")
async def startup_event():
    """Load heavy imports and routes only after startup."""
    try:
        from app.api.api_v1.api import api_router
        app.include_router(api_router, prefix="/api/v1")
    except Exception as e:
        print(f"Warning: Could not load API routes: {e}")
        # Continue with minimal functionality

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)