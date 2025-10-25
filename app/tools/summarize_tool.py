"""
Summarize Tool for analyzing Slack conversations
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
    Tool for summarizing Slack conversations
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

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

    def summarize_messages(self, messages: List[Dict]) -> str:
        """Summarize list of messages"""
        if not messages:
            return "No messages to summarize"

        # Simple summarization (could use LLM for better results)
        summary = f"Summary of {len(messages)} messages:\n\n"

        # Count users
        users = set(msg.get('user', 'unknown') for msg in messages)
        summary += f"Participants: {len(users)} users\n"

        # Extract key points (first 5 messages)
        summary += "\nKey messages:\n"
        for i, msg in enumerate(messages[:5], 1):
            text = msg.get('text', '')[:100]
            summary += f"{i}. {text}...\n"

        return summary

    def run(self, tool_input: str) -> str:
        """Run the tool"""
        try:
            input_data = json.loads(tool_input)
            action = input_data.get('action')
            parameters = input_data.get('parameters', {})

            self.logger.info(f"Summarize tool action: {action}")

            if action == 'get_messages':
                messages = self.get_slack_messages(parameters)
                return f"Retrieved {len(messages)} messages from Slack"

            elif action == 'summarize':
                messages = self.get_slack_messages(parameters)
                return self.summarize_messages(messages)

            elif action == 'extract_action_items':
                messages = self.get_slack_messages(parameters)
                # TODO: Use LLM to extract action items
                return f"Found {len(messages)} messages (action item extraction not implemented yet)"

            else:
                return f"Unknown action: {action}"

        except Exception as e:
            self.logger.error(f"Error in summarize tool: {e}")
            return f"Error: {str(e)}"
