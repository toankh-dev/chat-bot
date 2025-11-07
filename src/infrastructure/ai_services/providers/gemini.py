"""
Google Gemini LLM provider.
"""

from typing import Dict, Any, Optional
import google.generativeai as genai
from infrastructure.ai_services.providers.base import BaseLLMService
from core.config import settings
from core.logger import logger

class GeminiLLMService(BaseLLMService):
    """Google Gemini LLM service implementation."""
    
    def __init__(self, api_key: str = None, model_name: str = "gemini-1.5-pro"):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name
        
        if not self.api_key:
            raise ValueError("Gemini API key is required")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Initialize model
        self.model = genai.GenerativeModel(model_name)
    
    async def generate_response(
        self,
        prompt: str,
        context: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate response using Gemini."""
        try:
            # Build full prompt with context
            full_prompt = self._build_prompt(prompt, context)
            
            # Configure generation settings
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
                top_p=kwargs.get('top_p', 0.8),
                top_k=kwargs.get('top_k', 40)
            )
            
            # Generate response
            response = await self.model.generate_content_async(
                full_prompt,
                generation_config=generation_config
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini LLM error: {e}")
            raise Exception(f"Failed to generate response: {str(e)}")
    
    async def generate_streaming_response(
        self,
        prompt: str,
        context: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ):
        """Generate streaming response using Gemini."""
        try:
            full_prompt = self._build_prompt(prompt, context)
            
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
                top_p=kwargs.get('top_p', 0.8),
                top_k=kwargs.get('top_k', 40)
            )
            
            # Generate streaming response
            response = await self.model.generate_content_async(
                full_prompt,
                generation_config=generation_config,
                stream=True
            )
            
            async for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            logger.error(f"Gemini streaming error: {e}")
            raise Exception(f"Failed to generate streaming response: {str(e)}")
    
    def get_provider_name(self) -> str:
        """Get provider name."""
        return "gemini"
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            "provider": "gemini",
            "model_name": self.model_name,
            "supports_streaming": True,
            "supports_context": True,
            "max_input_tokens": 1048576,  # Gemini 1.5 Pro context window
            "max_output_tokens": 8192
        }
    
    def _build_prompt(self, prompt: str, context: Optional[str] = None) -> str:
        """Build the full prompt with context."""
        if context:
            return f"""Dựa trên thông tin sau đây, hãy trả lời câu hỏi một cách chính xác và chi tiết.

Thông tin tham khảo:
{context}

Câu hỏi: {prompt}

Trả lời:"""
        return prompt