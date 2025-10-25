"""
Report Tool for creating Backlog tickets and posting to Slack
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
    Tool for report operations (Backlog tickets, Slack messages)
    """

    def __init__(self):
        """Initialize the report tool"""
        self.logger = logging.getLogger(__name__)

        # LocalStack or real AWS
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

    def run(self, tool_input: str) -> str:
        """
        Run the tool

        Args:
            tool_input: JSON string with action and parameters

        Returns:
            Result message
        """

        try:
            # Parse input
            input_data = json.loads(tool_input)
            action = input_data.get('action')
            parameters = input_data.get('parameters', {})

            self.logger.info(f"Report tool action: {action}")

            # Route to appropriate function
            if action == 'create_backlog_ticket':
                return self.create_backlog_ticket(parameters)

            elif action == 'update_backlog_ticket':
                # TODO: Implement update functionality
                return "Update Backlog ticket functionality not yet implemented"

            elif action == 'post_slack_message':
                return self.post_slack_message(parameters)

            else:
                return f"Unknown action: {action}"

        except json.JSONDecodeError as e:
            error = f"Invalid JSON input: {str(e)}"
            self.logger.error(error)
            return error

        except Exception as e:
            self.logger.error(f"Error in report tool: {e}")
            return f"Error: {str(e)}"
