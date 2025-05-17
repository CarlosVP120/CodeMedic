import os
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
from langchain_community.chat_models import ChatOllama
from langgraph.graph import MessagesState, START, END, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from github import Github
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, TypedDict
from datetime import datetime
import json

# Modelos Pydantic
class GitHubIssue(BaseModel):
    number: int
    title: str
    body: str
    state: str
    created_at: datetime
    updated_at: datetime

class IssueAnalysis(BaseModel):
    issue_number: int = Field(..., description="Número del issue analizado")
    summary: str = Field(..., description="Resumen del problema")
    impact: str = Field(..., description="Impacto potencial del problema")
    affected_areas: List[str] = Field(..., description="Áreas del código afectadas")
    recommendations: List[str] = Field(..., description="Recomendaciones para resolver el problema")
    technical_details: Optional[Dict[str, Any]] = Field(None, description="Detalles técnicos adicionales")
    solution: Optional[str] = Field(None, description="Solución propuesta para el problema")

class PullRequestData(BaseModel):
    title: str = Field(..., description="Título del pull request")
    body: str = Field(..., description="Descripción del pull request")
    head_branch: str = Field(..., description="Rama de origen")
    base_branch: str = Field(..., description="Rama destino")
    issue_number: int = Field(..., description="Número del issue relacionado")

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

def get_github_issues() -> List[GitHubIssue]:
    """Obtiene los issues abiertos del repositorio."""
    try:
        print(f"\n🔍 Intentando acceder al repositorio: {GITHUB_REPOSITORY}")
        repo = github_client.get_repo(GITHUB_REPOSITORY)
        print("✓ Repositorio encontrado")
        
        print("\n📋 Obteniendo issues abiertos...")
        issues = repo.get_issues(state='open')
        issues_list = []
        
        for issue in issues:
            print(f"  - Issue #{issue.number}: {issue.title}")
            issues_list.append(GitHubIssue(
                number=issue.number,
                title=issue.title,
                body=issue.body or "",
                state=issue.state,
                created_at=issue.created_at,
                updated_at=issue.updated_at
            ))
        
        if not issues_list:
            print("⚠️ No se encontraron issues abiertos")
        else:
            print(f"✓ Se encontraron {len(issues_list)} issues abiertos")
        
        return issues_list
    except Exception as e:
        print(f"\n❌ Error al obtener issues: {str(e)}")
        print(f"Repositorio: {GITHUB_REPOSITORY}")
        print(f"Token válido: {'Sí' if github_token else 'No'}")
        print("\nDetalles del error:")
        print(f"- Tipo de error: {type(e).__name__}")
        print(f"- Mensaje: {str(e)}")
        return []

def parse_llm_response(response: str) -> IssueAnalysis:
    """Parsea la respuesta del LLM y la convierte en un IssueAnalysis."""
    try:
        # Intentar parsear la respuesta como JSON
        data = json.loads(response)
        return IssueAnalysis(**data)
    except json.JSONDecodeError:
        # Si no es JSON, intentar extraer la información de manera estructurada
        lines = response.split('\n')
        analysis = {
            "issue_number": 0,  # Se actualizará después
            "summary": "",
            "impact": "",
            "affected_areas": [],
            "recommendations": [],
            "technical_details": {},
            "solution": ""
        }
        
        current_section = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith("Resumen:"):
                current_section = "summary"
                analysis["summary"] = line.replace("Resumen:", "").strip()
            elif line.startswith("Impacto:"):
                current_section = "impact"
                analysis["impact"] = line.replace("Impacto:", "").strip()
            elif line.startswith("Áreas afectadas:"):
                current_section = "affected_areas"
                areas = line.replace("Áreas afectadas:", "").strip()
                analysis["affected_areas"] = [area.strip() for area in areas.split(",")]
            elif line.startswith("Recomendaciones:"):
                current_section = "recommendations"
                recs = line.replace("Recomendaciones:", "").strip()
                analysis["recommendations"] = [rec.strip() for rec in recs.split(",")]
            elif line.startswith("Solución:"):
                current_section = "solution"
                analysis["solution"] = line.replace("Solución:", "").strip()
            elif current_section and line.startswith("- "):
                if current_section == "recommendations":
                    analysis["recommendations"].append(line[2:].strip())
                elif current_section == "affected_areas":
                    analysis["affected_areas"].append(line[2:].strip())
        
        return IssueAnalysis(**analysis)

