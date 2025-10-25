"""
LLM Service using StableLM-Instruct-7B
Model: stabilityai/japanese-stablelm-instruct-alpha-7b-v2
"""

import os
import time
import logging
from typing import Optional, List, Dict
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import torch

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
MODEL_NAME = os.getenv("MODEL_NAME", "stabilityai/japanese-stablelm-instruct-alpha-7b-v2")
DEVICE = os.getenv("DEVICE", "cpu")
LOAD_IN_4BIT = os.getenv("LOAD_IN_4BIT", "true").lower() == "true"
MAX_NEW_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "512"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
TOP_P = float(os.getenv("TOP_P", "0.9"))

# Global model and tokenizer
model = None
tokenizer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model on startup, cleanup on shutdown"""
    global model, tokenizer

    logger.info(f"Loading model: {MODEL_NAME}")
    logger.info(f"Device: {DEVICE}")
    logger.info(f"4-bit quantization: {LOAD_IN_4BIT}")

    start_time = time.time()

    try:
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

        # Configure quantization if enabled
        if LOAD_IN_4BIT and DEVICE != "cpu":
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4"
            )
            logger.info("Loading model with 4-bit quantization")
        else:
            quantization_config = None
            logger.info("Loading model in full precision")

        # Load model
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            quantization_config=quantization_config,
            device_map="auto" if DEVICE != "cpu" else None,
            torch_dtype=torch.float16 if DEVICE != "cpu" else torch.float32,
            trust_remote_code=True
        )

        # Move to CPU if needed
        if DEVICE == "cpu":
            model = model.to("cpu")

        # Set to evaluation mode
        model.eval()

        load_time = time.time() - start_time
        logger.info(f"Model loaded successfully in {load_time:.2f}s")

        # Log model info
        if hasattr(model, 'num_parameters'):
            logger.info(f"Model parameters: {model.num_parameters():,}")

    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        raise

    yield

    # Cleanup
    logger.info("Shutting down LLM service")
    del model
    del tokenizer


# Initialize FastAPI app
app = FastAPI(
    title="LLM Service",
    description="StableLM text generation API",
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
class GenerateRequest(BaseModel):
    """Request model for text generation"""
    prompt: str = Field(..., description="Input prompt", min_length=1)
    max_new_tokens: Optional[int] = Field(MAX_NEW_TOKENS, description="Maximum tokens to generate", ge=1, le=2048)
    temperature: Optional[float] = Field(TEMPERATURE, description="Sampling temperature", ge=0.0, le=2.0)
    top_p: Optional[float] = Field(TOP_P, description="Nucleus sampling parameter", ge=0.0, le=1.0)
    top_k: Optional[int] = Field(50, description="Top-k sampling parameter", ge=1, le=100)
    do_sample: Optional[bool] = Field(True, description="Whether to use sampling")
    num_return_sequences: Optional[int] = Field(1, description="Number of sequences to generate", ge=1, le=5)

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "What are the main features of the login system?",
                "max_new_tokens": 256,
                "temperature": 0.7,
                "top_p": 0.9
            }
        }


class GenerateResponse(BaseModel):
    """Response model for text generation"""
    generated_text: str = Field(..., description="Generated text")
    prompt: str = Field(..., description="Original prompt")
    tokens_generated: int = Field(..., description="Number of tokens generated")
    processing_time: float = Field(..., description="Processing time in seconds")
    model: str = Field(..., description="Model name")


class ChatMessage(BaseModel):
    """Chat message model"""
    role: str = Field(..., description="Message role: system, user, or assistant")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Request model for chat completion"""
    messages: List[ChatMessage] = Field(..., description="Conversation history", min_items=1)
    max_new_tokens: Optional[int] = Field(MAX_NEW_TOKENS, ge=1, le=2048)
    temperature: Optional[float] = Field(TEMPERATURE, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(TOP_P, ge=0.0, le=1.0)

    class Config:
        json_schema_extra = {
            "example": {
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Explain the login bug."}
                ],
                "max_new_tokens": 256,
                "temperature": 0.7
            }
        }


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    model: str
    device: str
    quantization: str


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    return HealthResponse(
        status="healthy",
        model=MODEL_NAME,
        device=str(model.device) if hasattr(model, 'device') else DEVICE,
        quantization="4-bit" if LOAD_IN_4BIT else "full"
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "LLM Service",
        "model": MODEL_NAME,
        "device": DEVICE,
        "quantization": "4-bit" if LOAD_IN_4BIT else "full",
        "status": "ready" if model and tokenizer else "loading"
    }


@app.post("/generate", response_model=GenerateResponse)
async def generate_text(request: GenerateRequest):
    """
    Generate text based on a prompt

    Args:
        request: GenerateRequest with prompt and generation parameters

    Returns:
        GenerateResponse with generated text and metadata
    """
    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        start_time = time.time()

        # Tokenize input
        inputs = tokenizer(request.prompt, return_tensors="pt")
        inputs = {k: v.to(model.device) for k, v in inputs.items()}

        # Generate
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=request.max_new_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                top_k=request.top_k,
                do_sample=request.do_sample,
                num_return_sequences=request.num_return_sequences,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id
            )

        # Decode output
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Remove prompt from output
        if generated_text.startswith(request.prompt):
            generated_text = generated_text[len(request.prompt):].strip()

        processing_time = time.time() - start_time
        tokens_generated = len(outputs[0]) - len(inputs['input_ids'][0])

        logger.info(
            f"Generated {tokens_generated} tokens in {processing_time:.2f}s "
            f"({tokens_generated/processing_time:.1f} tokens/sec)"
        )

        return GenerateResponse(
            generated_text=generated_text,
            prompt=request.prompt,
            tokens_generated=tokens_generated,
            processing_time=processing_time,
            model=MODEL_NAME
        )

    except Exception as e:
        logger.error(f"Error generating text: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Text generation failed: {str(e)}")


@app.post("/chat")
async def chat_completion(request: ChatRequest):
    """
    Chat completion endpoint (supports conversation history)

    Args:
        request: ChatRequest with messages and parameters

    Returns:
        Generated assistant response
    """
    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        # Format messages into prompt
        prompt = ""
        for msg in request.messages:
            if msg.role == "system":
                prompt += f"System: {msg.content}\n\n"
            elif msg.role == "user":
                prompt += f"User: {msg.content}\n\n"
            elif msg.role == "assistant":
                prompt += f"Assistant: {msg.content}\n\n"

        prompt += "Assistant:"

        # Generate response
        gen_request = GenerateRequest(
            prompt=prompt,
            max_new_tokens=request.max_new_tokens,
            temperature=request.temperature,
            top_p=request.top_p
        )

        response = await generate_text(gen_request)

        return {
            "role": "assistant",
            "content": response.generated_text,
            "processing_time": response.processing_time,
            "tokens_generated": response.tokens_generated
        }

    except Exception as e:
        logger.error(f"Error in chat completion: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat completion failed: {str(e)}")


@app.get("/model/info")
async def model_info():
    """Get model information"""
    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    return {
        "model_name": MODEL_NAME,
        "device": str(model.device) if hasattr(model, 'device') else DEVICE,
        "quantization": "4-bit" if LOAD_IN_4BIT else "full",
        "vocab_size": tokenizer.vocab_size,
        "max_position_embeddings": model.config.max_position_embeddings if hasattr(model.config, 'max_position_embeddings') else None,
        "default_params": {
            "max_new_tokens": MAX_NEW_TOKENS,
            "temperature": TEMPERATURE,
            "top_p": TOP_P
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
