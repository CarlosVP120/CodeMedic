import os
from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from tools.tools import *
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint, HuggingFacePipeline
from typing import Optional
from models.models import GitHubIssue


def main(issue_data: Optional[GitHubIssue] = None):
    # Cargar variables de entorno
    if "GITHUB_TOKEN" in os.environ:
        del os.environ["GITHUB_TOKEN"]

    # Cargar variables de entorno desde .env
    load_dotenv(override=True)

    # Configuración de GitHub
    GITHUB_REPOSITORY = "Elcasvi/Code-Fixer-LLM-Agent"
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        raise ValueError("GITHUB_TOKEN no está definido en las variables de entorno")

    # Inicializar cliente de GitHub
    try:
        print("\n🔍 Verificando conexión con GitHub...")
        github_client = Github(github_token)

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
    # from langchain_openai import AzureChatOpenAI
    # load_dotenv(dotenv_path=".env")
    # load_dotenv()
    # api_key = os.getenv("AZURE_OPENAI_API_KEY")
    # endpoint = os.getenv("AZURE_OPENAI_ENDPOINT_GPT4")
    # model = AzureChatOpenAI(
    #     azure_endpoint=endpoint,
    #     azure_deployment="gpt-4o",
    #     api_version="2025-01-01-preview",
    #     temperature=0,
    #     max_tokens=1000,
    #     timeout=None,
    #     max_retries=2,
    #     api_key=api_key
    # )

    llm = HuggingFaceEndpoint(
        model="Qwen/Qwen3-4B",
        task="text-generation",
        max_new_tokens=512,
        do_sample=False,
        repetition_penalty=1.03
    )
    model = ChatHuggingFace(llm=llm)

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

    # Use the provided issue or fetch one if not provided
    if issue_data:
        issue = issue_data
        print(f"Using provided issue: #{issue.number}: {issue.title}")
    else:
        # Fallback to fetching an issue
        issue = get_github_issue(
            get_github_issues(
                GithubRepositoryData(github_token=github_token, repository=GITHUB_REPOSITORY)
            ),
            issue_number=2
        )
        print(f"Using fetched issue: #{issue.number}: {issue.title}")

    github_repository_data:GithubRepositoryData=GithubRepositoryData(github_token=github_token, repository=GITHUB_REPOSITORY)

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
    {issue.model_dump_json(indent=2)}

    ## GITHUB CREDENTIALS
    {github_repository_data.model_dump_json(indent=2)}

    """
        )
    ]

    inputs = {"messages": initial_messages}
    config = {"configurable": {"thread_id": f"thread-issue-{issue.number}"}}

    # Stream results when executed normally
    if issue_data is None:
        for event in graph.stream(inputs, config=config):
            print(event)
        return {"status": "streamed"}
    # Return results directly when called from the API
    else:
        result = graph.invoke(inputs, config=config)
        return {"issue_number": issue.number, "status": "processed"}

if __name__ == "__main__":
    main()






































#
# # Definir la estructura del estado
# class State(TypedDict):
#     issue: GitHubIssue
#     analysis: Optional[IssueAnalysis]
#     pr_data: Optional[PullRequestData]
#     files_analysis: Optional[dict]
#     user_approval: Optional[bool]
#     proposed_changes: Optional[Dict[str, str]]
#
# def analyze_files(state: State):
#     """Analiza los archivos relacionados con el issue."""
#     print("\n🔍 Analizando archivos relacionados...")
#
#     # Obtener la estructura de archivos
#     files = list_repo_files.invoke("")
#
#     # Crear prompt para sugerir archivos relacionados
#     prompt = f"""
#     Analiza el siguiente issue y la lista de archivos del repositorio para identificar los archivos potencialmente relacionados con el problema.
#
#     Issue:
#     Título: {state['issue'].title}
#     Descripción: {state['issue'].body}
#
#     Lista de archivos disponibles:
#     {files}
#
#     IMPORTANTE: Debes responder EXACTAMENTE en el siguiente formato JSON, sin texto adicional:
#     {{
#         "archivos_relacionados": [
#             {{
#                 "ruta": "ruta/al/archivo",
#                 "razon": "Breve explicación de por qué este archivo está relacionado",
#                 "probabilidad": "alta/media/baja"
#             }}
#         ],
#         "archivos_a_revisar": [
#             {{
#                 "ruta": "ruta/al/archivo",
#                 "razon": "Breve explicación de por qué deberíamos revisar este archivo"
#             }}
#         ],
#         "archivos_a_ignorar": [
#             {{
#                 "ruta": "ruta/al/archivo",
#                 "razon": "Breve explicación de por qué podemos ignorar este archivo"
#             }}
#         ]
#     }}
#     """
#
#     messages = [HumanMessage(content=prompt)]
#     response = model.invoke(messages)
#
#     try:
#         content = response.content.strip()
#         json_start = content.find('{')
#         json_end = content.rfind('}') + 1
#         if json_start >= 0 and json_end > json_start:
#             content = content[json_start:json_end]
#
#         state['files_analysis'] = json.loads(content)
#         return state
#     except json.JSONDecodeError as e:
#         print(f"\n⚠️ Error al procesar la respuesta del LLM: {str(e)}")
#         state['files_analysis'] = {"archivos_relacionados": [], "archivos_a_revisar": [], "archivos_a_ignorar": []}
#         return state
#
# def prepare_pull_request(state: State):
#     """Prepara los datos para el pull request basado en el análisis."""
#     print("\n📝 Preparando pull request...")
#
#     if not state.get('analysis') or not state.get('files_analysis'):
#         print("❌ No hay análisis suficiente para crear un pull request")
#         return state
#
#     # Crear prompt para generar el pull request
#     prompt = f"""
#     Basado en el siguiente análisis, genera los datos para un pull request:
#
#     Análisis del Issue:
#     {state['analysis'].model_dump_json(indent=2)}
#
#     Archivos Relacionados:
#     {json.dumps(state['files_analysis'], indent=2)}
#
#     Genera un JSON con la siguiente estructura:
#     {{
#         "title": "Título del PR",
#         "body": "Descripción detallada del PR",
#         "head_branch": "rama-de-origen",
#         "base_branch": "main",
#         "issue_number": {state['issue'].number}
#     }}
#     """
#
#     messages = [HumanMessage(content=prompt)]
#     response = model.invoke(messages)
#
#     try:
#         content = response.content.strip()
#         json_start = content.find('{')
#         json_end = content.rfind('}') + 1
#         if json_start >= 0 and json_end > json_start:
#             content = content[json_start:json_end]
#
#         state['pr_data'] = PullRequestData(**json.loads(content))
#         return state
#     except Exception as e:
#         print(f"\n⚠️ Error al preparar el pull request: {str(e)}")
#         return state
#
# def human_review(state: State):
#     """Permite al usuario revisar y aprobar el pull request."""
#     if not state.get('pr_data'):
#         print("❌ No hay datos de pull request para revisar")
#         return state
#
#     print("\n👥 Revisión Humana del Pull Request")
#     print("==================================")
#     print(f"Título: {state['pr_data'].title}")
#     print(f"Descripción: {state['pr_data'].body}")
#     print(f"Rama de origen: {state['pr_data'].head_branch}")
#     print(f"Rama destino: {state['pr_data'].base_branch}")
#     print(f"Issue relacionado: #{state['pr_data'].issue_number}")
#
#     while True:
#         user_input = input("\n¿Deseas aprobar este pull request? (yes/no/modify): ").lower()
#         if user_input in ['yes', 'no', 'modify']:
#             if user_input == 'yes':
#                 state['user_approval'] = True
#             elif user_input == 'no':
#                 state['user_approval'] = False
#             else:  # modify
#                 print("\nModificando pull request...")
#                 state['pr_data'].title = input("Nuevo título: ") or state['pr_data'].title
#                 state['pr_data'].body = input("Nueva descripción: ") or state['pr_data'].body
#                 state['user_approval'] = True
#             break
#         print("Por favor, responde con 'yes', 'no' o 'modify'")
#
#     return state
#
# def prepare_code_changes(state: State):
#     """Prepara los cambios de código basados en el análisis."""
#     print("\n💻 Preparando cambios de código...")
#
#     if not state.get('analysis') or not state.get('files_analysis'):
#         print("❌ No hay análisis suficiente para proponer cambios")
#         return state
#
#     try:
#         # Obtener el archivo que necesita cambios
#         file_path = state['files_analysis']['archivos_relacionados'][0]['ruta']
#
#         # Obtener el contenido actual del archivo
#         current_content = get_file_content.invoke(file_path)
#
#         # Crear prompt para el LLM
#         prompt = f"""
#         Aquí está el contenido actual del archivo {file_path}:
#         ```
#         {current_content}
#         ```
#
#         Basado en el análisis del issue, genera el código corregido.
#         Responde SOLO con el código corregido, sin explicaciones ni pensamientos adicionales.
#         """
#
#         # Obtener el nuevo contenido del LLM
#         messages = [HumanMessage(content=prompt)]
#         response = model.invoke(messages)
#         corrected_content = response.content.strip()
#
#         # Eliminar los marcadores de código si existen
#         if corrected_content.startswith("```"):
#             corrected_content = corrected_content.split("\n", 1)[1]
#         if corrected_content.endswith("```"):
#             corrected_content = corrected_content.rsplit("\n", 1)[0]
#
#         # Filtrar el contenido para asegurarse de que solo se incluya el código
#         corrected_content = "\n".join([line for line in corrected_content.split("\n") if not line.strip().startswith("<think>") and not line.strip().endswith("</think>") and not line.strip().startswith("```")])
#
#         # Guardar los cambios propuestos
#         state['proposed_changes'] = {
#             file_path: corrected_content
#         }
#
#         # Crear el archivo local con la corrección
#         local_file_path = f"fixed_{file_path}"
#         create_local_file.invoke({"file_path": local_file_path, "content": corrected_content})
#         print(f"✅ Archivo local creado en: {local_file_path}")
#
#         return state
#     except Exception as e:
#         print(f"\n⚠️ Error al preparar los cambios: {str(e)}")
#         return state
#
# def review_code_changes(state: State):
#     if not state.get('proposed_changes'):
#         print("❌ No hay cambios propuestos para revisar")
#         return state
#
#     print("\n👥 Revisión de Cambios de Código")
#     print("==============================")
#
#     to_remove = []
#     for file_path, new_content in list(state['proposed_changes'].items()):
#         print(f"\n📄 Archivo: {file_path}")
#         print("Cambios propuestos:")
#         print("------------------")
#         print(new_content)
#
#         while True:
#             user_input = input("\n¿Aceptas estos cambios? (yes/no/modify): ").lower()
#             if user_input in ['yes', 'no', 'modify']:
#                 if user_input == 'yes':
#                     break
#                 elif user_input == 'no':
#                     to_remove.append(file_path)
#                     break
#                 else:  # modify
#                     print("\nModificando cambios...")
#                     new_content = input("Ingresa el nuevo contenido del archivo:\n")
#                     state['proposed_changes'][file_path] = new_content
#                     break
#             print("Por favor, responde con 'yes', 'no' o 'modify'")
#
#     for file_path in to_remove:
#         state['proposed_changes'].pop(file_path)
#
#     return state
#
# def analyze_issue(state: State):
#     """Analiza el issue y genera un análisis estructurado."""
#     print("\n🔍 Analizando issue...")
#
#     # Crear prompt para el análisis
#     prompt = f"""
#     Analiza el siguiente issue de GitHub y proporciona una respuesta estructurada:
#
#     Issue #{state['issue'].number}: {state['issue'].title}
#     Descripción: {state['issue'].body}
#
#     Por favor, proporciona tu análisis en el siguiente formato JSON:
#     {{
#         "issue_number": {state['issue'].number},
#         "summary": "Resumen conciso del problema",
#         "impact": "Impacto potencial del problema",
#         "affected_areas": ["Lista de áreas afectadas"],
#         "recommendations": ["Lista de recomendaciones"],
#         "technical_details": {{
#             "created_at": "{state['issue'].created_at.isoformat()}",
#             "updated_at": "{state['issue'].updated_at.isoformat()}",
#             "state": "{state['issue'].state}"
#         }},
#         "solution": "Solución propuesta para el problema"
#     }}
#     """
#
#     messages = [HumanMessage(content=prompt)]
#     response = model.invoke(messages)
#
#     try:
#         content = response.content.strip()
#         json_start = content.find('{')
#         json_end = content.rfind('}') + 1
#         if json_start >= 0 and json_end > json_start:
#             content = content[json_start:json_end]
#
#         state['analysis'] = IssueAnalysis(**json.loads(content))
#         print("\n✅ Análisis del issue completado")
#         return state
#     except Exception as e:
#         print(f"\n⚠️ Error al analizar el issue: {str(e)}")
#         return state
#
# def create_pull_request(state: State):
#     """Crea el pull request si fue aprobado por el usuario."""
#     if not state.get('user_approval'):
#         print("\n❌ Pull request no aprobado por el usuario")
#         return state
#
#     if not state.get('pr_data'):
#         print("\n❌ No hay datos de pull request para crear")
#         return state
#
#     print("\n🚀 Creando pull request...")
#     try:
#         # Obtener el repositorio
#         repo = github_client.get_repo(GITHUB_REPOSITORY)
#
#         # Crear el pull request
#         pull_request = repo.create_pull(
#             title=state['pr_data'].title,
#             body=state['pr_data'].body,
#             head="main",
#             base=state['pr_data'].base_branch
#         )
#
#         print(f"✅ Pull request creado: {pull_request.html_url}")
#     except Exception as e:
#         print(f"❌ Error al crear el pull request: {str(e)}")
#
#     return state
#
# def should_continue(state):
#     """Determina si continuar con el flujo basado en el estado."""
#     if not state.get('user_approval'):
#         return "end"
#     return "create_pr"
#
# @tool
# def modify_file(file_path: str, changes: str) -> str:
#     """
#     Modifica el contenido de un archivo en el repositorio.
#     Args:
#         file_path: Ruta del archivo a modificar
#         changes: Descripción de los cambios a realizar en formato JSON
#     Returns:
#         str: Resultado de la operación
#     """
#     try:
#         # Obtener el contenido actual del archivo
#         current_content = get_file_content.invoke(file_path)
#
#         # Crear prompt para el LLM
#         prompt = f"""
#         Aquí está el contenido actual del archivo {file_path}:
#         ```
#         {current_content}
#         ```
#
#         Y estos son los cambios que necesitas hacer:
#         {changes}
#
#         Por favor, proporciona el nuevo contenido completo del archivo con los cambios aplicados.
#         Responde SOLO con el contenido del archivo, sin explicaciones adicionales.
#         """
#
#         # Obtener el nuevo contenido del LLM
#         messages = [HumanMessage(content=prompt)]
#         response = model.invoke(messages)
#         new_content = response.content.strip()
#
#         # Eliminar los marcadores de código si existen
#         if new_content.startswith("```"):
#             new_content = new_content.split("\n", 1)[1]
#         if new_content.endswith("```"):
#             new_content = new_content.rsplit("\n", 1)[0]
#
#         return new_content
#     except Exception as e:
#         return f"Error al modificar el archivo: {str(e)}"
#
# def main():
#     # Obtener issues de GitHub
#     issues = get_github_issues()
#
#     if not issues:
#         print("No se encontraron issues abiertos en el repositorio.")
#         return
#
#     print("\n📋 Issues disponibles:")
#     for issue in issues:
#         print(f"\nIssue #{issue.number}: {issue.title}")
#         print(f"Descripción: {issue.body[:100]}...")
#
#     # Seleccionar el primer issue para análisis
#     first_issue = issues[0]
#     print(f"\n🔍 Analizando issue #{first_issue.number}...")
#
#     # Configurar el grafo
#     builder = StateGraph(State)
#
#     # Agregar nodos
#     builder.add_node("analyze_issue", analyze_issue)
#     builder.add_node("analyze_files", analyze_files)
#     builder.add_node("prepare_code_changes", prepare_code_changes)
#     builder.add_node("review_code_changes", review_code_changes)
#     builder.add_node("prepare_pr", prepare_pull_request)
#     builder.add_node("human_review", human_review)
#     builder.add_node("create_pr", create_pull_request)
#
#     # Definir flujo
#     builder.add_edge(START, "analyze_issue")
#     builder.add_edge("analyze_issue", "analyze_files")
#     builder.add_edge("analyze_files", "prepare_code_changes")
#     builder.add_edge("prepare_code_changes", "review_code_changes")
#     builder.add_edge("review_code_changes", "prepare_pr")
#     builder.add_edge("prepare_pr", "human_review")
#     builder.add_conditional_edges(
#         "human_review",
#         should_continue,
#         {
#             "create_pr": "create_pr",
#             "end": END
#         }
#     )
#     builder.add_edge("create_pr", END)
#
#     # Configurar memoria y compilar
#     memory = MemorySaver()
#     graph = builder.compile(checkpointer=memory)
#
#     # Ejecutar el grafo
#     initial_state = {
#         "issue": first_issue,
#         "analysis": None,
#         "pr_data": None,
#         "files_analysis": None,
#         "user_approval": None,
#         "proposed_changes": None
#     }
#
#     thread = {"configurable": {"thread_id": f"issue_{first_issue.number}"}}
#
#     for event in graph.stream(initial_state, thread, stream_mode="values"):
#         print(event)

# if __name__ == "__main__":
#     main()