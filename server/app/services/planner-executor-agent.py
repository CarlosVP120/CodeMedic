from langgraph.graph import StateGraph,START,END
from langchain_openai import AzureChatOpenAI
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel,Field
from typing import Tuple,Union
from typing_extensions import TypedDict
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
import asyncio
from dotenv import load_dotenv
import os
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_huggingface import HuggingFacePipeline
from app.services.tools.tools import *


# Define the plan and executor structure
class FixedCodeIssue(BaseModel):
    fixed_code: str


class PlanExecute(TypedDict):
    input: str
    plan: List[str]
    past_steps: List[Tuple[str, str]]
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
        fine_tune_Qwen3_llm = HuggingFacePipeline.from_model_id(
            model_id=model_id,
            task="text-generation",
            pipeline_kwargs={
                "max_new_tokens": 2048,
                "do_sample": False,
                "repetition_penalty": 1.03,
            }
        )
        self.structured_llm = fine_tune_Qwen3_llm.with_structured_output(FixedCodeIssue)

    async def run_plan_and_execute(self,github_issue):
        #Define diagnosis and action tools
        @tool
        def get_repo_files() -> list:
            """Get list of files in the repository"""
            return get_repository_file_names(
                self.github_credentials.token,
                self.github_credentials.repository_name
            )


        @tool
        def get_file_content(file_name: str) -> str:
            """Get content of a specific file from the repository"""
            print(f"🔧 DEBUG: Getting file content for {file_name}")
            return get_repository_file_content(
                self.github_credentials.token,
                self.github_credentials.repository_name,
                file_name
            )


        @tool
        def create_file(file_path: str, content: str) -> str:
            """Create or modify a local file with given content"""
            return create_or_modify_file_for_issue(file_path, content)


        @tool
        def create_new_branch(base_branch: str, new_branch: str) -> str:
            """Create a new branch from the specified base branch"""
            return create_branch(
                self.github_credentials.token,
                self.github_credentials.repository_name,
                base_branch,
                new_branch
            )


        @tool
        def update_file(file_path: str, new_content: str, commit_message: str, branch: str) -> str:
            """Update a file in the specified GitHub branch"""
            return update_file_in_branch(
                self.github_credentials.token,
                self.github_credentials.repository_name,
                file_path,
                new_content,
                commit_message,
                branch
            )


        @tool
        def create_pr(title: str, body: str, head_branch: str, base_branch: str) -> str:
            """Create a pull request with the changes"""
            return create_pull_request(
                self.github_credentials.token,
                self.github_credentials.repository_name,
                title,
                body,
                head_branch,
                base_branch
            )

        @tool
        def fix_code_issues(buggy_code:str)->dict:
            """Takes the code with bugs, Fixes the issues in the code and returns the corrected code"""
            messages = [
                SystemMessage(content="You're a an agent that is specialized on solving issues in python code"),
                HumanMessage(
                    content=f"Please find and solve the issue in the following python code: {buggy_code}"
                ),
            ]
            response:FixedCodeIssue=self.structured_llm.invoke(messages)
            return {"corrected_code":response.fixed_code}


        #set up tools
        tools=[get_repo_files,get_file_content,fix_code_issues,create_file,create_new_branch,update_file,create_pr]

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
            plan=state["plan"]
            task=plan[0]
            task_formatted=f"Executing step {task}"
            agent_response=await agent_executor.ainvoke({"messages":[("user",task_formatted)]})

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
        config = {"recursion_limit": 50}
        # Function to run the Plan-Execute agent

        #Input from the user
        inputs={"input":f"Fix the following github issue:{github_issue["issue_data"]}"}
        #Run the Plan_and_Execute agent asynchronously
        async for event in app.astream(inputs,config=config):
            print(event)

#Run the async function
if __name__=="__main__":

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

    github_credentials=GitHubCredentials(token="<your_token>", repository_name="Elcasvi/Code-Fixer-LLM-Agent")
    issue_data=IssueData(number=2,title="SyntaxError: invalid syntax",body="""I'm running missing_colon.py as follows:
    division(23, 0)
    
    but I get the following error:
    
    File "/Users/fuchur/Documents/24/git_sync/swe-agent-test-repo/tests/./missing_colon.py", line 4
    def division(a: float, b: float) -> float
    ^
    SyntaxError: invalid syntax""",state="open",created_at="2025-05-28T07:42:11.273Z",updated_at="2025-05-28T07:42:11.273Z")



    agent=PlanExecuteAgent(github_credentials)
    asyncio.run(agent.run_plan_and_execute(issue_data))