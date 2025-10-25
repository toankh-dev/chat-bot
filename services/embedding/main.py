"""
Embedding Service using Sentence Transformers
Model: paraphrase-multilingual-MiniLM-L12-v2
"""

import os
import time
import logging
from typing import List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
import torch

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
MODEL_NAME = os.getenv("MODEL_NAME", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
DEVICE = os.getenv("DEVICE", "cpu")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "32"))

# Global model instance
model = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model on startup, cleanup on shutdown"""
    global model

    logger.info(f"Loading model: {MODEL_NAME}")
    logger.info(f"Device: {DEVICE}")

    start_time = time.time()

    # Load model
    model = SentenceTransformer(MODEL_NAME, device=DEVICE)

    # Set to evaluation mode
    model.eval()

    load_time = time.time() - start_time
    logger.info(f"Model loaded successfully in {load_time:.2f}s")
    logger.info(f"Embedding dimension: {model.get_sentence_embedding_dimension()}")

    yield

    # Cleanup
    logger.info("Shutting down embedding service")
    del model


# Initialize FastAPI app
app = FastAPI(
    title="Embedding Service",
    description="Sentence Transformers embedding API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class EmbedRequest(BaseModel):
    """Request model for embedding generation"""
    texts: List[str] = Field(..., description="List of texts to embed", min_items=1, max_items=1000)
    normalize: bool = Field(True, description="Whether to normalize embeddings")

    class Config:
        json_schema_extra = {
            "example": {
                "texts": ["Hello world", "こんにちは", "Xin chào"],
                "normalize": True
            }
        }


class EmbedResponse(BaseModel):
    """Response model for embedding generation"""
    embeddings: List[List[float]] = Field(..., description="List of embedding vectors")
    dimension: int = Field(..., description="Embedding dimension")
    model: str = Field(..., description="Model name")
    processing_time: float = Field(..., description="Processing time in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "embeddings": [[0.1, 0.2, 0.3]],
                "dimension": 384,
                "model": "paraphrase-multilingual-MiniLM-L12-v2",
                "processing_time": 0.05
            }
        }


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    model: str
    device: str
    dimension: int


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    return HealthResponse(
        status="healthy",
        model=MODEL_NAME,
        device=DEVICE,
        dimension=model.get_sentence_embedding_dimension()
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Embedding Service",
        "model": MODEL_NAME,
        "dimension": model.get_sentence_embedding_dimension() if model else None,
        "device": DEVICE,
        "status": "ready" if model else "loading"
    }


@app.post("/embed", response_model=EmbedResponse)
async def embed_texts(request: EmbedRequest):
    """
    Generate embeddings for a list of texts

    Args:
        request: EmbedRequest containing texts and options

    Returns:
        EmbedResponse with embeddings and metadata
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        start_time = time.time()

        # Generate embeddings
        with torch.no_grad():
            embeddings = model.encode(
                request.texts,
                batch_size=BATCH_SIZE,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=request.normalize
            )

        processing_time = time.time() - start_time

        # Convert to list
        embeddings_list = embeddings.tolist()

        logger.info(
            f"Generated embeddings for {len(request.texts)} texts "
            f"in {processing_time:.3f}s "
            f"({len(request.texts)/processing_time:.1f} texts/sec)"
        )

        return EmbedResponse(
            embeddings=embeddings_list,
            dimension=model.get_sentence_embedding_dimension(),
            model=MODEL_NAME,
            processing_time=processing_time
        )

    except Exception as e:
        logger.error(f"Error generating embeddings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")


@app.post("/embed/single")
async def embed_single_text(text: str):
    """
    Generate embedding for a single text (convenience endpoint)

    Args:
        text: Single text string

    Returns:
        Single embedding vector
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        with torch.no_grad():
            embedding = model.encode(
                [text],
                batch_size=1,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True
            )

        return {
            "embedding": embedding[0].tolist(),
            "dimension": model.get_sentence_embedding_dimension(),
            "text_length": len(text)
        }

    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")


@app.get("/model/info")
async def model_info():
    """Get model information"""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    return {
        "model_name": MODEL_NAME,
        "dimension": model.get_sentence_embedding_dimension(),
        "max_seq_length": model.max_seq_length,
        "device": str(model.device),
        "normalize_embeddings": True,
        "batch_size": BATCH_SIZE
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
