# Add the project root and agent directory to Python path
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'agent'))

# Now we can import with relative paths
# from agent.ollama_langgraph_agent import main as agent_main
# from agent.models.models import GitHubIssue

from fastapi import APIRouter, HTTPException
import sys
import os
import io
import contextlib



router = APIRouter()

@router.post("/fix")
async def fix_code(issue: GitHubIssue):
    try:
        # Capture stdout to get the full agent output
        output_buffer = io.StringIO()
        with contextlib.redirect_stdout(output_buffer):
            # Call the agent's main function with the issue
            result = agent_main(issue)
        
        # Get the captured output
        agent_output = output_buffer.getvalue()
        
        # Add the full output to the response
        result_with_output = {
            "result": "Issue processing started",
            "details": result,
            "agent_output": agent_output
        }
        
        return result_with_output
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    

