from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.models.models import GitHubIssue, GitHubCredentials
from app.services.AgentService import AgentService
from fastapi.responses import StreamingResponse


router = APIRouter(prefix="/fix", tags=["fix"])

class FixCodeRequest(BaseModel):
    github_credentials: GitHubCredentials
    issue_data: GitHubIssue

@router.post(path="/issue")
async def fix_code(fix_code_request:FixCodeRequest):
    print("inside fix_code")
    try:
        agent_service: AgentService=AgentService(fix_code_request.github_credentials,fix_code_request.issue_data)

        def event_generator():
            try:
                for chunk in agent_service.fix_issue():  # This yields the values
                    yield f"{chunk}\n"  # Stream as plain text
            except Exception as e:
                yield f"Error: {str(e)}"

        return StreamingResponse(event_generator(), media_type="text/plain")
    except Exception as error:
        print(error)
        raise HTTPException(status_code=400, detail=str(error))

