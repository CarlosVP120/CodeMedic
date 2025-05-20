from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from app.models.models import*
from github import Github
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint, HuggingFacePipeline
from langchain_openai import AzureChatOpenAI
import os
from dotenv import load_dotenv

from app.services.tools.tools import *


class Agent:
    def __init__(self,github_credentials:GitHubCredentials):
        self.github_credentials = github_credentials


    def fix_github_issue(self,issue_data:GitHubIssue):
        # Inicializar cliente de GitHub
        try:
            print("\n🔍 Verificando conexión con GitHub...")
            github_client = Github(self.github_credentials.token)

            # Verificar token y usuario
            try:
                user = github_client.get_user()
                print(f"✓ Conectado como: {user.login}")
            except Exception as user_error:
                print(f"\n❌ Error al verificar el token: {str(user_error)}")
                print("El token podría estar expirado o ser inválido")
                raise

            print("\n✓ Conexión con GitHub establecida correctamente")

        except Exception as e:
            print(f"\n❌ Error general: {str(e)}")
            raise ValueError(f"Error al conectar con GitHub: {str(e)}")


        tools=[get_repository_file_names,get_repository_file_content,create_or_modify_file_for_issue,create_branch,update_file_in_branch,create_pull_request]

        # ---- LLM Setup ----
        load_dotenv(dotenv_path=".env")
        load_dotenv()
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT_GPT4")
        model = AzureChatOpenAI(
            azure_endpoint=endpoint,
            azure_deployment="gpt-4o",
            api_version="2025-01-01-preview",
            temperature=0,
            max_tokens=1000,
            timeout=None,
            max_retries=2,
            api_key=api_key
        )

        # """
        # Set a env var in deployment, adding the HUGGINGFACEHUB_API_TOKEN
        # """
        # llm = HuggingFaceEndpoint(
        #     model="Qwen/Qwen3-4B",
        #     task="text-generation",
        #     max_new_tokens=512,
        #     do_sample=False,
        #     repetition_penalty=1.03
        # )
        # model = ChatHuggingFace(llm=llm)

        # model_id = "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"
        # llm = HuggingFacePipeline.from_model_id(
        #     model_id=model_id,
        #     task="text-generation",
        #     pipeline_kwargs={
        #         "max_new_tokens": 512,
        #         "repetition_penalty": 1.03,
        #     }
        # )
        # model = ChatHuggingFace(llm=llm, model_id=model_id)

        # model_id = "TheCasvi/Qwen3-1.7B-35KD"
        # llm = HuggingFacePipeline.from_model_id(
        #     model_id=model_id,
        #     task="text-generation",
        #     pipeline_kwargs={
        #         "max_new_tokens": 4096,
        #         "repetition_penalty": 1.03,
        #     }
        # )
        # model = ChatHuggingFace(llm=llm, model_id=model_id)

        checkpointer = MemorySaver()
        graph = create_react_agent(
            model=model,
            tools=tools,
            checkpointer=checkpointer
        )

        initial_messages = [
            ("system", """You are an AI assistant that must use tools to answer questions.
            You are provided with the following tools:
            - get_repository_file_names(github_token, repository)
            - get_repository_file_content(github_token, repository, file_name)
            - create_or_modify_file_for_issue(file_path, content)
            - create_branch(github_token,repository: ,base_branch, new_branch)
            - update_file_in_branch( github_token ,repository ,file_path ,new_content ,commit_message ,branch)
            - create_pull_request(github_token, repository, title, body, head_branch, base_branch, issue_number)
    
            You should reason step-by-step, then call the appropriate tool using the format:
            Action: tool_name
            Action Input: JSON
    
            Once you get a tool result, continue reasoning.
    
            End your answer with:
            Final Answer: [your answer here]
            """),
            (
                "user",
                f"""## ISSUE TO FIX
        {issue_data.model_dump_json(indent=2)}
    
        ## GITHUB CREDENTIALS
        {self.github_credentials.model_dump_json(indent=2)}
    
        """
            )
        ]

        inputs = {"messages": initial_messages}
        config = {"configurable": {"thread_id": f"thread-issue-{issue_data.number}"}}

        # Stream results when executed normally
        for event in graph.stream(inputs, config=config):
            print(event)
            yield event


        # # Return results directly when called from the API
        # else:
        #     result = graph.invoke(inputs, config=config)
        #     return {"issue_number": issue_data.number, "status": "processed"}