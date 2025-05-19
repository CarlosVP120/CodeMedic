from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any
import sys
from datetime import datetime
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.fixer import CodeFixerAgent

router = APIRouter()
agent = CodeFixerAgent()

class GitHubIssue(BaseModel):
    number: int
    title: str
    body: str
    state: str
    created_at: datetime
    updated_at: datetime

@router.post("/fix")
async def fix_code(req: GitHubIssue):
    try:
        fixed = agent.fix_code(req.code, "OOP", req.log)
        return {"fixed_code": fixed}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    

