"""
Utility functions for LLM services (Infrastructure layer).

These are standalone utility functions that can be used by any LLM
implementation without requiring inheritance.

Benefits:
1. No inheritance needed
2. Can be used anywhere (not just in classes)
3. Easy to test in isolation
4. More flexible and composable
"""
from typing import Optional, Dict, Any


def build_prompt_with_context(prompt: str, context: Optional[str] = None) -> str:
    """
    Build full prompt with context if provided.

    Args:
        prompt: User question/prompt
        context: Retrieved context from knowledge base

    Returns:
        str: Full prompt string

    Example:
        >>> build_prompt_with_context("What is AI?", "AI stands for...")
        'Context:\nAI stands for...\n\nQuestion: What is AI?'
    """
    if context:
        return f"Context:\n{context}\n\nQuestion: {prompt}"
    return prompt


def validate_generation_parameters(max_tokens: int, temperature: float) -> None:
    """
    Validate LLM generation parameters.

    Args:
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature

    Raises:
        ValueError: If parameters are invalid

    Example:
        >>> validate_generation_parameters(1000, 0.7)  # OK
        >>> validate_generation_parameters(-1, 0.7)  # Raises ValueError
    """
    if max_tokens <= 0:
        raise ValueError(f"max_tokens must be positive, got {max_tokens}")
    if not 0.0 <= temperature <= 2.0:
        raise ValueError(f"temperature must be between 0.0 and 2.0, got {temperature}")


def format_model_info(provider: str, model_id: str, **kwargs) -> Dict[str, Any]:
    """
    Format model information into standard structure.

    Args:
        provider: Provider name (bedrock, gemini, etc.)
        model_id: Model identifier
        **kwargs: Additional model metadata

    Returns:
        Dict containing standardized model info

    Example:
        >>> format_model_info("gemini", "gemini-pro", version="1.0")
        {'provider': 'gemini', 'model_id': 'gemini-pro', 'version': '1.0'}
    """
    info = {
        "provider": provider,
        "model_id": model_id
    }
    info.update(kwargs)
    return info


def estimate_tokens(text: str, chars_per_token: int = 4) -> int:
    """
    Estimate number of tokens in text.

    This is a rough approximation. For accurate counting,
    use provider-specific tokenizers.

    Args:
        text: Text to estimate
        chars_per_token: Average characters per token (default: 4)

    Returns:
        Estimated token count

    Example:
        >>> estimate_tokens("Hello world!")
        3
    """
    if not text:
        return 0
    return max(1, len(text) // chars_per_token)


def validate_prompt_input(prompt: str) -> None:
    """
    Validate prompt input before sending to LLM.

    Args:
        prompt: Prompt text to validate

    Raises:
        ValueError: If prompt is empty or invalid

    Example:
        >>> validate_prompt_input("Hello")  # OK
        >>> validate_prompt_input("")  # Raises ValueError
    """
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty")


def truncate_context(context: str, max_tokens: int, chars_per_token: int = 4) -> str:
    """
    Truncate context to fit within token limit.

    Args:
        context: Context text
        max_tokens: Maximum tokens allowed
        chars_per_token: Average characters per token

    Returns:
        Truncated context string

    Example:
        >>> truncate_context("Hello world this is a test", max_tokens=3)
        'Hello world this...'
    """
    if not context:
        return ""

    max_chars = max_tokens * chars_per_token
    if len(context) <= max_chars:
        return context

    return context[:max_chars - 3] + "..."


def merge_system_and_user_prompt(system_prompt: Optional[str], user_prompt: str) -> str:
    """
    Merge system prompt and user prompt into single prompt.

    Args:
        system_prompt: Optional system instructions
        user_prompt: User's question/prompt

    Returns:
        Merged prompt string

    Example:
        >>> merge_system_and_user_prompt("You are helpful", "Hi")
        'System: You are helpful\n\nUser: Hi'
    """
    if not system_prompt:
        return user_prompt

    return f"System: {system_prompt}\n\nUser: {user_prompt}"