@tool
def analyze_issue(issue_data: dict) -> str:
    """
    Analiza un issue de GitHub y proporciona un análisis detallado.
    Espera un diccionario con las claves: number, title, body.
    """
    try:
        # Convertir el diccionario a un modelo GitHubIssue
        issue = GitHubIssue(**issue_data)
        
        # Crear prompt para el análisis
        analysis_prompt = f"""
        Analiza el siguiente issue de GitHub y proporciona una respuesta estructurada:
        
        Issue #{issue.number}: {issue.title}
        Descripción: {issue.body}
        
        Por favor, proporciona tu análisis en el siguiente formato JSON:
        {{
            "issue_number": {issue.number},
            "summary": "Resumen conciso del problema",
            "impact": "Impacto potencial del problema",
            "affected_areas": ["Lista de áreas afectadas"],
            "recommendations": ["Lista de recomendaciones"],
            "technical_details": {{
                "created_at": "{issue.created_at.isoformat()}",
                "updated_at": "{issue.updated_at.isoformat()}",
                "state": "{issue.state}"
            }},
            "solution": "Solución propuesta para el problema"
        }}
        """
        
        # Obtener respuesta del LLM
        messages = [HumanMessage(content=analysis_prompt)]
        response = model.invoke(messages)
        
        # Parsear la respuesta y convertirla a IssueAnalysis
        analysis = parse_llm_response(response.content)
        
        # Actualizar el número de issue
        analysis.issue_number = issue.number
        
        return analysis.model_dump_json(indent=2)
    except Exception as e:
        return f"Error al analizar el issue: {str(e)}"

@tool
def create_pull_request(pr_data: dict) -> str:
    """
    Crea un pull request en GitHub.
    Espera un diccionario con las claves: title, body, head_branch, base_branch, issue_number.
    """
    try:
        # Convertir el diccionario a un modelo PullRequestData
        pr = PullRequestData(**pr_data)
        
        # Obtener el repositorio
        repo = github_client.get_repo(GITHUB_REPOSITORY)
        
        # Crear el pull request
        pull_request = repo.create_pull(
            title=pr.title,
            body=pr.body,
            head=f"{pr.head_branch}/issue-{pr.issue_number}",
            base=pr.base_branch
        )
        
        return f"Pull request creado exitosamente: {pull_request.html_url}"
    except Exception as e:
        return f"Error al crear el pull request: {str(e)}"

@tool
def list_repo_files(path: str = "") -> str:
    """
    Lista todos los archivos en el repositorio de GitHub de manera formateada.
    Args:
        path: Ruta opcional para listar archivos desde un directorio específico
    Returns:
        str: Lista formateada de archivos y directorios
    """
    try:
        repo = github_client.get_repo(GITHUB_REPOSITORY)
        output = []
        
        def _list_files_recursive(path, level=0):
            try:
                contents = repo.get_contents(path)
                for content in contents:
                    # Crear indentación basada en el nivel
                    indent = "  " * level
                    if content.type == "dir":
                        output.append(f"{indent}📁 {content.name}/")
                        _list_files_recursive(content.path, level + 1)
                    else:
                        # Obtener la extensión del archivo
                        ext = os.path.splitext(content.name)[1]
                        # Seleccionar emoji basado en la extensión
                        emoji = {
                            '.py': '🐍',
                            '.js': '📜',
                            '.html': '🌐',
                            '.css': '🎨',
                            '.json': '📋',
                            '.md': '📝',
                            '.txt': '📄',
                            '.gitignore': '🚫',
                            '.env': '🔑',
                            '': '📄'
                        }.get(ext, '📄')
                        output.append(f"{indent}{emoji} {content.name}")
            except Exception as e:
                output.append(f"{indent}❌ Error al acceder a {path}: {str(e)}")
        
        print("\n📂 Listando archivos del repositorio...")
        _list_files_recursive(path)
        
        if not output:
            return "No se encontraron archivos en el repositorio."
        
        return "\n".join(output)
    except Exception as e:
        return f"Error al listar archivos: {str(e)}"

# Tool para extraer el contenido de un archivo
@tool
def get_file_content(file_path: str) -> str:
    """
    Extrae el contenido de un archivo del repositorio de GitHub.
    """
    try:
        repo = github_client.get_repo(GITHUB_REPOSITORY)
        content = repo.get_contents(file_path)
        return content.decoded_content.decode()
    except Exception as e:
        return f"Error al obtener el contenido del archivo: {str(e)}"

# Configuración del agente
tools = [analyze_issue, create_pull_request, list_repo_files, get_file_content]
tool_node = ToolNode(tools)
model = ChatOllama(model="qwen3:8b")

