"""
Code Review Tool for analyzing GitLab code
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
    Tool for reviewing GitLab code
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

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

    def run(self, tool_input: str) -> str:
        """Run the tool"""
        try:
            input_data = json.loads(tool_input)
            action = input_data.get('action')
            parameters = input_data.get('parameters', {})

            self.logger.info(f"Code review tool action: {action}")

            if action == 'get_merge_requests':
                return self.get_merge_requests(parameters)

            elif action == 'analyze_code':
                return self.analyze_code(parameters)

            elif action == 'check_standards':
                return "Coding standards check not yet implemented"

            else:
                return f"Unknown action: {action}"

        except Exception as e:
            self.logger.error(f"Error in code review tool: {e}")
            return f"Error: {str(e)}"
