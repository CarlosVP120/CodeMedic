import os
from langchain_community.chat_models import ChatOllama
from typing import Dict, Any, List, Optional
from github import Github
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langchain_core.tools import Tool
from models.GithubRepositoryDataModel import GithubRepositoryData
from langchain_core.messages import BaseMessage
import json
from tools.tools import get_repository_file_names, create_local_file, get_repository_file_content, get_github_issue,get_github_issues
import asyncio


class PullRequestData(BaseModel):
    title: str = Field(..., description="Título del pull request")
    body: str = Field(..., description="Descripción del pull request")
    head_branch: str = Field(..., description="Rama de origen")
    base_branch: str = Field(..., description="Rama destino")
    issue_number: int = Field(..., description="Número del issue relacionado")




def main():
    # Cargar variables de entorno
    if "GITHUB_TOKEN" in os.environ:
        print("\n⚠️  Limpiando GITHUB_TOKEN existente en variables de entorno...")
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
        print("Token: ", github_token)

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



    # Configuración del agente
    # Define a simple state type
    tools = [
        Tool.from_function(
            func=get_repository_file_names,
            name="get_repository_file_names",
            description="Get a list of file names from the root of a GitHub repository."
        ),
        Tool.from_function(
            func=get_repository_file_content,
            name="get_repository_file_content",
            description="Get the content of a specific file in the GitHub repository."
        ),
        Tool.from_function(
            func=create_local_file,
            name="create_local_file",
            description="Create or overwrite a local file with the given content."
        )
    ]
    tool_map = {tool.name: tool for tool in tools}

    # ---- State Definition ----
    class AgentState(BaseModel):
        messages: List[BaseMessage]
        tool_result: Optional[str] = None

    # ---- LLM Setup ----
    model = ChatOllama(model="qwen3:8b")

    # ---- LLM Node ----
    async def call_llm(state: AgentState) -> Dict[str, Any]:
        messages = state.messages
        if state.tool_result:
            messages.append(AIMessage(content=state.tool_result))
        response = await model.ainvoke(messages)
        return {"messages": [response], "tool_result": None}

    # ---- Tool Execution Node ----
    async def run_tool(state: AgentState) -> Dict[str, Any]:
        ai_message = state.messages[-1]
        content = ai_message.content

        try:
            tool_name = next((name for name in tool_map if name in content), None)
            if not tool_name:
                return {"tool_result": "Tool not found.", "messages": []}

            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            args = json.loads(content[json_start:json_end])
            result = tool_map[tool_name].invoke(args)

            return {"tool_result": str(result), "messages": []}
        except Exception as e:
            return {"tool_result": f"Tool execution error: {str(e)}", "messages": []}

    # ---- Router ----
    def tool_router(state: AgentState) -> str:
        ai_message = state.messages[-1].content.lower()
        for name in tool_map:
            if name in ai_message:
                return "run_tool"
        if "end" in ai_message or "finished" in ai_message:
            return END
        return "run_tool"

    # ---- Graph Construction ----
    workflow = StateGraph(AgentState)
    workflow.add_node("call_llm", call_llm)
    workflow.add_node("run_tool", run_tool)

    workflow.set_entry_point("call_llm")
    workflow.add_conditional_edges("call_llm", tool_router, {
        "run_tool": "run_tool",
        END: END
    })
    workflow.add_edge("run_tool", "call_llm")

    graph = workflow.compile()

    #input_message = {"messages": [HumanMessage(content=f"Fix the following issue: {get_github_issue(get_github_issues(github_repository_data=GithubRepositoryData(client=github_client,repository=GITHUB_REPOSITORY)),2).__str__()}")]}

    async def simulate_interaction():
        issue = get_github_issue(
            get_github_issues(
                github_repository_data=GithubRepositoryData(client=github_client, repository=GITHUB_REPOSITORY)
            ),
            2
        )
        input_message = {
            "messages": [HumanMessage(content=f"Fix the following issue: {issue.__str__()}")]
        }

        async for output, metadata in graph.astream(input_message, stream_mode=["messages", "updates"]):
            if isinstance(metadata, dict) and 'call_llm' in metadata:
                ai_message = metadata['call_llm']['messages'][0]
                if ai_message.content:
                    print(ai_message.content, end="|", flush=True)

    # Run the simulation
    asyncio.run(simulate_interaction())

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