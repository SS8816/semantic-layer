"""
FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, auth, metadata, tables
from app.api.relationships_api import router as relationships_router
from app.api.enriched_tables_api import router as enriched_tables_router
from app.config import settings
from app.middleware.auth_middleware import AuthMiddleware
from app.utils.logger import app_logger as logger

# Create FastAPI app
app = FastAPI(
    title="Metadata Explorer API",
    description="API for exploring and managing table metadata with geographic detection and AI-generated aliases",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://10.170.92.62:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AuthMiddleware)
# Include routers
app.include_router(auth.router)
app.include_router(tables.router)
app.include_router(metadata.router)
app.include_router(admin.router)
app.include_router(relationships_router)
app.include_router(enriched_tables_router)


@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("=" * 60)
    logger.info("Starting Metadata Explorer API")
    logger.info(f"Version: 1.0.0")
    logger.info(f"Environment: {settings.log_level}")
    logger.info(f"Starburst Host: {settings.starburst_host}")
    logger.info(f"DynamoDB Region: {settings.aws_region}")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("Shutting down Metadata Explorer API")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Metadata Explorer API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level=settings.log_level.lower(),
    )
