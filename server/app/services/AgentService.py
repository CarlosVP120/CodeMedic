from fastapi import HTTPException
from app.models.models import GitHubIssue, GitHubCredentials
from app.services.StructuredAgent import StructuredAgent
from typing import Generator, Dict, Any
import json


class AgentService:
    def __init__(self, github_credentials: GitHubCredentials, issue_data: GitHubIssue):
        self.issue_data = issue_data
        self.github_credentials = github_credentials
    
    def fix_issue_structured(self) -> Generator[str, None, None]:
        """New fix_issue method using StructuredAgent with JsonOutputParser"""
        try:
            print("Inside fix_issue_structured")
            structured_agent = StructuredAgent(self.github_credentials)
            
            # Stream the structured responses
            for response in structured_agent.fix_github_issue(self.issue_data):
                # Convert response to JSON string for streaming
                response_json = json.dumps(response)
                print(f"Streaming response: {response_json}")
                yield f"data: {response_json}\n\n"
                
        except Exception as e:
            # Send error response in structured format
            error_response = {
                "type": "final_response",
                "data": {
                    "summary": f"Internal server error: {str(e)}",
                    "status": "error",
                    "errors": [str(e)],
                    "rawContent": str(e)
                }
            }
            error_json = json.dumps(error_response)
            print(f"Error response: {error_json}")
            yield f"data: {error_json}\n\n"
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")