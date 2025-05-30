from fastapi import HTTPException
from app.models.models import GitHubIssue, GitHubCredentials
from app.services.ReactAgent import ReactAgent


class AgentService:
    def __init__(self, github_credentials: GitHubCredentials, issue_data: GitHubIssue):
        self.issue_data = issue_data
        self.github_credentials = github_credentials
    
    def fix_issue_structured(self):
        """New fix_issue method using StructuredAgent with JsonOutputParser"""
        try:
            react_agent = ReactAgent(self.github_credentials)
            agent_response=react_agent.run(self.issue_data)
            return agent_response
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
                
