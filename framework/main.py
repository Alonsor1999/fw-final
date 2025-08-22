"""
Framework MVP - Aplicación principal FastAPI
"""
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from framework.config import settings
from framework.core.orchestrator import Orchestrator
from framework.api.routes import robots, modules, health, metrics
from framework.api.dependencies import get_orchestrator, set_orchestrator

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global orchestrator instance
orchestrator: Orchestrator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager para la aplicación"""
    global orchestrator
    
    # Startup
    logger.info("Starting Framework MVP...")
    
    try:
        # Initialize orchestrator
        orchestrator = Orchestrator()
        await orchestrator.initialize()
        
        # Set orchestrator in dependencies
        set_orchestrator(orchestrator)
        
        logger.info("Framework MVP started successfully")
        yield
        
    except Exception as e:
        logger.error(f"Failed to start Framework MVP: {e}")
        raise
    
    finally:
        # Shutdown
        logger.info("Shutting down Framework MVP...")
        
        if orchestrator:
            await orchestrator.close()
        
        logger.info("Framework MVP shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Framework MVP",
    description="Sistema de Automatización Robótica - Versión MVP",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(robots.router, prefix="/api/v1/robots", tags=["robots"])
app.include_router(modules.router, prefix="/api/v1/modules", tags=["modules"])
app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["metrics"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Framework MVP - Sistema de Automatización Robótica",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        if orchestrator:
            system_health = await orchestrator.get_system_health()
            return {
                "status": "healthy" if system_health["overall_status"] == "HEALTHY" else "degraded",
                "timestamp": system_health["last_check"],
                "components": {
                    "database": system_health["database"],
                    "cache": system_health["cache"],
                    "modules": system_health["modules"]
                }
            }
        else:
            return {"status": "initializing", "timestamp": "2024-12-14T10:00:00Z"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "timestamp": "2024-12-14T10:00:00Z"
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "framework.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
