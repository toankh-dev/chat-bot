from typing import List, Dict, Optional


class PromptBuilder:
    """
    Utility for building chat prompts in Bedrock-supported message format.
    """

    def __init__(self, system_prompt: Optional[str] = None):
        self.system_prompt = system_prompt
        self.messages: List[Dict[str, str]] = []

    def add_system(self, content: str):
        """Set or update system prompt."""
        self.system_prompt = content

    def add_user(self, content: str):
        """Append a user message."""
        self.messages.append({"role": "user", "content": content})

    def add_assistant(self, content: str):
        """Append an assistant response."""
        self.messages.append({"role": "assistant", "content": content})

    def add_context(self, context: str):
        """
        Add contextual info (RAG knowledge, memory, etc.)
        Represented as an assistant 'system-style' message.
        """
        self.messages.append({"role": "assistant", "content": f"[CONTEXT]\n{context}"})

    def add_history(self, history: List[Dict[str, str]]):
        """Attach previous chat history."""
        self.messages.extend(history)

    def clear_messages(self):
        """Reset conversation except system prompt."""
        self.messages.clear()

    def build(self) -> List[Dict[str, str]]:
        """Return final standard Bedrock chat format."""
        final_messages = []

        if self.system_prompt:
            final_messages.append({
                "role": "system",
                "content": self.system_prompt
            })

        final_messages.extend(self.messages)
        return final_messages

    def __repr__(self):
        return f"<PromptBuilder messages={len(self.messages)}, system_prompt={'yes' if self.system_prompt else 'no'}>"
