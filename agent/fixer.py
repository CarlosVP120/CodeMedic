
class CodeFixerAgent:
    def __init__(self):
        # Cargar tu modelo o credenciales
        pass

    def fix_code(self, code: str, code_type: str, log: dict) -> str:
        # Simulamos una "corrección" simple
        prompt = f"Code type: {code_type}\nLog: {log}\nCode:\n{code}"
        print("Prompt generado para el modelo:\n", prompt)

        # Simulación de llamada al modelo
        fixed_code = code.replace("bug", "fix")  # Solo para prueba

        return fixed_code
from typing import Dict, Any, List, TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.tools import tool
from langchain_community.llms import Ollama
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from github import Github
import json
import os
import getpass
from dotenv import load_dotenv

# Cargar variables de entorno
if "GITHUB_TOKEN" in os.environ:
    print("\n⚠️  Limpiando GITHUB_TOKEN existente en variables de entorno...")
    del os.environ["GITHUB_TOKEN"]

# Cargar variables de entorno desde .env
load_dotenv(override=True)  # override=True fuerza a que use los valores del .env

# Repositorio de GitHub (definido directamente, no por variable de entorno)
GITHUB_REPOSITORY = "Elcasvi/Code-Fixer-LLM-Agent"
print(f"\nUsando repositorio: {GITHUB_REPOSITORY}")

# Configuración de GitHub
def setup_github_auth():
    """Configura la autenticación de GitHub usando token."""
    # Obtener token de variable de entorno
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN no está definido en las variables de entorno")
    
    # Configuración adicional
    GITHUB_BASE_BRANCH = os.getenv("GITHUB_BASE_BRANCH", "main")
    GITHUB_WORKING_BRANCH = os.getenv("GITHUB_WORKING_BRANCH", "fix")
    
    return {
        "token": token,
        "base_branch": GITHUB_BASE_BRANCH,
        "working_branch": GITHUB_WORKING_BRANCH
    }

# Configuración de GitHub
github_config = setup_github_auth()

# Definición de tipos para el estado del agente
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], "Mensajes en la conversación"]
    issue_data: Annotated[Dict[str, Any], "Datos del issue de GitHub"]
    current_step: Annotated[str, "Paso actual del proceso"]
    analysis: Annotated[str, "Análisis del issue"]
    solution: Annotated[str, "Solución propuesta"]
    steps: Annotated[List[str], "Pasos tomados"]
    recommendations: Annotated[List[str], "Recomendaciones"]

