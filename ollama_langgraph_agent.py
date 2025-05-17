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
from typing import List, Optional, Dict, Any
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
    
    # Crear input inicial con el issue seleccionado
    initial_input = {
        "messages": [
            HumanMessage(content=f"Por favor analiza este issue: {first_issue.model_dump()}")
        ]
    }
    thread = {"configurable": {"thread_id": f"issue_{first_issue.number}"}}
    
    print("\n--- INICIO DEL AGENTE LANGGRAPH CON OLLAMA ---")
    for event in app.stream(initial_input, thread, stream_mode="values"):
        if isinstance(event, dict) and "messages" in event:
            for message in event["messages"]:
                if isinstance(message, AIMessage):
                    try:
                        # Intentar parsear la respuesta como JSON
                        analysis = json.loads(message.content)
                        print("\n📊 Análisis del Issue:")
                        print("-------------------")
                        print(f"📝 Resumen: {analysis.get('summary', 'No disponible')}")
                        print(f"💥 Impacto: {analysis.get('impact', 'No disponible')}")
                        print("\n🎯 Áreas Afectadas:")
                        for area in analysis.get('affected_areas', []):
                            print(f"  - {area}")
                        print("\n💡 Recomendaciones:")
                        for rec in analysis.get('recommendations', []):
                            print(f"  - {rec}")
                        if 'solution' in analysis:
                            print(f"\n✨ Solución Propuesta:\n{analysis['solution']}")
                        if 'technical_details' in analysis:
                            print("\n🔧 Detalles Técnicos:")
                            for key, value in analysis['technical_details'].items():
                                print(f"  - {key}: {value}")
                    except json.JSONDecodeError:
                        # Si no es JSON, mostrar el mensaje tal cual
                        print("\n📝 Respuesta del Agente:")
                        print(message.content)
    print("\n--- FIN DEL AGENTE ---")

if __name__ == "__main__":
    main() 