# from langchain_openai import AzureChatOpenAI
from langchain_huggingface import HuggingFaceEndpoint, HuggingFacePipeline, ChatHuggingFace
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
import os

from app.models.models import GitHubIssue, GitHubCredentials,  FinalAgentOutput
from app.models.agent_response import AgentResponse
from app.services.tools.tools import get_repository_file_names, get_repository_file_content, fix_code_issues, \
    create_branch, update_file_in_branch, create_pull_request


class ReactAgent:
    def __init__(self, github_credentials:GitHubCredentials):
        load_dotenv(dotenv_path=".env")
        self.github_credentials = github_credentials

    def run(self, github_issue: GitHubIssue):

        # set up tools
        tools = [get_repository_file_names, get_repository_file_content, fix_code_issues, create_branch,update_file_in_branch, create_pull_request]

        # Get HuggingFace token from environment
        hf_token = os.getenv("HUGGINGFACE_HUB_TOKEN")
        if not hf_token:
            raise ValueError("HuggingFace token not found in environment variables")
        

        # Create base LLM with authentication
        base_llm = HuggingFaceEndpoint(
            model="Qwen/Qwen3-4B",
            task="text-generation",
            max_new_tokens=1000,  # Increased token limit
            do_sample=False,
            repetition_penalty=1.03,
            temperature=0.1,  # Lower temperature for more consistent behavior
            huggingfacehub_api_token=hf_token  # Add the API token
        )
        
        # Wrap it with ChatHuggingFace for tool support
        llm = ChatHuggingFace(llm=base_llm)

        agent_graph = create_react_agent(model=llm, tools=tools)

        # Build messages input
        user_message = f"""You are a GitHub issue assistant. Your task is to analyze and fix the following GitHub issue.

ISSUE DETAILS:
{github_issue.model_dump_json(indent=2)}

GITHUB CREDENTIALS:
{self.github_credentials.model_dump_json(indent=2)}

INSTRUCTIONS:
1. First, examine the repository structure using get_repository_file_names
2. Analyze the issue description and identify the problem
3. Look at relevant files using get_repository_file_content
4. Create a solution plan
5. If code changes are needed, create a branch, update files, and create a pull request
6. Provide a clear summary of what was done

Focus only on the GitHub issue provided. Do not discuss other topics or provide general explanations about tools or libraries."""
        inputs = {"messages": [("user", user_message)]}

        # Configure with a thread id
        config = {"configurable": {"thread_id": f"issue-{github_issue.number}"}}

        # Run the agent and print messages
        result = agent_graph.invoke(inputs, config=config)
        formatted_messages = [msg.content for msg in result["messages"]]
        output = FinalAgentOutput(
            messages=formatted_messages,
            summary=formatted_messages[-1]  # or generate your own summary
        )
        return output