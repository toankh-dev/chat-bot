"""
Code Review Tool for analyzing code

Supports:
- GitLab (merge requests, diffs)
- Discord (code snippets, discussions) - optional alternative
"""

import json
import logging
import os
import boto3
import requests
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class CodeReviewTool:
    """
    Tool for code reviews

    - GitLab: Full MR analysis with diffs
    - Discord: Share code snippets for discussion
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Check which service to use
        self.use_discord = os.getenv("USE_DISCORD", "false").lower() == "true"
        self.use_gitlab = os.getenv("USE_GITLAB", "false").lower() == "true"

        # Discord configuration
        if self.use_discord:
            self.discord_token = os.getenv("DISCORD_BOT_TOKEN")
            self.discord_base_url = "https://discord.com/api/v10"

        # GitLab configuration
        if self.use_gitlab:
            endpoint_url = os.getenv("LOCALSTACK_ENDPOINT")
            self.secrets_client = boto3.client(
                'secretsmanager',
                endpoint_url=endpoint_url,
                region_name=os.getenv("AWS_DEFAULT_REGION", "ap-southeast-1")
            )
            self._gitlab_secret = None

    def _get_gitlab_secret(self) -> Dict[str, str]:
        """Get GitLab credentials"""
        if self._gitlab_secret is None:
            response = self.secrets_client.get_secret_value(
                SecretId='/chatbot/gitlab/api-token'
            )
            self._gitlab_secret = json.loads(response['SecretString'])
        return self._gitlab_secret

    def get_merge_requests(self, params: Dict[str, Any]) -> str:
        """Get merge requests from GitLab"""
        try:
            secret = self._get_gitlab_secret()
            token = secret['token']
            base_url = secret['base_url']

            project_id = params.get('project_id')
            state = params.get('state', 'opened')

            url = f"{base_url}/projects/{project_id}/merge_requests"
            headers = {'PRIVATE-TOKEN': token}
            params_dict = {'state': state, 'per_page': 10}

            response = requests.get(url, headers=headers, params=params_dict, timeout=30)

            if response.status_code == 200:
                mrs = response.json()
                result = f"Found {len(mrs)} merge requests:\n\n"

                for mr in mrs[:5]:
                    result += f"- MR !{mr['iid']}: {mr['title']}\n"
                    result += f"  Author: {mr['author']['username']}\n"
                    result += f"  Status: {mr['state']}\n"
                    result += f"  URL: {mr['web_url']}\n\n"

                return result
            else:
                return f"Error fetching MRs: {response.status_code}"

        except Exception as e:
            self.logger.error(f"Error fetching merge requests: {e}")
            return f"Error: {str(e)}"

    def analyze_code(self, params: Dict[str, Any]) -> str:
        """Analyze code changes in a merge request"""
        # TODO: Implement actual code analysis with LLM
        return "Code analysis functionality not yet fully implemented"

    def post_code_snippet(self, params: Dict[str, Any]) -> str:
        """Post code snippet to Discord for review"""
        try:
            channel_id = params.get('channel_id')
            code = params.get('code', '')
            language = params.get('language', 'python')
            description = params.get('description', '')

            if not channel_id:
                return "Error: channel_id is required"

            if not code:
                return "Error: code is required"

            self.logger.info(f"Posting code snippet to Discord channel {channel_id}")

            # Format code with markdown
            message = f"{description}\n\n```{language}\n{code}\n```"

            url = f"{self.discord_base_url}/channels/{channel_id}/messages"
            headers = {
                'Authorization': f'Bot {self.discord_token}',
                'Content-Type': 'application/json'
            }

            response = requests.post(
                url,
                headers=headers,
                json={'content': message},
                timeout=30
            )
            response.raise_for_status()

            message_data = response.json()
            message_id = message_data.get('id')

            return (
                f"✅ Code snippet posted to Discord\n"
                f"Channel ID: {channel_id}\n"
                f"Message ID: {message_id}\n"
                f"Language: {language}"
            )

        except Exception as e:
            self.logger.error(f"Error posting code snippet: {e}")
            return f"Error posting code snippet: {str(e)}"

    def search_code_snippets(self, params: Dict[str, Any]) -> str:
        """Search for code snippets in Discord"""
        try:
            channel_id = params.get('channel_id')
            query = params.get('query', '')

            if not channel_id:
                return "Error: channel_id is required"

            self.logger.info(f"Searching code snippets in Discord channel {channel_id}")

            # Get recent messages
            url = f"{self.discord_base_url}/channels/{channel_id}/messages"
            headers = {
                'Authorization': f'Bot {self.discord_token}',
                'Content-Type': 'application/json'
            }

            response = requests.get(
                url,
                headers=headers,
                params={'limit': 100},
                timeout=30
            )
            response.raise_for_status()

            messages = response.json()

            # Filter messages with code blocks
            code_messages = []
            for msg in messages:
                content = msg.get('content', '')
                if '```' in content:  # Has code block
                    if not query or query.lower() in content.lower():
                        code_messages.append(msg)

            if not code_messages:
                return f"No code snippets found"

            result = f"Found {len(code_messages)} code snippets:\n\n"
            for i, msg in enumerate(code_messages[:5], 1):
                author = msg.get('author', {}).get('username', 'unknown')
                timestamp = msg.get('timestamp', '')[:10]
                content = msg.get('content', '')[:200]
                result += f"{i}. [{timestamp}] by {author}\n{content}...\n\n"

            return result

        except Exception as e:
            self.logger.error(f"Error searching code snippets: {e}")
            return f"Error searching code snippets: {str(e)}"

    def run(self, tool_input: str) -> str:
        """
        Run the tool

        Supported actions:
            Discord:
                - post_code_snippet: Share code for review
                - search_code_snippets: Find code snippets
            GitLab:
                - get_merge_requests: Get MRs
                - analyze_code: Analyze MR changes
        """
        try:
            input_data = json.loads(tool_input)
            action = input_data.get('action')
            parameters = input_data.get('parameters', {})

            self.logger.info(f"Code review tool action: {action}")

            # Discord actions
            if self.use_discord:
                if action == 'post_code_snippet':
                    return self.post_code_snippet(parameters)

                elif action == 'search_code_snippets':
                    return self.search_code_snippets(parameters)

                elif action == 'analyze_code':
                    return "Code analysis for Discord is not applicable. Use 'post_code_snippet' to share code for discussion."

            # GitLab actions
            elif self.use_gitlab:
                if action == 'get_merge_requests':
                    return self.get_merge_requests(parameters)

                elif action == 'analyze_code':
                    return self.analyze_code(parameters)

                elif action == 'check_standards':
                    return "Coding standards check not yet implemented"

            else:
                return "Error: No code review service configured. Set USE_DISCORD=true or USE_GITLAB=true"

            return f"Unknown action: {action}"

        except Exception as e:
            self.logger.error(f"Error in code review tool: {e}")
            return f"Error: {str(e)}"
