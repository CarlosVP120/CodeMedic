from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class AgentResponse(BaseModel):
    """Structured response from the CodeMedic agent"""
    
    summary: str = Field(
        description="Brief summary of what was accomplished or the current status"
    )
    
    solution: Optional[str] = Field(
        default=None,
        description="Detailed explanation of the solution implemented"
    )
    
    files_modified: Optional[List[str]] = Field(
        default=None,
        description="List of files that were created or modified"
    )
    
    pull_request_url: Optional[str] = Field(
        default=None,
        description="URL of the created pull request if applicable"
    )
    
    branch_name: Optional[str] = Field(
        default=None,
        description="Name of the branch created for the fix"
    )
    
    errors: Optional[List[str]] = Field(
        default=None,
        description="List of errors encountered during the process"
    )
    
    status: Literal["success", "error", "partial"] = Field(
        description="Overall status of the operation"
    )
    
    next_steps: Optional[List[str]] = Field(
        default=None,
        description="Recommended next steps or actions to take"
    )

class AgentStepResponse(BaseModel):
    """Response for individual steps during agent execution"""
    
    step: str = Field(description="Description of the current step")
    status: Literal["in_progress", "completed", "failed"] = Field(description="Status of this step")
    details: Optional[str] = Field(default=None, description="Additional details about this step") 