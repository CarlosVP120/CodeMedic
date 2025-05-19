from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any
import sys
from datetime import datetime
import os

# Add the project root and agent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'agent'))

# Now we can import with relative paths
from agent.ollama_langgraph_agent import main as agent_main
from agent.models.models import GitHubIssue

router = APIRouter()

@router.post("/fix")
async def fix_code(issue: GitHubIssue):
    try:
        # Call the agent's main function with the issue
        result = agent_main(issue)
        return {"result": "Issue processing started", "details": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    

