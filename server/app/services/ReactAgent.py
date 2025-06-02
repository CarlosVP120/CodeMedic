from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
import os
import functools

from app.models.models import GitHubIssue, GitHubCredentials,  FinalAgentOutput
# Import tools directly first to test
from app.services.tools.tools import (
    get_repository_file_names, 
    get_repository_file_content, 
    fix_code_issues,
    create_branch, 
    update_file_in_branch, 
    create_pull_request
)

tool_path_log = []

# Decorator to log tool usage
def log_tool_call(tool_func):
    @functools.wraps(tool_func)  # This preserves the original function's metadata
    def wrapper(*args, **kwargs):
        tool_path_log.append(tool_func.__name__)
        print(f"🔧 Tool called: {tool_func.__name__}")
        return tool_func(*args, **kwargs)
    return wrapper


class ReactAgent:
    def __init__(self, github_credentials:GitHubCredentials):
        env_path = 'app/.env'
        load_dotenv(env_path)
        self.hf_token =os.getenv("HUGGINGFACEHUB_API_TOKEN")
        self.github_credentials = github_credentials

    def run(self, github_issue: GitHubIssue):
        # Clear the tool log for this run
        global tool_path_log
        tool_path_log = []

        # Use original tools without modification for now
        tools = [
            get_repository_file_names,
            get_repository_file_content,
            fix_code_issues,
            create_branch,
            update_file_in_branch,
            create_pull_request
        ]
        # Create base LLM with authentication
        base_llm = HuggingFaceEndpoint(
            model="Qwen/Qwen3-4B",
            task="text-generation",
            max_new_tokens=1000,  # Increased token limit
            do_sample=False,
            repetition_penalty=1.03,
            temperature=0.1,  # Lower temperature for more consistent behavior
            huggingfacehub_api_token=self.hf_token  # Add the API token
        )
        
        # Wrap it with ChatHuggingFace for tool support
        llm = ChatHuggingFace(llm=base_llm)

        agent_graph = create_react_agent(model=llm, tools=tools)

        # Build messages input
        user_message = f"""You are a GitHub issue assistant specialized in fixing code problems. Your task is to analyze and fix the following GitHub issue.

ISSUE DETAILS:
{github_issue.model_dump_json(indent=2)}

GITHUB CREDENTIALS:
{self.github_credentials.model_dump_json(indent=2)}

MANDATORY INSTRUCTIONS (FOLLOW EXACTLY):
1. First, examine the repository structure using get_repository_file_names
2. Analyze the issue description and identify the problematic file(s)
3. Use get_repository_file_content to read the file(s) that contain the issue
4. **MANDATORY**: Once you identify buggy code, you MUST use fix_code_issues tool to fix the code problems
5. Create a new branch using create_branch with a descriptive name
6. Update the fixed code in the branch using update_file_in_branch with the corrected code from fix_code_issues
7. Create a pull request using create_pull_request with the fix

CRITICAL REQUIREMENTS:
- You MUST use fix_code_issues tool for any code that has syntax errors, logical errors, or bugs
- Do NOT manually fix code - always use the fix_code_issues tool first
- The fix_code_issues tool will analyze and return the corrected code
- Only proceed with file updates after getting the fixed code from fix_code_issues tool

Focus only on the GitHub issue provided. Always use the fix_code_issues tool when dealing with code problems."""
        inputs = {"messages": [("user", user_message)]}

        # Configure with a thread id
        config = {"configurable": {"thread_id": f"issue-{github_issue.number}"}}

        # Run the agent and print messages
        result = agent_graph.invoke(inputs, config=config)
        formatted_messages = [msg.content for msg in result["messages"]]
        
        # Extract tool usage from agent messages
        used_tools = self._extract_tools_from_messages(result["messages"])
        
        # Create output with extracted tool usage
        output = FinalAgentOutput(
            messages=formatted_messages,
            summary=formatted_messages[-1] if formatted_messages else "No response generated",
            tool_path=used_tools
        )
        
        print(f"\n🔧 Tools used in this execution: {used_tools}")
        return output
    
    def _extract_tools_from_messages(self, messages):
        """Extract tool usage from agent messages"""
        used_tools = []
        tool_names = [
            "get_repository_file_names",
            "get_repository_file_content", 
            "fix_code_issues",
            "create_branch",
            "update_file_in_branch", 
            "create_pull_request"
        ]
        
        for message in messages:
            message_content = str(message.content)
            for tool_name in tool_names:
                if tool_name in message_content and tool_name not in used_tools:
                    used_tools.append(tool_name)
        
        return used_tools