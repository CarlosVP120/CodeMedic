import modal
from typing import Any, Dict
import os

# Crear la aplicación Modal
app = modal.App("codemedic-server")

# Definir la imagen con todas las dependencias y el código
image = (
    modal.Image.debian_slim()
    .pip_install_from_requirements("requirements.txt")
    .copy_local_dir("./app", "/root/app")  # Copiar el directorio app completo
    .env({"PYTHONPATH": "/root"})
)

@app.function(
    image=image,
    gpu="L4",  # Empezamos con L4 que es más barato para pruebas
    timeout=300,  # 5 minutos de timeout
    secrets=[modal.Secret.from_name("huggingface-secret")]
)
@modal.asgi_app()
def fastapi_app():
    """
    Aplicación FastAPI completa con documentación automática
    Disponible en /docs para Swagger UI y /redoc para ReDoc
    """
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    import sys
    sys.path.append("/root")
    
    from app.models.models import GitHubIssue, GitHubCredentials
    from app.services.AgentService import AgentService
    
    # Crear la aplicación FastAPI
    fastapi = FastAPI(
        title="CodeMedic API",
        description="""
        **CodeMedic** es una API para arreglar issues de GitHub usando IA.
        
        ## Características
        
        * **ReactAgent**: Agente basado en LangGraph con ReAct pattern
        * **HuggingFace**: Usando el modelo Qwen/Qwen3-4B 
        * **GitHub Integration**: Herramientas para interactuar con repositorios
        * **GPU Processing**: Ejecutándose en Modal con GPU L4
        
        ## Uso
        
        1. Configura tus credenciales de GitHub
        2. Envía un issue para procesar
        3. Recibe la respuesta del agente con la solución
        """,
        version="1.0.0"
    )
    
    # Modelo para el request
    class FixIssueRequest(BaseModel):
        github_credentials: dict
        issue_data: dict
        
        class Config:
            schema_extra = {
                "example": {
                    "github_credentials": {
                        "token": "ghp_xxxxxxxxxxxxxxxxxxxx",
                        "repository_name": "mi-usuario/mi-repositorio"
                    },
                    "issue_data": {
                        "number": 42,
                        "title": "Bug en autenticación",
                        "body": "La autenticación de usuarios está fallando",
                        "state": "open",
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z"
                    }
                }
            }
    
    @fastapi.post("/", 
                  summary="Arreglar Issue con ReactAgent",
                  description="Procesa un issue de GitHub usando ReactAgent con HuggingFace",
                  response_description="Respuesta del agente con la solución propuesta")
    async def fix_issue_with_react_agent(request_data: FixIssueRequest):
        """
        **Arregla un issue de GitHub usando ReactAgent**
        
        Este endpoint:
        - 🔍 Analiza el issue proporcionado
        - 🤖 Usa ReactAgent con modelo Qwen/Qwen3-4B
        - 🛠️ Interactúa con GitHub para obtener contexto
        - 💡 Genera una solución propuesta
        - 📝 Puede crear branches y pull requests
        
        **Parámetros:**
        - `github_credentials`: Token y nombre del repositorio
        - `issue_data`: Información completa del issue
        
        **Respuesta:**
        - `status`: "success" o "error" 
        - `data`: Mensajes y resumen del agente
        """
        try:
            # Verificar que el token de HuggingFace esté disponible
            hf_token = os.getenv("HUGGINGFACE_HUB_TOKEN")
            if not hf_token:
                raise HTTPException(status_code=500, detail="HuggingFace token no encontrado en secrets")
                        
            # Validar y parsear los datos de entrada
            github_credentials = GitHubCredentials(**request_data.github_credentials)
            issue_data = GitHubIssue(**request_data.issue_data)
            
            # Crear el servicio y procesar con ReactAgent
            agent_service = AgentService(github_credentials, issue_data)
            agent_response = agent_service.fix_issue_structured()  # Internamente usa ReactAgent
            
            print("ReactAgent response:", agent_response)
            return {"status": "success", "data": agent_response}
            
        except Exception as e:
            import traceback
            print(f"Error in ReactAgent processing: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @fastapi.get("/health", 
                 summary="Health Check",
                 description="Verifica que el servicio esté funcionando correctamente")
    async def health_check():
        """
        **Health Check del servicio**
        
        Retorna información básica sobre el estado del servicio:
        - ✅ Estado del servicio
        - 🤖 Tipo de agente (ReactAgent)
        - 🧠 Modelo utilizado (Qwen/Qwen3-4B)
        - 🏗️ Proveedor (HuggingFace)
        """
        return {
            "message": "CodeMedic API is running on Modal!", 
            "status": "healthy",
            "agent_type": "ReactAgent",
            "model": "Qwen/Qwen3-4B",
            "provider": "HuggingFace",
            "docs_url": "/docs",
            "redoc_url": "/redoc"
        }
    
    return fastapi

# Función para deployment local
@app.local_entrypoint()
def main():
    """Deploy the app"""
    print("🚀 Deploying CodeMedic with ReactAgent to Modal...")
    print("📡 Your API will be available at the Modal-generated URL")
    print("📚 Documentation will be available at /docs and /redoc") 