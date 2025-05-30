from langchain_openai import AzureChatOpenAI
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
import os

from app.models.models import GitHubIssue, GitHubCredentials,  FinalAgentOutput
from app.services.tools.tools import get_repository_file_names, get_repository_file_content, fix_code_issues, \
    create_branch, update_file_in_branch, create_pull_request


class ReactAgent:
    def __init__(self, github_credentials:GitHubCredentials):
        load_dotenv(dotenv_path=".env")
        self.github_credentials = github_credentials
        self.endpoint_gpt4 = os.getenv("AZURE_OPENAI_ENDPOINT_GPT4")

    def run(self, github_issue: GitHubIssue):

        # set up tools
        tools = [get_repository_file_names, get_repository_file_content, fix_code_issues, create_branch,update_file_in_branch, create_pull_request]

        llm = AzureChatOpenAI(
            azure_endpoint=self.endpoint_gpt4,
            azure_deployment="gpt-4o",
            api_version="2025-01-01-preview",
            temperature=0,
            max_tokens=1000,
            timeout=None,
            max_retries=2,
        )

        agent_graph = create_react_agent(model=llm, tools=tools)

        # Build messages input
        user_message = f"""Fix the following GitHub issue:\n{github_issue.model_dump_json(indent=2)}\n
        Use these credentials if needed:\n{self.github_credentials.model_dump_json(indent=2)}"""
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