def agent_reasoning(state):
    messages = state["messages"]
    response = model.invoke(messages)
    return {"messages": messages + [response]}

def should_continue(state):
    messages = state["messages"]
    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "continue"
    return "end"

# Construir el grafo
workflow = StateGraph(MessagesState)
workflow.add_node("agent_reasoning", agent_reasoning)
workflow.add_node("call_tool", tool_node)
workflow.add_edge(START, "agent_reasoning")
workflow.add_conditional_edges(
    "agent_reasoning", should_continue, {
        "continue": "call_tool",
        "end": END
    }
)
workflow.add_edge("call_tool", "agent_reasoning")

memory = MemorySaver()
app = workflow.compile(checkpointer=memory, interrupt_before=["call_tool"])

# Definir la estructura del estado
class State(TypedDict):
    issue: GitHubIssue
    analysis: Optional[IssueAnalysis]
    pr_data: Optional[PullRequestData]
    files_analysis: Optional[dict]
    user_approval: Optional[bool]
    proposed_changes: Optional[Dict[str, str]]

def analyze_files(state: State):
    """Analiza los archivos relacionados con el issue."""
    print("\n🔍 Analizando archivos relacionados...")
    
    # Obtener la estructura de archivos
    files = list_repo_files.invoke("")
    
    # Crear prompt para sugerir archivos relacionados
    prompt = f"""
    Analiza el siguiente issue y la lista de archivos del repositorio para identificar los archivos potencialmente relacionados con el problema.

    Issue:
    Título: {state['issue'].title}
    Descripción: {state['issue'].body}

    Lista de archivos disponibles:
    {files}

    IMPORTANTE: Debes responder EXACTAMENTE en el siguiente formato JSON, sin texto adicional:
    {{
        "archivos_relacionados": [
            {{
                "ruta": "ruta/al/archivo",
                "razon": "Breve explicación de por qué este archivo está relacionado",
                "probabilidad": "alta/media/baja"
            }}
        ],
        "archivos_a_revisar": [
            {{
                "ruta": "ruta/al/archivo",
                "razon": "Breve explicación de por qué deberíamos revisar este archivo"
            }}
        ],
        "archivos_a_ignorar": [
            {{
                "ruta": "ruta/al/archivo",
                "razon": "Breve explicación de por qué podemos ignorar este archivo"
            }}
        ]
    }}
    """
    
    messages = [HumanMessage(content=prompt)]
    response = model.invoke(messages)
    
    try:
        content = response.content.strip()
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            content = content[json_start:json_end]
        
        state['files_analysis'] = json.loads(content)
        return state
    except json.JSONDecodeError as e:
        print(f"\n⚠️ Error al procesar la respuesta del LLM: {str(e)}")
        state['files_analysis'] = {"archivos_relacionados": [], "archivos_a_revisar": [], "archivos_a_ignorar": []}
        return state

def prepare_pull_request(state: State):
    """Prepara los datos para el pull request basado en el análisis."""
    print("\n📝 Preparando pull request...")
    
    if not state.get('analysis') or not state.get('files_analysis'):
        print("❌ No hay análisis suficiente para crear un pull request")
        return state
    
    # Crear prompt para generar el pull request
    prompt = f"""
    Basado en el siguiente análisis, genera los datos para un pull request:
    
    Análisis del Issue:
    {state['analysis'].model_dump_json(indent=2)}
    
    Archivos Relacionados:
    {json.dumps(state['files_analysis'], indent=2)}
    
    Genera un JSON con la siguiente estructura:
    {{
        "title": "Título del PR",
        "body": "Descripción detallada del PR",
        "head_branch": "rama-de-origen",
        "base_branch": "main",
        "issue_number": {state['issue'].number}
    }}
    """
    
    messages = [HumanMessage(content=prompt)]
    response = model.invoke(messages)
    
    try:
        content = response.content.strip()
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            content = content[json_start:json_end]
        
        state['pr_data'] = PullRequestData(**json.loads(content))
        return state
    except Exception as e:
        print(f"\n⚠️ Error al preparar el pull request: {str(e)}")
        return state

