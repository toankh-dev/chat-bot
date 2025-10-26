"""
Summarize Tool for analyzing conversations

Supports:
- Discord (recommended, free, easy)
- Slack (optional)
"""

import json
import logging
import os
import boto3
import requests
from typing import Dict, Any, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SummarizeTool:
    """
    Tool for summarizing conversations from Discord or Slack

    Automatically uses Discord if USE_DISCORD=true, otherwise falls back to Slack
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Check which service to use
        self.use_discord = os.getenv("USE_DISCORD", "false").lower() == "true"
        self.use_slack = os.getenv("USE_SLACK", "false").lower() == "true"

        # Discord configuration
        if self.use_discord:
            self.discord_token = os.getenv("DISCORD_BOT_TOKEN")
            self.discord_guild_id = os.getenv("DISCORD_GUILD_ID")
            self.discord_base_url = "https://discord.com/api/v10"

        # Slack configuration
        if self.use_slack:
            endpoint_url = os.getenv("LOCALSTACK_ENDPOINT")
            self.secrets_client = boto3.client(
                'secretsmanager',
                endpoint_url=endpoint_url,
                region_name=os.getenv("AWS_DEFAULT_REGION", "ap-southeast-1")
            )
            self._slack_secret = None

    def _get_slack_secret(self) -> Dict[str, str]:
        """Get Slack credentials"""
        if self._slack_secret is None:
            response = self.secrets_client.get_secret_value(
                SecretId='/chatbot/slack/bot-token'
            )
            self._slack_secret = json.loads(response['SecretString'])
        return self._slack_secret

    def get_slack_messages(self, params: Dict[str, Any]) -> List[Dict]:
        """Get messages from Slack channel"""
        try:
            secret = self._get_slack_secret()
            bot_token = secret['bot_token']

            channel = params.get('channel')
            days = params.get('days', 7)

            # Calculate time range
            oldest = (datetime.now() - timedelta(days=days)).timestamp()

            url = "https://slack.com/api/conversations.history"
            headers = {'Authorization': f'Bearer {bot_token}'}
            params_dict = {
                'channel': channel,
                'oldest': oldest,
                'limit': params.get('limit', 100)
            }

            response = requests.get(url, headers=headers, params=params_dict, timeout=30)
            result = response.json()

            if result.get('ok'):
                return result.get('messages', [])
            else:
                self.logger.error(f"Slack API error: {result.get('error')}")
                return []

        except Exception as e:
            self.logger.error(f"Error fetching Slack messages: {e}")
            return []

    def get_discord_messages(self, params: Dict[str, Any]) -> List[Dict]:
        """Get messages from Discord channel"""
        try:
            channel_id = params.get('channel_id')
            limit = params.get('limit', 100)

            if not channel_id:
                self.logger.error("No channel_id provided")
                return []

            self.logger.info(f"Fetching Discord messages from channel {channel_id}")

            url = f"{self.discord_base_url}/channels/{channel_id}/messages"
            headers = {
                'Authorization': f'Bot {self.discord_token}',
                'Content-Type': 'application/json'
            }

            # Discord limits to 100 per request
            response = requests.get(
                url,
                headers=headers,
                params={'limit': min(limit, 100)},
                timeout=30
            )
            response.raise_for_status()

            messages = response.json()
            return messages

        except Exception as e:
            self.logger.error(f"Error fetching Discord messages: {e}")
            return []

    def search_discord_messages(self, params: Dict[str, Any]) -> List[Dict]:
        """Search messages in Discord"""
        try:
            channel_id = params.get('channel_id')
            query = params.get('query', '')

            if not channel_id or not query:
                self.logger.error("channel_id and query are required")
                return []

            self.logger.info(f"Searching Discord for '{query}' in channel {channel_id}")

            # Note: Discord search requires guild_id
            if not self.discord_guild_id:
                self.logger.error("DISCORD_GUILD_ID not configured")
                return []

            url = f"{self.discord_base_url}/guilds/{self.discord_guild_id}/messages/search"
            headers = {
                'Authorization': f'Bot {self.discord_token}',
                'Content-Type': 'application/json'
            }

            response = requests.get(
                url,
                headers=headers,
                params={
                    'channel_id': channel_id,
                    'content': query
                },
                timeout=30
            )
            response.raise_for_status()

            results = response.json()
            messages = results.get('messages', [])

            return messages

        except Exception as e:
            self.logger.error(f"Error searching Discord messages: {e}")
            return []

    def summarize_messages(self, messages: List[Dict], source: str = 'slack') -> str:
        """Summarize list of messages"""
        if not messages:
            return "No messages to summarize"

        # Simple summarization (could use LLM for better results)
        summary = f"Summary of {len(messages)} messages from {source.title()}:\n\n"

        # Count users/authors
        if source == 'discord':
            users = set(msg.get('author', {}).get('username', 'unknown') for msg in messages)
        else:  # slack
            users = set(msg.get('user', 'unknown') for msg in messages)

        summary += f"Participants: {len(users)} users\n"

        # Extract key points (first 5 messages)
        summary += "\nKey messages:\n"
        for i, msg in enumerate(messages[:5], 1):
            if source == 'discord':
                author = msg.get('author', {}).get('username', 'unknown')
                text = msg.get('content', '')[:100]
                timestamp = msg.get('timestamp', '')[:10]
            else:  # slack
                author = msg.get('user', 'unknown')
                text = msg.get('text', '')[:100]
                timestamp = datetime.fromtimestamp(float(msg.get('ts', 0))).strftime('%Y-%m-%d')

            summary += f"{i}. [{timestamp}] {author}: {text}...\n"

        return summary

    def run(self, tool_input: str) -> str:
        """
        Run the tool

        Supported actions:
            Discord:
                - get_messages: Get recent messages
                - summarize: Summarize messages
                - search: Search for messages
            Slack:
                - get_messages: Get recent messages
                - summarize: Summarize messages
        """
        try:
            input_data = json.loads(tool_input)
            action = input_data.get('action')
            parameters = input_data.get('parameters', {})

            self.logger.info(f"Summarize tool action: {action}")

            # Discord actions
            if self.use_discord:
                if action == 'get_messages':
                    messages = self.get_discord_messages(parameters)
                    return f"Retrieved {len(messages)} messages from Discord"

                elif action == 'summarize':
                    messages = self.get_discord_messages(parameters)
                    return self.summarize_messages(messages, source='discord')

                elif action == 'search':
                    messages = self.search_discord_messages(parameters)
                    if messages:
                        return self.summarize_messages(messages, source='discord')
                    else:
                        return f"No messages found for query: {parameters.get('query')}"

                elif action == 'extract_action_items':
                    messages = self.get_discord_messages(parameters)
                    # TODO: Use LLM to extract action items
                    return f"Found {len(messages)} Discord messages (action item extraction not implemented yet)"

            # Slack actions
            elif self.use_slack:
                if action == 'get_messages':
                    messages = self.get_slack_messages(parameters)
                    return f"Retrieved {len(messages)} messages from Slack"

                elif action == 'summarize':
                    messages = self.get_slack_messages(parameters)
                    return self.summarize_messages(messages, source='slack')

                elif action == 'extract_action_items':
                    messages = self.get_slack_messages(parameters)
                    # TODO: Use LLM to extract action items
                    return f"Found {len(messages)} Slack messages (action item extraction not implemented yet)"

            else:
                return "Error: No messaging service configured. Set USE_DISCORD=true or USE_SLACK=true"

            return f"Unknown action: {action}"

        except Exception as e:
            self.logger.error(f"Error in summarize tool: {e}")
            return f"Error: {str(e)}"
