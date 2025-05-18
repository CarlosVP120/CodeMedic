from datetime import datetime
from pydantic import BaseModel

class GitHubIssue(BaseModel):
    number: int
    title: str
    body: str
    state: str
    created_at: datetime
    updated_at: datetime

    def __str__(self):
        return f"""
        GitHubIssue(
        number: ${self.number},
        title: ${self.title},
        body: ${self.body},
        state: ${self.state},
        created_at: ${self.created_at},
        updated_at: ${self.updated_at})
        )
        """