def human_review(state: State):
    """Permite al usuario revisar y aprobar el pull request."""
    if not state.get('pr_data'):
        print("❌ No hay datos de pull request para revisar")
        return state
    
    print("\n👥 Revisión Humana del Pull Request")
    print("==================================")
    print(f"Título: {state['pr_data'].title}")
    print(f"Descripción: {state['pr_data'].body}")
    print(f"Rama de origen: {state['pr_data'].head_branch}")
    print(f"Rama destino: {state['pr_data'].base_branch}")
    print(f"Issue relacionado: #{state['pr_data'].issue_number}")
    
    while True:
        user_input = input("\n¿Deseas aprobar este pull request? (yes/no/modify): ").lower()
        if user_input in ['yes', 'no', 'modify']:
            if user_input == 'yes':
                state['user_approval'] = True
            elif user_input == 'no':
                state['user_approval'] = False
            else:  # modify
                print("\nModificando pull request...")
                state['pr_data'].title = input("Nuevo título: ") or state['pr_data'].title
                state['pr_data'].body = input("Nueva descripción: ") or state['pr_data'].body
                state['user_approval'] = True
            break
        print("Por favor, responde con 'yes', 'no' o 'modify'")
    
    return state

def create_pull_request(state: State):
    """Crea el pull request si fue aprobado por el usuario."""
    if not state.get('user_approval'):
        print("\n❌ Pull request no aprobado por el usuario")
        return state
    
    if not state.get('pr_data'):
        print("\n❌ No hay datos de pull request para crear")
        return state
    
    print("\n🚀 Creando pull request...")
    try:
        result = create_pull_request.invoke(state['pr_data'].model_dump())
        print(f"✅ {result}")
    except Exception as e:
        print(f"❌ Error al crear el pull request: {str(e)}")
    
    return state

def should_continue(state):
    """Determina si continuar con el flujo basado en el estado."""
    if not state.get('user_approval'):
        return "end"
    return "create_pr"

@tool
def modify_file(file_path: str, changes: str) -> str:
    """
    Modifica el contenido de un archivo en el repositorio.
    Args:
        file_path: Ruta del archivo a modificar
        changes: Descripción de los cambios a realizar en formato JSON
    Returns:
        str: Resultado de la operación
    """
    try:
        # Obtener el contenido actual del archivo
        current_content = get_file_content.invoke(file_path)
        
        # Crear prompt para el LLM
        prompt = f"""
        Aquí está el contenido actual del archivo {file_path}:
        ```
        {current_content}
        ```
        
        Y estos son los cambios que necesitas hacer:
        {changes}
        
        Por favor, proporciona el nuevo contenido completo del archivo con los cambios aplicados.
        Responde SOLO con el contenido del archivo, sin explicaciones adicionales.
        """
        
        # Obtener el nuevo contenido del LLM
        messages = [HumanMessage(content=prompt)]
        response = model.invoke(messages)
        new_content = response.content.strip()
        
        # Eliminar los marcadores de código si existen
        if new_content.startswith("```"):
            new_content = new_content.split("\n", 1)[1]
        if new_content.endswith("```"):
            new_content = new_content.rsplit("\n", 1)[0]
        
        return new_content
    except Exception as e:
        return f"Error al modificar el archivo: {str(e)}"

def prepare_code_changes(state: State):
    """Prepara los cambios de código basados en el análisis."""
    print("\n💻 Preparando cambios de código...")
    
    if not state.get('analysis') or not state.get('files_analysis'):
        print("❌ No hay análisis suficiente para proponer cambios")
        return state
    
    # Crear prompt para generar los cambios
    prompt = f"""
    Basado en el siguiente análisis, genera los cambios necesarios para resolver el issue:
    
    Análisis del Issue:
    {state['analysis'].model_dump_json(indent=2)}
    
    Archivos Relacionados:
    {json.dumps(state['files_analysis'], indent=2)}
    
    Para cada archivo que necesite cambios, proporciona un JSON con la siguiente estructura:
    {{
        "archivo": "ruta/al/archivo",
        "cambios": "Descripción detallada de los cambios necesarios",
        "razon": "Explicación de por qué se necesitan estos cambios"
    }}
    """
    
    messages = [HumanMessage(content=prompt)]
    response = model.invoke(messages)
    
    try:
        content = response.content.strip()
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            content = content[json_start:json_end]
        
        changes_data = json.loads(content)
        state['proposed_changes'] = {}
        
        # Aplicar cambios a cada archivo
        for change in changes_data:
            print(f"\n📝 Aplicando cambios a {change['archivo']}...")
            print(f"Razón: {change['razon']}")
            
            new_content = modify_file.invoke(change['archivo'], change['cambios'])
            state['proposed_changes'][change['archivo']] = new_content
            
            print("✅ Cambios aplicados correctamente")
        
        return state
    except Exception as e:
        print(f"\n⚠️ Error al preparar los cambios: {str(e)}")
        return state

