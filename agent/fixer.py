
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
from langchain_community.chat_models import ChatOllama
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
        
        # Inicializar herramientas
        self.tools = [
            self.analyze_issue,
            self.create_pull_request,
            self.get_repository_content,
            self.create_file,
            self.update_file,
            self.delete_file
        ]
        
        # Inicializar LLM con ChatOllama
        self.llm = ChatOllama(model="qwen3:8b")
        
        # Inicializar memoria
        self.memory = MemorySaver()
        
        # Crear el grafo del agente
        self.workflow = self._create_workflow()
        
        # Crear el ejecutor del agente
        self.agent_executor = self.workflow.compile()

    def list_issues(self) -> List[Dict[str, Any]]:
        """Lista todos los issues disponibles en el repositorio."""
        try:
            repo = self.github_client.get_repo(GITHUB_REPOSITORY)            
            issues = repo.get_issues(state='open')
            issues_list = []
            
            for issue in issues:
                issues_list.append({
                    "number": issue.number,
                    "title": issue.title,
                    "body": issue.body or "",
                    "state": issue.state,
                    "created_at": issue.created_at.isoformat(),
                    "updated_at": issue.updated_at.isoformat()
                })
            
            if not issues_list:
                print("No hay issues abiertos en el repositorio.")
                return []
            
            return issues_list
        except Exception as e:
            error_msg = f"Error al acceder al repositorio: {str(e)}"
            print(f"\n❌ {error_msg}")
            return []

    def _analyze_issue(self, issue_data: Dict[str, Any]) -> str:
        """Lógica interna para analizar un issue de GitHub y proporcionar un análisis detallado."""
        try:
            print(f"\n🔍 Analizando issue...")
            print(f"Analizando issue: {issue_data}")
            
            # Crear prompt para el análisis
            analysis_prompt = f"""
            Analiza el siguiente issue de GitHub:
            
            Título: {issue_data['title']}
            Descripción: {issue_data['body']}
            
            Proporciona un análisis detallado que incluya:
            1. Resumen del problema
            2. Impacto potencial
            3. Áreas afectadas
            4. Recomendaciones iniciales
            """
            
            # Obtener análisis del LLM usando el formato de mensajes
            messages = [HumanMessage(content=analysis_prompt)]
            response = self.llm.invoke(messages)
            analysis = response.content
            
            print(f"✓ Análisis completado para issue #{issue_data['number']}")
            
            return analysis
        except Exception as e:
            error_msg = f"Error al analizar el issue: {str(e)}"
            print(f"\n❌ {error_msg}")
            return error_msg

    @tool("analyze_issue")
    def analyze_issue(self, issue_data: Dict[str, Any]) -> str:
        """Herramienta para LangChain: llama a la lógica interna de análisis."""
        return self._analyze_issue(issue_data)

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
        """Crea el grafo de flujo del agente."""
        workflow = StateGraph(AgentState)

        def analyze_step(state: AgentState) -> AgentState:
            """Paso de análisis del issue."""
            try:
                print("\n🔍 Analizando issue...")
                issue_data = state.get("issue_data", {})
                print(f"Analizando issue: {issue_data}")

                # Llamar a la lógica interna directamente
                analysis_result = self._analyze_issue(issue_data)

                # Actualizar estado
                new_state = dict(state)
                new_state["current_step"] = "analyze"
                new_state["analysis"] = analysis_result
                new_state["messages"] = state.get("messages", []) + [AIMessage(content=f"Análisis del issue:\n{analysis_result}")]
                new_state["steps"] = state.get("steps", []) + ["Análisis completado"]
                return new_state
            except Exception as e:
                print(f"❌ Error en analyze_step: {str(e)}")
                raise

        def solution_step(state: AgentState) -> AgentState:
            """Paso de generación de solución."""
            try:
                print("\n💡 Generando solución...")
                messages = state.get("messages", [])

                # Crear prompt para la solución
                solution_prompt = f"""
                Basado en el siguiente análisis:
                {state['analysis']}

                Proporciona una solución técnica detallada y pasos específicos que se deben seguir para resolver el problema descrito en el issue.
                """
                # Usar el modelo LLM para generar la solución
                solution_result = self.llm.invoke(solution_prompt)

                new_state = dict(state)
                new_state["current_step"] = "solution"
                new_state["solution"] = solution_result
                new_state["messages"] = messages + [AIMessage(content=f"Solución propuesta:\n{solution_result}")]
                new_state["steps"] = state.get("steps", []) + ["Solución generada"]
                return new_state
            except Exception as e:
                print(f"❌ Error en solution_step: {str(e)}")
                raise

        # Añadir nodos al grafo
        workflow.add_node("analizar_issue", analyze_step)
        workflow.add_node("generar_solucion", solution_step)

        # Definir flujo entre nodos
        workflow.set_entry_point("analizar_issue")
        workflow.add_edge("analizar_issue", "generar_solucion")
        workflow.add_edge("generar_solucion", END)

        return workflow

    def fix_issue(self, issue_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Método principal para resolver un issue.
        
        Args:
            issue_data: Diccionario con los datos del issue (number, title, body, etc.).
            
        Returns:
            Diccionario con los resultados del proceso
        """
        try:
            print("\n🔍 Diagnóstico de fix_issue:")
            print(f"Tipo de issue_data: {type(issue_data)}")
            print(f"Claves disponibles: {list(issue_data.keys()) if isinstance(issue_data, dict) else 'No es un diccionario'}")
            print(f"Datos recibidos: {json.dumps(issue_data, indent=2) if isinstance(issue_data, dict) else issue_data}")
            
            # Verificar que issue_data sea un diccionario
            if not isinstance(issue_data, dict):
                raise ValueError(f"issue_data debe ser un diccionario, se recibió: {type(issue_data)}")
            
            # Verificar campos requeridos
            required_fields = ['number', 'title', 'body']
            missing_fields = [field for field in required_fields if field not in issue_data]
            if missing_fields:
                print(f"\n⚠️ Campos actuales en issue_data: {list(issue_data.keys())}")
                print(f"⚠️ Valores actuales:")
                for key, value in issue_data.items():
                    print(f"  - {key}: {value}")
                raise ValueError(f"Faltan campos requeridos en issue_data: {missing_fields}")
            
            # Estado inicial
            initial_state = {
                "messages": [HumanMessage(content=f"Voy a analizar y resolver el issue #{issue_data['number']}")],
                "issue_data": issue_data,  # Pasar el diccionario completo
                "current_step": "start",
                "analysis": "",
                "solution": "",
                "steps": [],
                "recommendations": []
            }
            
            print("\n✓ Estado inicial creado correctamente")
            print(f"Thread ID: issue_{issue_data['number']}")
            
            # Configuración para el thread_id
            config = {"configurable": {"thread_id": f"issue_{issue_data['number']}"}}
            
            # Ejecutar el agente paso a paso
            final_state = None
            for step in self.agent_executor.stream(initial_state, config):
                final_state = step
                print(f"\nPaso actual: {step.get('current_step', 'unknown')}")
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
            error_msg = f"Error en fix_issue: {str(e)}"
            print(f"\n❌ {error_msg}")
            import traceback
            print("\nDetalles del error:")
            print(traceback.format_exc())
            return {"error": error_msg}


# Datos de prueba
test_issue = {
    "number": 2,
    "title": "Test Issue",
    "body": "This is a test issue for the CodeFixerAgent"
}

if __name__ == "__main__":
    agent = CodeFixerAgent()
    
    issue_number = 1  # Cambia esto al número real del issue que quieres analizar

    initial_state: AgentState = {
        "messages": [HumanMessage(content=f"Por favor, analiza el issue #{issue_number}")],
        "issue_data": {"number": issue_number},
        "current_step": "",
        "analysis": "",
        "solution": "",
        "steps": [],
        "recommendations": []
    }

    final_state = agent.agent_executor.invoke(initial_state)
    print("\n✅ Ejecución completada")
    print("\n--- Mensajes finales ---")
    for msg in final_state["messages"]:
        print(f"\n[{msg.type}] {msg.content}")
