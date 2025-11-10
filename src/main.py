"""
FastAPI application entry point.

This module initializes the FastAPI application with all necessary configurations,
middleware, and routers for local development and Lambda deployment.
"""

import sys
import os

# Add src directory to Python path for direct imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from core.config import settings
from core.logger import logger
from core.errors import BaseAppException
import time

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI Backend System with Clean Architecture",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID Middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add unique request ID to each request."""
    request_id = request.headers.get("X-Request-ID", f"req_{int(time.time() * 1000)}")
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    return response


# Timing Middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)

    return response


# Exception Handlers
@app.exception_handler(BaseAppException)
async def app_exception_handler(request: Request, exc: BaseAppException):
    """Handle custom application exceptions."""
    logger.error(
        f"Application error: {exc.error_code} - {exc.message}",
        extra={"request_id": request.state.request_id, "details": exc.details}
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    logger.warning(
        f"Validation error: {str(exc)}",
        extra={"request_id": request.state.request_id}
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": exc.errors()
            }
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(
        f"Unexpected error: {str(exc)}",
        extra={"request_id": request.state.request_id},
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": {"error": str(exc)} if settings.DEBUG else {}
            }
        }
    )


# Health Check Endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns:
        dict: Health status
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }


# Root Endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information.

    Returns:
        dict: API information
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs" if settings.DEBUG else "Documentation disabled in production",
        "health": "/health"
    }


# Startup Event
@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} starting up...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")

    # Initialize database connections
    # from infrastructure.postgresql.pg_client import get_postgresql_client
    # pg_client = get_postgresql_client()
    # await pg_client.create_tables()  # Create tables if they don't exist

    logger.info("Application startup complete")


# Shutdown Event
@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info(f"{settings.APP_NAME} shutting down...")

    # Close database connections
    # from infrastructure.postgresql.pg_client import get_postgresql_client
    # pg_client = get_postgresql_client()
    # await pg_client.close()

    logger.info("Application shutdown complete")


# Import and include routers

from api.routers.group_routes import router as group_router
from api.routers.auth_routes import router as auth_router
from api.routers.user_routes import router as user_router
from api.routers.chatbot_routes import router as chatbot_router
from api.routers.conversation_routes import router as conversation_router
from api.routers.document_routes import router as document_router
from api.routers.ai_routes import router as ai_router
from api.routers.gitlab_routes import router as gitlab_router

app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(user_router, prefix="/api/v1/users", tags=["Users"])
app.include_router(group_router, prefix="/api/v1/groups", tags=["Groups"])
app.include_router(chatbot_router, prefix="/api/v1/chatbots", tags=["Chatbots"])
app.include_router(conversation_router, prefix="/api/v1/conversations", tags=["Conversations"])
app.include_router(document_router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(ai_router, prefix="/api/v1/ai", tags=["AI Services"])
app.include_router(gitlab_router, prefix="/api/v1/gitlab", tags=["GitLab Integration"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
