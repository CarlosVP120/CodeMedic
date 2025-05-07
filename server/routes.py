from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.fixer import CodeFixerAgent

router = APIRouter()
agent = CodeFixerAgent()

class FixRequest(BaseModel):
    code: str = Field(..., min_length=1, description="The OOP code to be fixed")
    log: Dict[str, Any] = Field(..., description="Structured log information")

@router.post("/fix")
async def fix_code(req: FixRequest):
    try:
        fixed = agent.fix_code(req.code, "OOP", req.log)
        return {"fixed_code": fixed}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    

