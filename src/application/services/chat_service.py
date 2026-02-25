"""
Chat service for handling conversational AI interactions.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from application.services.conversation_service import ConversationService
from application.services.chatbot_service import ChatbotService
from infrastructure.ai_services.llm.factory import LLMFactory
from domain.entities.chatbot import ChatbotEntity
from domain.entities.message import MessageEntity
from core.logger import logger


class ChatService:
    """
    Service for chat functionality - orchestrates conversation flow with AI responses.
    """

    def __init__(
        self,
        conversation_service: ConversationService,
        chatbot_service: ChatbotService
    ):
        self.conversation_service = conversation_service
        self.chatbot_service = chatbot_service

    async def send_message_and_get_response(
        self,
        bot_id: int,
        user_id: int,
        message: str,
        conversation_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Send user message and get AI response.

        Args:
            bot_id: Chatbot ID
            user_id: User ID
            message: User's message content
            conversation_id: Optional existing conversation ID

        Returns:
            Dict with conversation_id, conversation_title, user_message, assistant_message
        """
        try:
            # 1. Get chatbot configuration
            chatbot = await self.chatbot_service.get_chatbot_by_id(bot_id)
            if not chatbot or not chatbot.is_active:
                raise ValueError("Chatbot not found or inactive")

            # 2. Handle conversation (create or get existing)
            if not conversation_id:
                # Create new conversation
                title = self._generate_title(message)
                conversation = await self.conversation_service.create_conversation(
                    user_id=user_id,
                    chatbot_id=bot_id,
                    title=title
                )
                conversation_id = conversation.id
                conversation_title = conversation.title
            else:
                # Get existing conversation
                conversation = await self.conversation_service.get_conversation_by_id(
                    conversation_id, user_id
                )
                conversation_title = conversation.title

            # 3. Save user message directly using MessageModel
            from infrastructure.postgresql.models.conversation_model import MessageModel
            from core.dependencies import get_db_session

            async for session in get_db_session():
                user_msg_model = MessageModel(
                    conversation_id=conversation_id,
                    role="user",
                    content=message,
                    msg_metadata={"token_count": self._count_tokens(message)}
                )
                session.add(user_msg_model)
                await session.flush()
                await session.refresh(user_msg_model)

                # 4. Get conversation history for AI context
                conversation_with_messages = await self.conversation_service.get_conversation_with_messages(
                    conversation_id, user_id
                )

                # Get recent messages (limit to last 10 for context)
                recent_messages = conversation_with_messages.messages[-10:]

                # 5. Build context and call AI
                llm = LLMFactory.create(model_name="gemini-2.5-flash")

                # Format messages for Gemini (convert to single prompt)
                formatted_prompt = self._format_messages_for_gemini(
                    recent_messages,
                    chatbot.system_prompt,
                    message
                )

                # Call Gemini
                ai_response_text = await llm.generate_response(
                    prompt=formatted_prompt,
                    max_tokens=chatbot.max_tokens or 1000,
                    temperature=chatbot.temperature or 0.7
                )

                # 6. Save assistant message
                ai_token_count = self._count_tokens(ai_response_text)
                assistant_msg_model = MessageModel(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=ai_response_text,
                    msg_metadata={"token_count": ai_token_count, "model": "gemini-2.5-flash"}
                )
                session.add(assistant_msg_model)
                await session.flush()
                await session.refresh(assistant_msg_model)

                # Commit the transaction
                await session.commit()

                # Map to user_msg and assistant_msg for response
                user_msg = user_msg_model
                assistant_msg = assistant_msg_model
                break

            # 7. Update conversation metadata
            # Note: update_conversation_metadata may not exist yet, skip for now
            # Will update message_count manually if needed

            return {
                "conversation_id": conversation_id,
                "conversation_title": conversation_title,
                "user_message": {
                    "id": user_msg.id,
                    "role": "user",
                    "content": user_msg.content,
                    "created_at": user_msg.created_at.isoformat() if user_msg.created_at else datetime.utcnow().isoformat(),
                    "metadata": user_msg.msg_metadata or {}
                },
                "assistant_message": {
                    "id": assistant_msg.id,
                    "role": "assistant",
                    "content": assistant_msg.content,
                    "created_at": assistant_msg.created_at.isoformat() if assistant_msg.created_at else datetime.utcnow().isoformat(),
                    "metadata": assistant_msg.msg_metadata or {}
                }
            }

        except Exception as e:
            logger.error(f"Error in chat service: {e}")
            raise

    def _generate_title(self, message: str, max_words: int = 6) -> str:
        """Generate conversation title from first message."""
        words = message.strip().split()[:max_words]
        title = " ".join(words)
        return title + ("..." if len(message.split()) > max_words else "")

    def _count_tokens(self, text: str) -> int:
        """Simple word-based token estimation."""
        return len(text.split())

    def _format_messages_for_gemini(
        self,
        messages: List[MessageEntity],
        system_prompt: Optional[str],
        current_message: str
    ) -> str:
        """
        Convert chat message format to single prompt for Gemini.

        Args:
            messages: Previous messages in conversation
            system_prompt: System prompt from chatbot config
            current_message: Current user message

        Returns:
            Formatted prompt string
        """
        prompt_parts = []

        # Add system prompt
        if system_prompt:
            prompt_parts.append(f"System Instructions: {system_prompt}\n")
            prompt_parts.append("---\n")

        # Add conversation history (excluding current message which is already added)
        for msg in messages[:-1]:  # Exclude last message (current user message)
            role = "User" if msg.role == "user" else "Assistant"
            prompt_parts.append(f"{role}: {msg.content}\n")

        # Add current message
        prompt_parts.append(f"User: {current_message}\n")
        prompt_parts.append("Assistant:")

        return "\n".join(prompt_parts)
