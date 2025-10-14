"""
Main FastAPI application for UCIP - Urban Carbon Intelligence Platform

🚀 Quick Access:
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- Dashboard: http://localhost:3000
"""
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from pydantic import BaseModel

from routes import emissions, hotspots, policy, predictions


# Pydantic models
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    # Startup
    logger.info("Starting UCIP API...")
    logger.info("🚀 UCIP API is now running!")
    logger.info("📚 API Documentation: http://localhost:8000/docs")
    logger.info("🏥 Health Check: http://localhost:8000/health")
    logger.info("📊 Dashboard: http://localhost:3000")
    # Initialize connections, load models, etc.
    yield
    # Shutdown
    logger.info("Shutting down UCIP API...")


# Create FastAPI app
app = FastAPI(
    title="Urban Carbon Intelligence Platform API",
    description="AI-powered carbon monitoring and policy simulation for Pennsylvania",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="0.1.0"
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Urban Carbon Intelligence Platform API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }


# Include routers
app.include_router(emissions.router, prefix="/api/v1/emissions", tags=["Emissions"])
app.include_router(hotspots.router, prefix="/api/v1/hotspots", tags=["Hotspots"])
app.include_router(policy.router, prefix="/api/v1/policy", tags=["Policy"])
app.include_router(predictions.router, prefix="/api/v1/predictions", tags=["Predictions"])


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("API_PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )

