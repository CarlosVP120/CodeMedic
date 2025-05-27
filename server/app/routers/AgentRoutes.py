from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.models.models import GitHubIssue, GitHubCredentials
from app.services.AgentService import AgentService
from fastapi.responses import StreamingResponse


router = APIRouter(prefix="/fix", tags=["fix"])

class FixCodeRequest(BaseModel):
    github_credentials: GitHubCredentials
    issue_data: GitHubIssue

@router.post(path="/issue/structured")
async def fix_code_structured(fix_code_request: FixCodeRequest):
    """New endpoint using StructuredAgent with JsonOutputParser"""
    print("inside fix_code_structured")
    try:
        agent_service: AgentService = AgentService(fix_code_request.github_credentials, fix_code_request.issue_data)

        def structured_event_generator():
            try:
                for chunk in agent_service.fix_issue_structured():
                    yield chunk  # Already formatted as SSE
            except Exception as e:
                # Send final error in structured format
                import json
                error_response = {
                    "type": "final_response",
                    "data": {
                        "summary": f"Error: {str(e)}",
                        "status": "error",
                        "errors": [str(e)],
                        "rawContent": str(e)
                    }
                }
                yield f"data: {json.dumps(error_response)}\n\n"

        return StreamingResponse(
            structured_event_generator(), 
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*"
            }
        )
    except Exception as error:
        print(error)
        raise HTTPException(status_code=400, detail=str(error))

