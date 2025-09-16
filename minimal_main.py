"""Minimal FastAPI app for Render.com deployment with reduced memory footprint."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Global variable to track if routes are loaded
routes_loaded = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    global routes_loaded
    
    # Startup
    try:
        # Import in startup to avoid blocking initial health check
        from app.api.api_v1.api import api_router
        app.include_router(api_router, prefix="/api/v1")
        routes_loaded = True
        print("✅ API routes loaded successfully")
    except Exception as e:
        print(f"⚠️  Warning: Could not load full API routes: {e}")
        print("📊 Running in minimal mode - health check only")
    
    yield
    
    # Shutdown
    print("🔄 Application shutting down")

# Create app with lifespan handler
app = FastAPI(
    title="PLC Copilot Backend",
    description="A FastAPI backend for automating PLC programming and testing",
    version="1.0.0",
    lifespan=lifespan
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
    """Health check endpoint for Render deployment monitoring."""
    import time
    global routes_loaded
    return {
        "status": "healthy", 
        "service": "plc-copilot",
        "timestamp": int(time.time()),
        "version": "1.0.0",
        "routes_loaded": routes_loaded
    }

@app.get("/minimal")
async def minimal_check():
    """Minimal endpoint to verify service is responding."""
    return {"message": "Minimal service running", "endpoints": ["/", "/health", "/minimal"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)