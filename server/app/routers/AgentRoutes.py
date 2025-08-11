from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.models.models import GitHubIssue, GitHubCredentials
from app.services.AgentService import AgentService


router = APIRouter(prefix="/fix", tags=["fix"])

class FixCodeRequest(BaseModel):
    github_credentials: GitHubCredentials
    issue_data: GitHubIssue

@router.post(path="/")
async def fix_code_structured(fix_code_request: FixCodeRequest):
    """New endpoint using StructuredAgent with JsonOutputParser"""
    try:
        agent_service: AgentService = AgentService(fix_code_request.github_credentials, fix_code_request.issue_data)
        agent_response=agent_service.fix_issue_structured()
        print("agent_response", agent_response)
        return agent_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
