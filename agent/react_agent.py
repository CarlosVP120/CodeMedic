import json
from langgraph.graph import StateGraph,START,END
from langchain_openai import AzureChatOpenAI
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel,Field
from typing import Tuple, Union, List, Any
from typing_extensions import TypedDict
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
import asyncio
from dotenv import load_dotenv
import os
from langchain_huggingface import HuggingFacePipeline
from github import Github
from github.GithubException import GithubException


class FinalAgentOutput(BaseModel):
    messages: List[str]
    summary: str  # Optional: a natural language summary


class GitHubCredentials(BaseModel):
    token: str
    repository_name: str

class IssueData(BaseModel):
    number: int
    title: str
    body: str
    state: str
    created_at: str
    updated_at: str

class FixedCodeIssue(BaseModel):
    fixed_code: str

class ReactAgent:
    def __init__(self, github_credentials):
        load_dotenv(dotenv_path=".env")
        self.github_credentials = github_credentials
        self.endpoint_gpt4 = os.getenv("AZURE_OPENAI_ENDPOINT_GPT4")

    def run(self, github_issue: IssueData):

        @tool
        def get_repository_file_names(github_token: str, repository: str) -> str:
            """
            Returns the list of file names from the root of the given GitHub repository.
            """
            print("Inside get_repository_file_names")
            try:
                github_client = Github(github_token)
                repo = github_client.get_repo(repository)
                contents = repo.get_contents("")
                files_list = []
                while contents:
                    file_content = contents.pop(0)
                    if file_content.type == "dir":
                        contents.extend(repo.get_contents(file_content.path))
                    else:
                        files_list.append(file_content.name)
                return f"📄 Repository contains the following files: {', '.join(files_list)}"
            except Exception as e:
                return f"❌ Error retrieving files: {str(e)}"

        @tool
        def get_repository_file_content(github_token: str, repository: str, file_name: str) -> str:
            """
            Retrieves the content of a specific file from the GitHub repository.
            """
            print("Inside get_repository_file_content")
            try:
                github_client = Github(github_token)
                repo = github_client.get_repo(repository)
                content = repo.get_contents(file_name)
                return f"📄 The file `{file_name}` contains:\n\n```python\n{content.decoded_content.decode()}\n```"
            except Exception as e:
                return f"❌ Error getting file content: {str(e)}"

        @tool
        def create_branch(github_token: str, repository: str, base_branch: str, new_branch: str) -> str:
            """
            Creates a new branch from the specified base branch.
            """
            print("Inside create_branch")
            try:
                github_client = Github(github_token)
                repo = github_client.get_repo(repository)
                base_ref = repo.get_git_ref(f"heads/{base_branch}")
                base_sha = base_ref.object.sha
                new_ref = f"refs/heads/{new_branch}"
                repo.create_git_ref(ref=new_ref, sha=base_sha)
                return f"✅ Branch `{new_branch}` created from `{base_branch}` in `{repository}`"
            except GithubException as e:
                if e.status == 422:
                    return f"⚠️ Branch `{new_branch}` already exists."
                return f"❌ GitHub error: {e.data.get('message', str(e))}"
            except Exception as e:
                return f"❌ Error creating branch: {str(e)}"

        @tool
        def update_file_in_branch(
                github_token: str,
                repository: str,
                file_path: str,
                new_content: str,
                commit_message: str,
                branch: str
        ) -> str:
            """
            Updates a file in the specified GitHub branch.
            """
            print("Inside update_file_in_branch")
            try:
                github_client = Github(github_token)
                repo = github_client.get_repo(repository)
                contents = repo.get_contents(file_path, ref=branch)
                current_sha = contents.sha

                repo.update_file(
                    path=file_path,
                    message=commit_message,
                    content=new_content,
                    sha=current_sha,
                    branch=branch
                )
                return f"✅ File `{file_path}` updated on branch `{branch}` with commit message: '{commit_message}'"
            except Exception as e:
                return f"❌ Error updating file: {str(e)}"

        @tool
        def create_pull_request(
                github_token: str,
                repository: str,
                title: str,
                body: str,
                head_branch: str,
                base_branch: str
        ) -> str:
            """
            Creates a pull request with the given data.
            """
            print("Inside create_pull_request")
            try:
                github_client = Github(github_token)
                repo = github_client.get_repo(repository)
                pull_request = repo.create_pull(
                    title=title,
                    body=body,
                    head=head_branch,
                    base=base_branch
                )
                return f"✅ Pull request created: {pull_request.html_url}"
            except Exception as e:
                return f"❌ Error creating pull request: {str(e)}"

        @tool
        def fix_code_issues(buggy_code: str) -> dict:
            """
                Analyzes the given Python code for syntax or logical errors and returns a corrected version.

                This tool uses a fine-tuned language model to automatically fix issues in the provided code snippet.
                It returns the result as a JSON dictionary in the format: { "fixed_code": "..." }.

                Args:
                    buggy_code (str): A Python code snippet that contains one or more errors.

                Returns:
                    dict: A dictionary containing the corrected version of the code. If the model fails to produce valid JSON,
                          an error message is included in the output.
                """
            print("inside fix_code_issues...")
            llm_test = AzureChatOpenAI(
                azure_endpoint=self.endpoint_gpt4,
                azure_deployment="gpt-4o",
                api_version="2025-01-01-preview",
                temperature=0,
                max_tokens=1000,
                timeout=None,
                max_retries=2,
            )
            prompt = f"""
                       Fix the following buggy Python code. Respond only with JSON using this format:
                       {{ "fixed_code": "..." }}

                       Code:
                       {buggy_code}
                    """
            print("prompt: ", prompt)
            result = llm_test.with_structured_output(FixedCodeIssue).invoke([{"role": "user", "content": prompt}])
            print("fine_tuned mode result: ", result)
            return result

        # set up tools
        tools = [get_repository_file_names, get_repository_file_content, fix_code_issues, create_branch,update_file_in_branch, create_pull_request]

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an AI GitHub issues fixer assistant."),
            ("user", f"""Fix the following GitHub issue:
            {github_issue.model_dump_json(indent=2)}\n
            Use these credentials if needed: {self.github_credentials.model_dump_json(indent=2)}""")
        ])

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
        # for msg in result["messages"]:
        #     print(msg.content)
        return output
# Run the agent
if __name__ == "__main__":
    github_credentials = GitHubCredentials(
        token="token",
        repository_name="Elcasvi/Code-Fixer-LLM-Agent"
    )
    issue_data = IssueData(
        number=2,
        title="SyntaxError: invalid syntax",
        body="""I'm running missing_colon.py as follows:
    division(23, 0)

    but I get the following error:

    File "/Users/fuchur/Documents/24/git_sync/swe-agent-test-repo/tests/./missing_colon.py", line 4
    def division(a: float, b: float) -> float
    ^
    SyntaxError: invalid syntax""",
        state="open",
        created_at="2025-05-28T07:42:11.273Z",
        updated_at="2025-05-28T07:42:11.273Z"
    )
    agent = ReactAgent(github_credentials)
    output=agent.run(issue_data)
    print("output: ",output)
