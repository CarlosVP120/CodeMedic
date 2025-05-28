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


class PlanExecute(TypedDict):
    input: str
    plan: List[str]
    past_steps: List[Tuple[str, str]]
    github_credentials: Tuple[str, str]
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
        self.fine_tune_Qwen3_llm = HuggingFacePipeline.from_model_id(
            model_id=model_id,
            task="text-generation",
            pipeline_kwargs={
                "max_new_tokens": 2048,
                "do_sample": False,
                "repetition_penalty": 1.03,
            }
        )
        #self.structured_llm = fine_tune_Qwen3_llm.with_structured_output(FixedCodeIssue)

    async def run_plan_and_execute(self,github_issue):
        #Define diagnosis and action tools
        @tool
        def get_repository_file_names(github_token: str, repository: str) -> List[str]:
            """
            Returns the list of file names from the root of the given GitHub repository.
            """
            try:
                #print(f"\n🔍 Intentando acceder al repositorio: {repository}")
                github_client = Github(github_token)
                repo = github_client.get_repo(repository)
                #print("✓ Repositorio encontrado")
            except Exception as e:
                print(f"❌ Error al obtener issues: {str(e)}")
                return []

            contents = repo.get_contents("")
            files_list = []
            while contents:
                file_content = contents.pop(0)
                if file_content.type == "dir":
                    contents.extend(repo.get_contents(file_content.path))
                else:
                    files_list.append(file_content.name)
                    #print("File name: ", file_content.name)
            return files_list

        @tool
        def get_repository_file_content(github_token: str, repository: str, file_name: str) -> str:
            """
            Retrieves the content of a specific file from the GitHub repository.
            """
            try:
                #print(f"\n🔍 Intentando acceder al repositorio: {repository}")
                github_client = Github(github_token)
                repo = github_client.get_repo(repository)
                #print("✓ Repositorio encontrado")
            except Exception as e:
                return f"❌ Error al conectar con el repositorio: {str(e)}"

            try:
                #print("Trying to retrieve file content")
                content = repo.get_contents(file_name)
                #print("content file: ", content)
                return content.decoded_content.decode()
            except Exception as e:
                return f"Error al obtener el contenido del archivo: {str(e)}"

        @tool
        def create_branch(
                github_token: str,
                repository: str,
                base_branch: str,
                new_branch: str
        ) -> str:
            """
            Creates a new branch from the specified base branch.

            Args:
                github_token: GitHub access token.
                repository: Repository name in 'owner/repo' format.
                base_branch: The branch to branch off from (e.g., 'main').
                new_branch: The name of the new branch to create.

            Returns:
                The name of the created branch or an error message.
            """
            try:
                print(f"🌿 Creating branch '{new_branch}' from '{base_branch}' in repo '{repository}'")

                github_client = Github(github_token)
                repo = github_client.get_repo(repository)

                # Get the commit SHA of the base branch
                base_ref = repo.get_git_ref(f"heads/{base_branch}")
                base_sha = base_ref.object.sha

                # Create new branch ref
                new_ref = f"refs/heads/{new_branch}"
                repo.create_git_ref(ref=new_ref, sha=base_sha)

                print(f"✅ Branch '{new_branch}' created")
                return f"Branch '{new_branch}' created successfully"

            except GithubException as e:
                if e.status == 422:
                    return f"⚠️ Branch '{new_branch}' already exists."
                else:
                    print(f"❌ GitHub Exception: {e.data}")
                    return f"❌ GitHub error: {e.data.get('message', str(e))}"
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                return f"❌ Error: {str(e)}"

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

            Args:
                github_token: GitHub token for authentication.
                repository: Repo name in 'owner/repo' format.
                file_path: Path to the file to update.
                new_content: New content for the file (as a string).
                commit_message: Commit message for the change.
                branch: Branch name to commit to.

            Returns:
                Status message indicating success or error.
            """
            try:
                github_client = Github(github_token)
                repo = github_client.get_repo(repository)

                # Get the current file SHA (required to update the file)
                contents = repo.get_contents(file_path, ref=branch)
                current_sha = contents.sha

                # Commit the updated content
                repo.update_file(
                    path=file_path,
                    message=commit_message,
                    content=new_content,
                    sha=current_sha,
                    branch=branch
                )

                return f"✅ File '{file_path}' updated on branch '{branch}'"
            except Exception as e:
                print(f"❌ Error updating file: {str(e)}")
                return f"❌ Error: {str(e)}"

        @tool
        def create_pull_request(
                github_token: str,
                repository: str,
                title: str,
                body: str,
                head_branch: str,
                base_branch: str
        ) -> Any:
            """
            Creates a pull request with the given data.
            """
            try:
                print("📦 inside create_pull_request")
                print(repository)
                print(title)
                print(body)
                print(head_branch)
                print(base_branch)

                github_client = Github(github_token)
                repo = github_client.get_repo(repository)
                pull_request = repo.create_pull(
                    title=title,
                    body=body,
                    head=head_branch,
                    base=base_branch
                )
                print(f"✅ Pull request creado: {pull_request.html_url}")
                return pull_request.html_url
            except Exception as e:
                print(f"❌ Error al crear el pull request: {str(e)}")
                return str(e)

        @tool
        def fix_code_issues(buggy_code:str)->dict:
            """Takes the code with bugs, Fixes the issues in the code and returns the corrected code"""
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
            print("prompt: ",prompt)
            #result = self.fine_tune_Qwen3_llm.invoke([{"role": "user", "content": prompt}])
            result = llm_test.with_structured_output(FixedCodeIssue).invoke([{"role": "user", "content": prompt}])
            print("fine_tuned mode result: ",result)
            return result
            # try:
            #     print("json result: ",json.loads(result))
            #     return json.loads(result)
            # except json.JSONDecodeError:
            #     return {"error": "Invalid JSON output", "raw_output": result}


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
            Use create_new_branch() to create a new branch
            Use fix_code_issues() to solve the issues in the code
            Use update_file() to modify files on the new branch
            Use create_pr() to create a pull request,
            followed by creating the pull request as the final step.
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

        def should_end(state:PlanExecute):
            if "response" in state and state["response"]:
                return END
            else:
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
        config = {"recursion_limit": 5}
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

    github_credentials = GitHubCredentials(token="<your_token>",
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