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

# Define the plan and executor structure

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


class PlanExecute(TypedDict, total=False):  # `total=False` makes all fields optional
    input: str
    plan: List[str]
    past_steps: List[Tuple[str, str]]
    github_credentials: Tuple[str, str]
    fixed_code: str
    file_path: str
    branch_name: str
    response: str


class Plan(BaseModel):
    steps: List[str] = Field(description="Task to check and resolve code issues")


class Response(BaseModel):
    response: str


class Act(BaseModel):
    action: Union[Response, Plan] = Field(description="Action to execute if you want to response to user, use Response")


class PlanExecuteAgent:
    def __init__(self,github_credentials):
        load_dotenv(dotenv_path=".env")
        self.github_credentials = github_credentials
        self.endpoint_gpt4 = os.getenv("AZURE_OPENAI_ENDPOINT_GPT4")
        model_id = "TheCasvi/Qwen3-1.7B-35KD-adapter"
        # self.fine_tune_Qwen3_llm = HuggingFacePipeline.from_model_id(
        #     model_id=model_id,
        #     task="text-generation",
        #     pipeline_kwargs={
        #         "max_new_tokens": 2048,
        #         "do_sample": False,
        #         "repetition_penalty": 1.03,
        #     }
        # )
        #self.structured_llm = fine_tune_Qwen3_llm.with_structured_output(FixedCodeIssue)

    async def run_plan_and_execute(self,github_issue):
        #Define diagnosis and action tools
        @tool
        def get_repository_file_names(github_token: str, repository: str) -> str:
            """
            Returns the list of file names from the root of the given GitHub repository.
            """
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


        #set up tools
        tools=[get_repository_file_names,get_repository_file_content,fix_code_issues,create_branch,update_file_in_branch,create_pull_request]

        #set up the model and agent executor
        prompt=ChatPromptTemplate.from_messages(
            [
                ("system","You are an github issues fixer agent"),
                ("placeholder","{messages}")
            ]
        )

        llm = AzureChatOpenAI(
                    azure_endpoint=self.endpoint_gpt4,
                    azure_deployment="gpt-4o",
                    api_version="2025-01-01-preview",
                    temperature=0,
                    max_tokens=1000,
                    timeout=None,
                    max_retries=2,
        )


        agent_executor = create_react_agent(llm, tools, state_modifier=prompt)

        #Planning steps
        planner_prompt = ChatPromptTemplate.from_messages(
         [
         ("system", """You are CodeMedic, an AI assistant that fixes GitHub issues.
            For the given GitHub issue, create a step-by-step solution plan including:
            Use get_repo_files() to understand repository structure
            Use get_file_content() to read relevant files
            Use create_new_branch() to create a new branch where the fix issue will be uploaded
            Use fix_code_issues() to solve the issues in the code
            Use update_file() to modify files with the solved code issues on the new branch
            Use create_pr() to create a pull request with the github issue
            If you don't create a PR, the fix is incomplete."""),

         ("placeholder", "{messages}"),
         ]
         )
        planner=planner_prompt|llm.with_structured_output(Plan)
        #Replanning steps
        replanner_prompt = ChatPromptTemplate.from_template(
         """For the given task, update the plan based on the current results:
         Your original task was:
         {input}
         You have completed the following steps:
         {past_steps}
         Update the plan accordingly. Only include the remaining tasks.If code needs to be regenerated, or more files need to be updated, adjust the plan accordingly."""
         )
        replanner=replanner_prompt|llm.with_structured_output(Act)

        #Execution step function
        async def execute_step(state:PlanExecute)->dict:
            print("Inside execute_step")
            print("state: ",state)
            plan=state["plan"]
            task=plan[0]
            task_formatted=f"""Solve the following task: {task}\n use the following github credentials if needed: {state["github_credentials"]}"""
            agent_response = await agent_executor.ainvoke({
                "messages": [
                    ("user", task_formatted)
                ],
            })

            past_steps = state.get("past_steps", [])
            past_steps.append((task, agent_response["messages"][-1].content))

            return {
                "past_steps": past_steps,
                "plan": plan[1:],  # remove the executed step
            }

        #Planning step function
        async def plan_step(state: PlanExecute):
            plan = await planner.ainvoke({"messages": [("user", state["input"])]})
            return {"plan": plan.steps}

        #Replanning step function()In case execution needs something)
        async def replan_step(state:PlanExecute):
            output = await replanner.ainvoke({
                "input": state["input"],
                "past_steps": state["past_steps"]
            })

            #if the replanner decides to return an response, we use it as the final answer
            if isinstance(output.action,Response):#final response provided
                return {"response":output.action.response}
            else:
                #Otherwise we continue with the new plan
                return {"plan":output.action.steps}

        def should_end(state: PlanExecute):
            if not state.get("plan"):
                return END
            if state.get("response"):
                return END
            return "agent"


        # Build the workflow
        workflow = StateGraph(PlanExecute)
        workflow.add_node("planner", plan_step)
        workflow.add_node("agent", execute_step)
        workflow.add_node("replan", replan_step)
        # Add edges to transition between nodes
        workflow.add_edge(START, "planner")
        workflow.add_edge("planner", "agent")
        workflow.add_edge("agent", "replan")
        workflow.add_conditional_edges("replan", should_end, ["agent", END])
        # Compile the workflow into executable application
        app = workflow.compile()
        config = {"recursion_limit": 10}
        # Function to run the Plan-Execute agent

        #Input from the user
        inputs = {
            "input": f"Fix the following issue:\n{issue_data.model_dump_json(indent=2)}\n",
            "github_credentials": (
                self.github_credentials.repository_name,
                self.github_credentials.token
            )
        }




        #Run the Plan_and_Execute agent asynchronously
        async for event in app.astream(inputs,config=config):
            print(event)

#Run the async function
if __name__=="__main__":

    github_credentials = GitHubCredentials(token="token",
                                           repository_name="Elcasvi/Code-Fixer-LLM-Agent")
    issue_data = IssueData(number=2, title="SyntaxError: invalid syntax", body="""I'm running missing_colon.py as follows:
    division(23, 0)

    but I get the following error:

    File "/Users/fuchur/Documents/24/git_sync/swe-agent-test-repo/tests/./missing_colon.py", line 4
    def division(a: float, b: float) -> float
    ^
    SyntaxError: invalid syntax""", state="open", created_at="2025-05-28T07:42:11.273Z",
                           updated_at="2025-05-28T07:42:11.273Z")

    agent = PlanExecuteAgent(github_credentials)
    asyncio.run(agent.run_plan_and_execute(issue_data))