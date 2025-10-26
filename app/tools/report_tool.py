"""
Report Tool for creating issues/tickets and posting messages

Supports:
- Discord (recommended, free, easy)
- Backlog (optional)
- Slack (optional)
"""

import json
import logging
import os
import boto3
import requests
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ReportTool:
    """
    Tool for report operations (Discord messages/threads, Backlog tickets, Slack messages)

    Automatically uses Discord if USE_DISCORD=true, otherwise falls back to Backlog/Slack
    """

    def __init__(self):
        """Initialize the report tool"""
        self.logger = logging.getLogger(__name__)

        # Check which service to use
        self.use_discord = os.getenv("USE_DISCORD", "false").lower() == "true"
        self.use_slack = os.getenv("USE_SLACK", "false").lower() == "true"
        self.use_backlog = os.getenv("USE_BACKLOG", "false").lower() == "true"

        # Discord configuration
        if self.use_discord:
            self.discord_token = os.getenv("DISCORD_BOT_TOKEN")
            self.discord_notification_channel = os.getenv("DISCORD_NOTIFICATION_CHANNEL")
            self.discord_base_url = "https://discord.com/api/v10"

        # LocalStack or real AWS (for Backlog/Slack secrets)
        if self.use_slack or self.use_backlog:
            endpoint_url = os.getenv("LOCALSTACK_ENDPOINT")
            self.secrets_client = boto3.client(
                'secretsmanager',
                endpoint_url=endpoint_url,
                region_name=os.getenv("AWS_DEFAULT_REGION", "ap-southeast-1")
            )

            # Cache for secrets
            self._backlog_secret = None
            self._slack_secret = None

    def _get_backlog_secret(self) -> Dict[str, str]:
        """Get Backlog API credentials from Secrets Manager"""
        if self._backlog_secret is None:
            try:
                response = self.secrets_client.get_secret_value(
                    SecretId='/chatbot/backlog/api-key'
                )
                self._backlog_secret = json.loads(response['SecretString'])
            except Exception as e:
                self.logger.error(f"Error fetching Backlog secret: {e}")
                raise

        return self._backlog_secret

    def _get_slack_secret(self) -> Dict[str, str]:
        """Get Slack API credentials from Secrets Manager"""
        if self._slack_secret is None:
            try:
                response = self.secrets_client.get_secret_value(
                    SecretId='/chatbot/slack/bot-token'
                )
                self._slack_secret = json.loads(response['SecretString'])
            except Exception as e:
                self.logger.error(f"Error fetching Slack secret: {e}")
                raise

        return self._slack_secret

    def create_backlog_ticket(self, params: Dict[str, Any]) -> str:
        """
        Create a Backlog ticket

        Args:
            params: Ticket parameters (project_key, summary, description, etc.)

        Returns:
            Result message
        """

        try:
            self.logger.info("Creating Backlog ticket...")

            # Get credentials
            secret = self._get_backlog_secret()
            api_key = secret['api_key']
            space_url = secret['space_url']

            # Prepare request
            url = f"{space_url}/api/v2/issues"
            data = {
                'apiKey': api_key,
                'projectId': params.get('project_key'),
                'summary': params.get('summary'),
                'description': params.get('description'),
                'issueTypeId': params.get('issue_type', 1),
                'priorityId': params.get('priority', 2)
            }

            # Add assignee if provided
            if params.get('assignee'):
                # Would need to look up user ID first
                pass

            # Create ticket
            response = requests.post(url, data=data, timeout=30)

            if response.status_code == 201:
                issue = response.json()
                result = (
                    f"✅ Created Backlog ticket: {issue['issueKey']}\n"
                    f"URL: {space_url}/view/{issue['issueKey']}\n"
                    f"ID: {issue['id']}"
                )
                self.logger.info(f"Ticket created: {issue['issueKey']}")
                return result
            else:
                error = f"Failed to create ticket: {response.status_code} - {response.text}"
                self.logger.error(error)
                return error

        except Exception as e:
            self.logger.error(f"Error creating Backlog ticket: {e}")
            return f"Error creating ticket: {str(e)}"

    def post_slack_message(self, params: Dict[str, Any]) -> str:
        """
        Post a message to Slack

        Args:
            params: Message parameters (channel, message, thread_ts)

        Returns:
            Result message
        """

        try:
            self.logger.info(f"Posting to Slack channel: {params.get('channel')}")

            # Get credentials
            secret = self._slack_secret()
            bot_token = secret['bot_token']

            url = "https://slack.com/api/chat.postMessage"
            headers = {
                'Authorization': f'Bearer {bot_token}',
                'Content-Type': 'application/json'
            }

            data = {
                'channel': params.get('channel'),
                'text': params.get('message'),
                'thread_ts': params.get('thread_ts')
            }

            response = requests.post(url, headers=headers, json=data, timeout=30)
            result = response.json()

            if result.get('ok'):
                return (
                    f"✅ Message posted to Slack\n"
                    f"Channel: {params.get('channel')}\n"
                    f"Timestamp: {result.get('ts')}"
                )
            else:
                error = f"Failed to post message: {result.get('error', 'Unknown error')}"
                self.logger.error(error)
                return error

        except Exception as e:
            self.logger.error(f"Error posting to Slack: {e}")
            return f"Error posting to Slack: {str(e)}"

    def post_discord_message(self, params: Dict[str, Any]) -> str:
        """
        Post a message to Discord

        Args:
            params: Message parameters (channel_id, message)

        Returns:
            Result message
        """

        try:
            channel_id = params.get('channel_id', self.discord_notification_channel)

            if not channel_id:
                return "Error: No Discord channel specified and DISCORD_NOTIFICATION_CHANNEL not configured"

            self.logger.info(f"Posting to Discord channel: {channel_id}")

            url = f"{self.discord_base_url}/channels/{channel_id}/messages"
            headers = {
                'Authorization': f'Bot {self.discord_token}',
                'Content-Type': 'application/json'
            }

            data = {
                'content': params.get('message')
            }

            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()

            message = response.json()
            message_id = message.get('id')

            return (
                f"✅ Message posted to Discord\n"
                f"Channel ID: {channel_id}\n"
                f"Message ID: {message_id}"
            )

        except Exception as e:
            self.logger.error(f"Error posting to Discord: {e}")
            return f"Error posting to Discord: {str(e)}"

    def create_discord_thread(self, params: Dict[str, Any]) -> str:
        """
        Create a thread in Discord

        Args:
            params: Thread parameters (channel_id, thread_name, message)

        Returns:
            Result message
        """

        try:
            channel_id = params.get('channel_id', self.discord_notification_channel)
            thread_name = params.get('thread_name', 'Discussion')
            message = params.get('message', '')

            if not channel_id:
                return "Error: No Discord channel specified"

            self.logger.info(f"Creating Discord thread: {thread_name}")

            # First, post initial message
            msg_url = f"{self.discord_base_url}/channels/{channel_id}/messages"
            headers = {
                'Authorization': f'Bot {self.discord_token}',
                'Content-Type': 'application/json'
            }

            msg_response = requests.post(
                msg_url,
                headers=headers,
                json={'content': message or f"Starting thread: {thread_name}"},
                timeout=30
            )
            msg_response.raise_for_status()
            message_data = msg_response.json()
            message_id = message_data.get('id')

            # Then create thread from message
            thread_url = f"{self.discord_base_url}/channels/{channel_id}/messages/{message_id}/threads"
            thread_response = requests.post(
                thread_url,
                headers=headers,
                json={
                    'name': thread_name,
                    'auto_archive_duration': 1440  # 1 day
                },
                timeout=30
            )
            thread_response.raise_for_status()
            thread = thread_response.json()
            thread_id = thread.get('id')

            return (
                f"✅ Created Discord thread: {thread_name}\n"
                f"Thread ID: {thread_id}\n"
                f"Channel ID: {channel_id}"
            )

        except Exception as e:
            self.logger.error(f"Error creating Discord thread: {e}")
            return f"Error creating Discord thread: {str(e)}"

    def run(self, tool_input: str) -> str:
        """
        Run the tool

        Args:
            tool_input: JSON string with action and parameters

        Returns:
            Result message

        Supported actions:
            Discord:
                - post_discord_message: Post message to Discord channel
                - create_discord_thread: Create discussion thread
            Backlog:
                - create_backlog_ticket: Create Backlog ticket
            Slack:
                - post_slack_message: Post message to Slack
        """

        try:
            # Parse input
            input_data = json.loads(tool_input)
            action = input_data.get('action')
            parameters = input_data.get('parameters', {})

            self.logger.info(f"Report tool action: {action}")

            # Discord actions (prioritized if USE_DISCORD=true)
            if action == 'post_discord_message' and self.use_discord:
                return self.post_discord_message(parameters)

            elif action == 'create_discord_thread' and self.use_discord:
                return self.create_discord_thread(parameters)

            # Backlog actions
            elif action == 'create_backlog_ticket' and self.use_backlog:
                return self.create_backlog_ticket(parameters)

            elif action == 'update_backlog_ticket' and self.use_backlog:
                # TODO: Implement update functionality
                return "Update Backlog ticket functionality not yet implemented"

            # Slack actions
            elif action == 'post_slack_message' and self.use_slack:
                return self.post_slack_message(parameters)

            # Auto-routing: if Discord is enabled, route generic actions to Discord
            elif action == 'post_message' and self.use_discord:
                return self.post_discord_message(parameters)

            elif action == 'create_ticket' and self.use_discord:
                # Map to Discord thread
                parameters['thread_name'] = parameters.get('summary', 'New Issue')
                parameters['message'] = parameters.get('description', '')
                return self.create_discord_thread(parameters)

            # Auto-routing: if Backlog is enabled
            elif action == 'create_ticket' and self.use_backlog:
                return self.create_backlog_ticket(parameters)

            # Auto-routing: if Slack is enabled
            elif action == 'post_message' and self.use_slack:
                return self.post_slack_message(parameters)

            else:
                available_services = []
                if self.use_discord:
                    available_services.append("Discord")
                if self.use_backlog:
                    available_services.append("Backlog")
                if self.use_slack:
                    available_services.append("Slack")

                if not available_services:
                    return "Error: No messaging service is configured. Please set USE_DISCORD=true or configure Backlog/Slack."

                return f"Unknown action '{action}' or service not enabled. Available services: {', '.join(available_services)}"

        except json.JSONDecodeError as e:
            error = f"Invalid JSON input: {str(e)}"
            self.logger.error(error)
            return error

        except Exception as e:
            self.logger.error(f"Error in report tool: {e}")
            return f"Error: {str(e)}"
