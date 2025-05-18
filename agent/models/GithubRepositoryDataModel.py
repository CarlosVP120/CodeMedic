from github import Github
from pydantic import BaseModel
class GithubRepositoryData(BaseModel):
    client: Github
    repository:str

    class Config:
        arbitrary_types_allowed = True
