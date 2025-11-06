"""
Bedrock mapper for converting domain entities to AWS Bedrock format.

This mapper isolates AWS Bedrock-specific formatting logic from the domain layer.
"""

from typing import Dict, Any, List
from src.domain.entities.message import Message


class BedrockMapper:
    """
    Mapper for converting domain entities to AWS Bedrock API format.

    This class encapsulates all knowledge about AWS Bedrock's message format,
    keeping the domain layer free from infrastructure concerns.
    """

    @staticmethod
    def message_to_bedrock_format(message: Message) -> Dict[str, Any]:
        """
        Convert a Message domain entity to AWS Bedrock message format.

        Args:
            message: Domain Message entity

        Returns:
            Dictionary formatted for AWS Bedrock API

        Example:
            {
                "role": "user",
                "content": [{"text": "Hello, world!"}]
            }
        """
        bedrock_message = {
            "role": message.role.value,
            "content": [{"text": message.content}]
        }

        # Add tool calls if present
        if message.tool_calls:
            bedrock_message["tool_calls"] = message.tool_calls

        return bedrock_message

    @staticmethod
    def messages_to_bedrock_format(messages: List[Message]) -> List[Dict[str, Any]]:
        """
        Convert a list of Message entities to AWS Bedrock format.

        Args:
            messages: List of domain Message entities

        Returns:
            List of dictionaries formatted for AWS Bedrock API
        """
        return [
            BedrockMapper.message_to_bedrock_format(message)
            for message in messages
        ]

    @staticmethod
    def bedrock_response_to_content(bedrock_response: Dict[str, Any]) -> str:
        """
        Extract content text from AWS Bedrock response.

        Args:
            bedrock_response: Response from AWS Bedrock API

        Returns:
            Extracted content text
        """
        # Handle different response formats from Bedrock
        if "content" in bedrock_response:
            content = bedrock_response["content"]
            if isinstance(content, list) and len(content) > 0:
                if "text" in content[0]:
                    return content[0]["text"]
            elif isinstance(content, str):
                return content

        # Fallback to direct text field
        if "text" in bedrock_response:
            return bedrock_response["text"]

        return ""
