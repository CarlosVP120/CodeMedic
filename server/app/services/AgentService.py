from fastapi import HTTPException
from app.models.models import GitHubIssue, GitHubCredentials
from app.services.Agent import Agent


class AgentService:
    def __init__(self, github_credentials:GitHubCredentials,issue_data: GitHubIssue):
        print("Inside Agent Controller")
        self.issue_data = issue_data
        self.github_credentials = github_credentials

    def fix_issue(self):
        try:
            print("Inside fix_issue")
            agent=Agent(self.github_credentials)
            agent_output=agent.fix_github_issue(self.issue_data)
            print("agent_output: ",agent_output)
            return agent_output
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")