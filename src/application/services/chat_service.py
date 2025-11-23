"""
Chat service for handling conversational AI interactions.
"""

from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime
from application.services.conversation_service import ConversationService
from application.services.chatbot_service import ChatbotService
from infrastructure.ai_services.llm.factory import LLMFactory
from domain.entities.message import MessageEntity
from shared.interfaces.services.ai_services.embedding_service import IEmbeddingService
from shared.interfaces.repositories.knowledge_base_repository import IKnowledgeBaseRepository
from application.services.agent_service import AgentService
from infrastructure.vector_store.factory import IVectorStoreFactory
from core.logger import logger
from infrastructure.postgresql.models.conversation_model import MessageModel
from core.dependencies import get_db_session
from shared.utils.common import extract_context_from_event


class ChatService:
    """
    Service for chat functionality - orchestrates conversation flow with AI responses.
    """

    def __init__(
        self,
        conversation_service: ConversationService,
        chatbot_service: ChatbotService,
        embedding_service: IEmbeddingService,
        vector_store_factory: IVectorStoreFactory,
        knowledge_base_repository: IKnowledgeBaseRepository,
    ):
        self.conversation_service = conversation_service
        self.chatbot_service = chatbot_service
        self.embedding_service = embedding_service
        self.vector_store_factory = vector_store_factory
        self.knowledge_base_repository = knowledge_base_repository

    async def send_message_and_get_response(
        self, bot_id: int, user_id: int, message: str, conversation_id: Optional[int] = None
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
            chatbot = await self.chatbot_service.get_chatbot_by_id(bot_id)
            if not chatbot or not chatbot.is_active:
                raise ValueError("Chatbot not found or inactive")

            chatbot_model_data = await self.chatbot_service.get_chatbot_model_data(bot_id)
            model_name = chatbot_model_data["model_name"]
            if not model_name:
                raise ValueError(f"AI model not found for chatbot {bot_id}")

            if not conversation_id:
                title = self._generate_title(message)
                conversation = await self.conversation_service.create_conversation(
                    user_id=user_id, chatbot_id=bot_id, title=title
                )
                conversation_id = conversation.id
                conversation_title = conversation.title
            else:
                conversation = await self.conversation_service.get_conversation_by_id(
                    conversation_id, user_id
                )
                conversation_title = conversation.title

            from infrastructure.postgresql.models.conversation_model import MessageModel
            from core.dependencies import get_db_session

            async for session in get_db_session():
                user_msg_model = MessageModel(
                    conversation_id=conversation_id,
                    role="user",
                    content=message,
                    msg_metadata={"token_count": self._count_tokens(message)},
                )
                session.add(user_msg_model)
                await session.flush()
                await session.refresh(user_msg_model)

                conversation_with_messages = (
                    await self.conversation_service.get_conversation_with_messages(
                        conversation_id, user_id
                    )
                )

                all_messages = sorted(
                    conversation_with_messages.messages,
                    key=lambda m: m.created_at if m.created_at else m.id,
                )
                max_context_messages = chatbot.max_conversation_length or 50
                recent_messages = all_messages[-max_context_messages:]

                llm = LLMFactory.create(config={"model_name": model_name})

                formatted_prompt = self._format_messages_for_gemini(
                    recent_messages,
                    chatbot.system_prompt,
                    message,
                    rag_contexts=None,  # RAG not used in non-streaming mode
                )

                try:
                    ai_response_text = await llm.generate_response(
                        prompt=formatted_prompt,
                        max_output_tokens=chatbot.max_tokens or 1000,
                        temperature=chatbot.temperature or 0.7,
                        top_p=chatbot.top_p or 1.0,
                    )
                except Exception as e:
                    logger.error(f"LLM generation failed: {e}")
                    if chatbot.fallback_message:
                        ai_response_text = chatbot.fallback_message
                        logger.info(f"Using fallback message for chatbot {bot_id}")
                    else:
                        raise

                ai_token_count = self._count_tokens(ai_response_text)
                assistant_msg_model = MessageModel(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=ai_response_text,
                    msg_metadata={"token_count": ai_token_count, "model": model_name},
                )
                session.add(assistant_msg_model)
                await session.flush()
                await session.refresh(assistant_msg_model)

                await session.commit()

                user_msg = user_msg_model
                assistant_msg = assistant_msg_model
                break

            return {
                "conversation_id": conversation_id,
                "conversation_title": conversation_title,
                "user_message": {
                    "id": user_msg.id,
                    "role": "user",
                    "content": user_msg.content,
                    "created_at": (
                        user_msg.created_at.isoformat()
                        if user_msg.created_at
                        else datetime.utcnow().isoformat()
                    ),
                    "metadata": user_msg.msg_metadata or {},
                },
                "assistant_message": {
                    "id": assistant_msg.id,
                    "role": "assistant",
                    "content": assistant_msg.content,
                    "created_at": (
                        assistant_msg.created_at.isoformat()
                        if assistant_msg.created_at
                        else datetime.utcnow().isoformat()
                    ),
                    "metadata": assistant_msg.msg_metadata or {},
                },
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
        current_message: str,
        rag_contexts: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
        Convert chat message format to single prompt for Gemini.

        Args:
            messages: Previous messages in conversation
            system_prompt: System prompt from chatbot config
            current_message: Current user message
            rag_contexts: Optional retrieved contexts from knowledge base

        Returns:
            Formatted prompt string
        """
        prompt_parts = []
        # Add system prompt
        if system_prompt:
            prompt_parts.append(f"System Instructions: {system_prompt}\n")
            prompt_parts.append("---\n")

        # Add RAG contexts if available
        if rag_contexts:
            prompt_parts.append("Relevant Knowledge Base Information:\n")
            for i, ctx in enumerate(rag_contexts, 1):
                text = ctx.get("text", "")
                source = ctx.get("source", "Unknown")
                score = ctx.get("score", 0.0)
                metadata = ctx.get("metadata", {})
                file_path = metadata.get("file_path", "")
                filename = metadata.get("filename", "")
                repo_url = metadata.get("repo_url", "")
                prompt_parts.append(
                    f"[Reference {i}] (Source: {source}, File: {filename}, Path: {file_path}, Repo: {repo_url}, Relevance: {score:.2f})\n{text}\n"
                )
            prompt_parts.append("---\n")
            prompt_parts.append(
                "Please answer the user's question based on the knowledge base references above. "
                "Cite the reference numbers when using information from the knowledge base.\n\n"
            )

        # Add conversation history (excluding current message which is already added)
        for msg in messages[:-1]:  # Exclude last message (current user message)
            role = "User" if msg.role == "user" else "Assistant"
            prompt_parts.append(f"{role}: {msg.content}\n")

        # Add current message
        prompt_parts.append(f"User: {current_message}\n")
        prompt_parts.append("Assistant:")

        return "\n".join(prompt_parts)

    async def send_message_and_stream_response(
        self,
        bot_id: int,
        user_id: int,
        message: str,
        conversation_id: Optional[int] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Send message and stream AI response in real-time.
        Supports both regular LLM streaming and agent streaming based on chatbot configuration.

        Args:
            bot_id: Chatbot ID
            user_id: User ID
            message: User's message content
            conversation_id: Optional existing conversation ID
            agent_service: Optional AgentService instance for agent-enabled chatbots
        """
        try:
            # -------------------------------
            # Get chatbot and validate
            # -------------------------------
            chatbot = await self.chatbot_service.get_chatbot_by_id(bot_id)
            if not chatbot or not chatbot.is_active:
                yield {"type": "error", "data": {"error": "Chatbot not found or inactive"}}
                return

            chatbot_model_data = await self.chatbot_service.get_chatbot_model_data(bot_id)
            if not chatbot_model_data["model_name"]:
                yield {
                    "type": "error",
                    "data": {"error": f"AI model not found for chatbot {bot_id}"},
                }
                return

            # -------------------------------
            # Create or get conversation
            # -------------------------------
            if not conversation_id:
                title = self._generate_title(message)
                conversation = await self.conversation_service.create_conversation(
                    user_id=user_id, chatbot_id=bot_id, title=title
                )
                conversation_id = conversation.id
                conversation_title = conversation.title
            else:
                conversation = await self.conversation_service.get_conversation_by_id(
                    conversation_id, user_id
                )
                conversation_title = conversation.title

            # -------------------------------
            # Yield start event
            # -------------------------------
            yield {
                "type": "start",
                "data": {
                    "conversation_id": conversation_id,
                    "conversation_title": conversation_title,
                    "timestamp": datetime.utcnow().isoformat(),
                    "bot_id": bot_id,
                },
            }

            # -------------------------------
            # Runtime config for agent
            # -------------------------------
            runtime_config = {
                "model_name": chatbot_model_data["model_name"],
                "max_iterations": 5,
                "max_output_tokens": chatbot.max_tokens,
                "temperature": chatbot.temperature,
                "top_p": chatbot.top_p,
                "system_prompt": chatbot.system_prompt,
            }

            # -------------------------------
            # Get knowledge base and vector store
            # -------------------------------
            knowledge_base = await self.knowledge_base_repository.get_by_chatbot_id(bot_id)
            if not knowledge_base or not knowledge_base.is_active:
                logger.info(f"No active knowledge base found for chatbot {bot_id}")
                yield {
                    "type": "info",
                    "data": {"message": f"No active knowledge base found for chatbot {bot_id}"},
                }
                return

            collection_name = knowledge_base.vector_store_collection or f"kb_{knowledge_base.id}"
            logger.info(f"Querying vector store collection: {collection_name}")

            vector_store = self.vector_store_factory.create(
                config={"collection_name": collection_name}
            )

            # -------------------------------
            # Initialize agent service
            # -------------------------------
            agent_service_instance = AgentService(
                embedding_service=self.embedding_service,
                runtime_config=runtime_config,
                retriever=vector_store,
            )
            llm_service = LLMFactory.create(
                provider="gemini", config={"model_name": chatbot_model_data["model_name"]}
            )
            # -------------------------------
            # Store user message
            # -------------------------------
            async for session in get_db_session():
                user_msg_model = MessageModel(
                    conversation_id=conversation_id,
                    role="user",
                    content=message,
                    msg_metadata={"token_count": self._count_tokens(message)},
                )
                session.add(user_msg_model)
                await session.flush()
                await session.refresh(user_msg_model)

                # -------------------------------
                # Stream from agent
                # -------------------------------
                full_response = ""
                contexts = None
                async for event in agent_service_instance.stream_events(message):
                    if event.get("type") == "tool_end":
                        contexts = extract_context_from_event(event)
                    yield event

                # Get conversation history
                conversation_with_messages = (
                    await self.conversation_service.get_conversation_with_messages(
                        conversation_id, user_id
                    )
                )

                all_messages = sorted(
                    conversation_with_messages.messages,
                    key=lambda m: m.created_at if m.created_at else m.id,
                )
                max_context_messages = chatbot.max_conversation_length or 50
                recent_messages = all_messages[-max_context_messages:]

                if contexts:
                    formatted_prompt = self._format_messages_for_gemini(
                        recent_messages, chatbot.system_prompt, message, rag_contexts=contexts
                    )

                    # Stream LLM response
                    full_response = ""
                    async for chunk in llm_service.generate_streaming_response(
                        prompt=formatted_prompt,
                        max_output_tokens=chatbot.max_tokens,
                        temperature=chatbot.temperature,
                        top_p=chatbot.top_p,
                    ):
                        full_response += chunk
                        yield {"type": "token", "data": {"content": chunk}}

                # -------------------------------
                # Save assistant message
                # -------------------------------
                ai_token_count = self._count_tokens(full_response)
                assistant_msg_model = MessageModel(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=full_response,
                    msg_metadata={
                        "token_count": ai_token_count,
                        "model": chatbot_model_data["model_name"],
                    },
                )
                session.add(assistant_msg_model)
                await session.commit()
                await session.refresh(user_msg_model)
                await session.refresh(assistant_msg_model)

                break  # Exit session loop

            # -------------------------------
            # Done event
            # -------------------------------
            yield {
                "type": "done",
                "data": {"finish_reason": "stop", "conversation_id": conversation_id},
            }

        except Exception as e:
            logger.error(f"Streaming error in chat service: {e}", exc_info=True)
            yield {
                "type": "error",
                "data": {"error": str(e), "message": "Failed to stream response"},
            }