class CodeFixerAgent:
    def __init__(self):
        # Inicializar cliente de GitHub con token
        try:
            print("\n🔍 Verificando conexión con GitHub...")
            self.github_client = Github(github_config["token"])
            
            # Verificar token y usuario
            try:
                user = self.github_client.get_user()
            except Exception as user_error:
                print(f"\n❌ Error al verificar el token: {str(user_error)}")
                print("El token podría estar expirado o ser inválido")
                raise
            
            print("\n✓ Conexión con GitHub establecida correctamente")
            
        except Exception as e:
            print(f"\n❌ Error general: {str(e)}")
            raise ValueError(f"Error al conectar con GitHub: {str(e)}")
        
        # Inicializar LLM
        self.llm = Ollama(model="qwen3:8b")
        
        # Inicializar herramientas
        self.tools = [
            self.analyze_issue,
            self.create_pull_request,
            self.get_repository_content,
            self.create_file,
            self.update_file,
            self.delete_file
        ]
        
        # Inicializar memoria
        self.memory = MemorySaver()
        
        # Crear el grafo del agente
        self.workflow = self._create_workflow()
        
        # Crear el ejecutor del agente
        self.agent_executor = self.workflow.compile()

    def list_issues(self) -> str:
        """Lista todos los issues disponibles en el repositorio."""
        try:
            repo = self.github_client.get_repo(GITHUB_REPOSITORY)            
            issues = repo.get_issues(state='open')
            issues_list = []
            for issue in issues:
                issues_list.append(f"#{issue.number}: {issue.title}")
            
            if not issues_list:
                return "No hay issues abiertos en el repositorio."
            
            return "\n".join(issues_list)
        except Exception as e:
            error_msg = f"Error al acceder al repositorio: {str(e)}"
            print(f"\n❌ {error_msg}")
            print("\nPosibles soluciones:")
            print("1. Verifica que el nombre del repositorio sea correcto")
            print("2. Verifica que el token tenga permisos de lectura en el repositorio")
            print("3. Verifica que el repositorio exista y sea accesible")
            return error_msg

    @tool
    def analyze_issue(self, issue_number: int) -> str:
        """Analiza un issue de GitHub y retorna información relevante.
        
        Args:
            issue_number: El número del issue a analizar
            
        Returns:
            str: Información detallada del issue
        """
        try:
            print(f"\n🔍 Analizando issue #{issue_number}")
            repo = self.github_client.get_repo(GITHUB_REPOSITORY)
            issue = repo.get_issue(issue_number)
            print(f"✓ Issue encontrado: #{issue.number} - {issue.title}")
            print(f"Descripción: {issue.body}")
            print(f"Labels: {[label.name for label in issue.labels]}")
            return f"Issue Title: {issue.title}\nDescription: {issue.body}\nLabels: {[label.name for label in issue.labels]}"
        except Exception as e:
            print(f"❌ Error analizando issue: {str(e)}")
            return f"Error analyzing issue: {str(e)}"

    @tool
    def create_pull_request(self, pr_data: Dict[str, Any]) -> str:
        """Crea un pull request con la solución propuesta."""
        try:
            repo = self.github_client.get_repo(GITHUB_REPOSITORY)
            pr = repo.create_pull(
                title=pr_data["title"],
                body=pr_data["body"],
                head=f"{github_config['working_branch']}/issue-{pr_data['issue_number']}",
                base=github_config["base_branch"]
            )
            return f"Pull request created: {pr.html_url}"
        except Exception as e:
            return f"Error creating pull request: {str(e)}"

    @tool
    def get_repository_content(self, file_path: str) -> str:
        """Obtiene el contenido de un archivo del repositorio."""
        try:
            repo = self.github_client.get_repo(GITHUB_REPOSITORY)
            content = repo.get_contents(file_path)
            return content.decoded_content.decode()
        except Exception as e:
            return f"Error getting file content: {str(e)}"

    @tool
    def create_file(self, file_data: Dict[str, Any]) -> str:
        """Crea un nuevo archivo en el repositorio."""
        try:
            repo = self.github_client.get_repo(GITHUB_REPOSITORY)
            repo.create_file(
                path=file_data["path"],
                message=file_data["message"],
                content=file_data["content"],
                branch=github_config["working_branch"]
            )
            return f"File created: {file_data['path']}"
        except Exception as e:
            return f"Error creating file: {str(e)}"

    @tool
    def update_file(self, file_data: Dict[str, Any]) -> str:
        """Actualiza un archivo existente en el repositorio."""
        try:
            repo = self.github_client.get_repo(GITHUB_REPOSITORY)
            file = repo.get_contents(file_data["path"])
            repo.update_file(
                path=file_data["path"],
                message=file_data["message"],
                content=file_data["content"],
                sha=file.sha,
                branch=github_config["working_branch"]
            )
            return f"File updated: {file_data['path']}"
        except Exception as e:
            return f"Error updating file: {str(e)}"

    @tool
    def delete_file(self, file_data: Dict[str, Any]) -> str:
        """Elimina un archivo del repositorio."""
        try:
            repo = self.github_client.get_repo(GITHUB_REPOSITORY)
            file = repo.get_contents(file_data["path"])
            repo.delete_file(
                path=file_data["path"],
                message=file_data["message"],
                sha=file.sha,
                branch=github_config["working_branch"]
            )
            return f"File deleted: {file_data['path']}"
        except Exception as e:
            return f"Error deleting file: {str(e)}"

    def _create_workflow(self) -> StateGraph:
        """Crea el grafo de flujo de trabajo del agente."""
        # Crear el grafo
        workflow = StateGraph(AgentState)
        
        # Definir nodos del grafo
        def analyze_step(state: AgentState) -> AgentState:
            """Paso de análisis del issue."""
            try:
                messages = state["messages"]
                issue_data = state["issue_data"]
                print(f"\n🔍 Analizando issue: {issue_data}")
                
                # Obtener análisis del issue usando el número del issue
                analysis_result = self.analyze_issue.invoke(issue_data["number"])
                print(f"✓ Análisis obtenido: {analysis_result}")
                
                # Actualizar estado
                new_state = dict(state)
                new_state["current_step"] = "analysis"
                new_state["analysis"] = analysis_result
                new_state["messages"] = messages + [AIMessage(content=f"Análisis del issue:\n{analysis_result}")]
                new_state["steps"] = state.get("steps", []) + ["Análisis completado"]
                return new_state
            except Exception as e:
                print(f"❌ Error en analyze_step: {str(e)}")
                raise
        
        def solution_step(state: AgentState) -> AgentState:
            """Paso de generación de solución."""
            try:
                messages = state["messages"]
                print("\n💡 Generando solución...")
                
                # Generar solución usando el LLM
                solution_prompt = f"""
                Basado en el siguiente análisis:
                {state['analysis']}
                
                Genera una solución detallada para el issue.
                """
                solution = self.llm.invoke(solution_prompt)
                print(f"✓ Solución generada: {solution}")
                
                # Actualizar estado
                new_state = dict(state)
                new_state["current_step"] = "solution"
                new_state["solution"] = solution
                new_state["messages"] = messages + [AIMessage(content=f"Solución propuesta:\n{solution}")]
                new_state["steps"] = state.get("steps", []) + ["Solución generada"]
                return new_state
            except Exception as e:
                print(f"❌ Error en solution_step: {str(e)}")
                raise
        
        def create_pr_step(state: AgentState) -> AgentState:
            """Paso de creación de pull request."""
            try:
                messages = state["messages"]
                issue_data = state["issue_data"]
                print("\n📝 Creando pull request...")
                
                # Preparar datos del PR
                pr_data = {
                    "title": f"Fix for issue #{issue_data['number']}",
                    "body": state["solution"],
                    "issue_number": issue_data["number"]
                }
                
                # Crear PR
                pr_result = self.create_pull_request(pr_data)
                print(f"✓ Pull request creado: {pr_result}")
                
                # Actualizar estado
                new_state = dict(state)
                new_state["current_step"] = "pr_created"
                new_state["messages"] = messages + [AIMessage(content=f"Pull request creado:\n{pr_result}")]
                new_state["steps"] = state.get("steps", []) + ["Pull request creado"]
                return new_state
            except Exception as e:
                print(f"❌ Error en create_pr_step: {str(e)}")
                raise
        
        # Agregar nodos al grafo
        workflow.add_node("analyze", analyze_step)
        workflow.add_node("generate_solution", solution_step)
        workflow.add_node("create_pr", create_pr_step)
        
        # Definir el flujo
        workflow.add_edge("analyze", "generate_solution")
        workflow.add_edge("generate_solution", "create_pr")
        workflow.add_edge("create_pr", END)
        
        # Establecer el nodo inicial
        workflow.set_entry_point("analyze")
        
        return workflow

    def fix_issue(self, issue_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Método principal para resolver un issue.
        
        Args:
            issue_data: Diccionario con los datos del issue
            
        Returns:
            Diccionario con los resultados del proceso
        """
        try:
            # Estado inicial
            initial_state = {
                "messages": [HumanMessage(content=f"Voy a analizar y resolver el issue #{issue_data['number']}")],
                "issue_data": issue_data,
                "current_step": "start",
                "analysis": "",
                "solution": "",
                "steps": [],
                "recommendations": []
            }
            
            # Configuración para el thread_id
            config = {"configurable": {"thread_id": f"issue_{issue_data['number']}"}}
            
            # Ejecutar el agente paso a paso
            final_state = None
            for step in self.agent_executor.stream(initial_state, config):
                final_state = step
                print(f"Paso actual: {step.get('current_step', 'unknown')}")
                if 'analysis' in step:
                    print(f"Análisis: {step['analysis']}")
                if 'solution' in step:
                    print(f"Solución: {step['solution']}")
            
            if not final_state:
                return {"error": "No se obtuvo un estado final"}
            
            # Asegurarse de que todas las claves necesarias estén presentes
            return {
                "analysis": final_state.get("analysis", ""),
                "solution": final_state.get("solution", ""),
                "steps": final_state.get("steps", []),
                "recommendations": final_state.get("recommendations", []),
                "current_step": final_state.get("current_step", "unknown")
            }
            
        except Exception as e:
            print(f"Error en fix_issue: {str(e)}")
            return {"error": str(e)}


# Datos de prueba
test_issue = {
    "number": 2,
    "title": "Test Issue",
    "body": "This is a test issue for the CodeFixerAgent"
}
