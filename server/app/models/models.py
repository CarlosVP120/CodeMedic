from datetime import datetime
from typing import List

from pydantic import BaseModel
class FileEditInput(BaseModel):
    file_path: str
    content: str


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

class FinalAgentOutput(BaseModel):
    messages: List[str]
    summary: str
class FixedCodeIssue(BaseModel):
    fixed_code: str