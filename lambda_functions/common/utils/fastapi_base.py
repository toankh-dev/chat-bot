"""
Base FastAPI Application Factory
Shared configuration for all management Lambda functions
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
import time
import os

logger = logging.getLogger(__name__)


def create_management_app(
    title: str,
    description: str,
    version: str = "2.0.0",
    prefix: str = ""
) -> FastAPI:
    """
    Factory function to create FastAPI app for management Lambdas

    Args:
        title: API title
        description: API description
        version: API version
        prefix: URL prefix (e.g., "/api/v1")

    Returns:
        Configured FastAPI application
    """

    app = FastAPI(
        title=title,
        description=description,
        version=version,
        docs_url=f"{prefix}/docs" if prefix else "/docs",
        redoc_url=f"{prefix}/redoc" if prefix else "/redoc",
        openapi_url=f"{prefix}/openapi.json" if prefix else "/openapi.json"
    )

    # CORS Configuration
    cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()

        # Log request
        logger.info(f"→ {request.method} {request.url.path}")

        # Process request
        response = await call_next(request)

        # Log response
        process_time = (time.time() - start_time) * 1000
        logger.info(f"← {response.status_code} ({process_time:.2f}ms)")

        # Add custom headers
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"

        return response

    # Exception handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation errors"""
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "validation_error",
                "message": "Invalid request data",
                "details": exc.errors()
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle unexpected errors"""
        logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "internal_error",
                "message": "An unexpected error occurred",
                "details": str(exc) if os.getenv("DEBUG") == "true" else None
            }
        )

    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "service": title,
            "version": version
        }

    return app