def review_code_changes(state: State):
    """Permite al usuario revisar los cambios propuestos."""
    if not state.get('proposed_changes'):
        print("❌ No hay cambios propuestos para revisar")
        return state
    
    print("\n👥 Revisión de Cambios de Código")
    print("==============================")
    
    for file_path, new_content in state['proposed_changes'].items():
        print(f"\n📄 Archivo: {file_path}")
        print("Cambios propuestos:")
        print("------------------")
        print(new_content)
        
        while True:
            user_input = input("\n¿Aceptas estos cambios? (yes/no/modify): ").lower()
            if user_input in ['yes', 'no', 'modify']:
                if user_input == 'yes':
                    continue
                elif user_input == 'no':
                    state['proposed_changes'].pop(file_path)
                else:  # modify
                    print("\nModificando cambios...")
                    new_content = input("Ingresa el nuevo contenido del archivo:\n")
                    state['proposed_changes'][file_path] = new_content
                break
            print("Por favor, responde con 'yes', 'no' o 'modify'")
    
    return state

def analyze_issue(state: State):
    """Analiza el issue y genera un análisis estructurado."""
    print("\n🔍 Analizando issue...")
    
    # Crear prompt para el análisis
    prompt = f"""
    Analiza el siguiente issue de GitHub y proporciona una respuesta estructurada:
    
    Issue #{state['issue'].number}: {state['issue'].title}
    Descripción: {state['issue'].body}
    
    Por favor, proporciona tu análisis en el siguiente formato JSON:
    {{
        "issue_number": {state['issue'].number},
        "summary": "Resumen conciso del problema",
        "impact": "Impacto potencial del problema",
        "affected_areas": ["Lista de áreas afectadas"],
        "recommendations": ["Lista de recomendaciones"],
        "technical_details": {{
            "created_at": "{state['issue'].created_at.isoformat()}",
            "updated_at": "{state['issue'].updated_at.isoformat()}",
            "state": "{state['issue'].state}"
        }},
        "solution": "Solución propuesta para el problema"
    }}
    """
    
    messages = [HumanMessage(content=prompt)]
    response = model.invoke(messages)
    
    try:
        content = response.content.strip()
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            content = content[json_start:json_end]
        
        state['analysis'] = IssueAnalysis(**json.loads(content))
        print("\n✅ Análisis del issue completado")
        return state
    except Exception as e:
        print(f"\n⚠️ Error al analizar el issue: {str(e)}")
        return state

def main():
    # Obtener issues de GitHub
    issues = get_github_issues()
    
    if not issues:
        print("No se encontraron issues abiertos en el repositorio.")
        return
    
    print("\n📋 Issues disponibles:")
    for issue in issues:
        print(f"\nIssue #{issue.number}: {issue.title}")
        print(f"Descripción: {issue.body[:100]}...")
    
    # Seleccionar el primer issue para análisis
    first_issue = issues[0]
    print(f"\n🔍 Analizando issue #{first_issue.number}...")
    
    # Configurar el grafo
    builder = StateGraph(State)
    
    # Agregar nodos
    builder.add_node("analyze_issue", analyze_issue)
    builder.add_node("analyze_files", analyze_files)
    builder.add_node("prepare_code_changes", prepare_code_changes)
    builder.add_node("review_code_changes", review_code_changes)
    builder.add_node("prepare_pr", prepare_pull_request)
    builder.add_node("human_review", human_review)
    builder.add_node("create_pr", create_pull_request)
    
    # Definir flujo
    builder.add_edge(START, "analyze_issue")
    builder.add_edge("analyze_issue", "analyze_files")
    builder.add_edge("analyze_files", "prepare_code_changes")
    builder.add_edge("prepare_code_changes", "review_code_changes")
    builder.add_edge("review_code_changes", "prepare_pr")
    builder.add_edge("prepare_pr", "human_review")
    builder.add_conditional_edges(
        "human_review",
        should_continue,
        {
            "create_pr": "create_pr",
            "end": END
        }
    )
    builder.add_edge("create_pr", END)
    
    # Configurar memoria y compilar
    memory = MemorySaver()
    graph = builder.compile(checkpointer=memory)
    
    # Ejecutar el grafo
    initial_state = {
        "issue": first_issue,
        "analysis": None,
        "pr_data": None,
        "files_analysis": None,
        "user_approval": None,
        "proposed_changes": None
    }
    
    thread = {"configurable": {"thread_id": f"issue_{first_issue.number}"}}
    
    for event in graph.stream(initial_state, thread, stream_mode="values"):
        print(event)

if __name__ == "__main__":
    main() 