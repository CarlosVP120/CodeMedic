from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
class FileEditInput(BaseModel):
    file_path: str
    content: str

class IssueAnalysis(BaseModel):
    number: int
    summary: str
    impact: str
    affected_areas: List[str]
    recommendations: List[str]
    technical_details: Optional[Dict[str, Any]]
    solution: Optional[str]

class GitHubIssue(BaseModel):
    number: int
    title: str
    body: str
    state: str
    created_at: datetime
    updated_at: datetime

class GitHubCredentials(BaseModel):
    token: str
    repository_name:str

class GetRepositoryFileContentInput(BaseModel):
    github_credentials: GitHubCredentials
    file_name: str

class PullRequest(BaseModel):
    title: str
    body: str
    head_branch: str
    base_branch: str
    issue_number: int

class CreateOrModifyFileInput(BaseModel):
    file_path: str
    content: str

class CreatePullRequestInput(BaseModel):
    pull_request_data: PullRequest
    github_credentials: GitHubCredentials

