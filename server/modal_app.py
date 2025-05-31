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
@modal.fastapi_endpoint(method="POST", label="codemedic-api")
def fix_issue_with_react_agent(request_data: Dict[str, Any]):
    """
    Endpoint para arreglar issues usando ReactAgent con HuggingFace
    
    Este endpoint utiliza:
    - ReactAgent: Agente basado en LangGraph con ReAct pattern
    - HuggingFace Endpoint: Usando el modelo Qwen/Qwen3-4B
    - Tools: Para interactuar con GitHub (obtener archivos, crear branches, etc.)
    """
    try:
        # Importar dentro de la función para evitar problemas de importación
        import sys
        sys.path.append("/root")
        
        from app.models.models import GitHubIssue, GitHubCredentials
        from app.services.AgentService import AgentService
        
        # Verificar que el token de HuggingFace esté disponible
        hf_token = os.getenv("HUGGINGFACE_HUB_TOKEN")
        if not hf_token:
            raise Exception("HuggingFace token no encontrado en secrets")
        
        print(f"Using HuggingFace token: {hf_token[:10]}...")
        
        # Validar y parsear los datos de entrada
        github_credentials = GitHubCredentials(**request_data["github_credentials"])
        issue_data = GitHubIssue(**request_data["issue_data"])
        
        # Crear el servicio y procesar con ReactAgent
        agent_service = AgentService(github_credentials, issue_data)
        agent_response = agent_service.fix_issue_structured()  # Internamente usa ReactAgent
        
        print("ReactAgent response:", agent_response)
        return {"status": "success", "data": agent_response}
        
    except Exception as e:
        import traceback
        print(f"Error in ReactAgent processing: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return {"status": "error", "detail": str(e)}, 500

@app.function(image=image)
@modal.fastapi_endpoint(method="GET", label="health-check")
def health_check():
    """Endpoint simple para verificar que el servicio está funcionando"""
    return {
        "message": "CodeMedic API is running on Modal!", 
        "status": "healthy",
        "agent_type": "ReactAgent",
        "model": "Qwen/Qwen3-4B",
        "provider": "HuggingFace"
    }

# Función para deployment local
@app.local_entrypoint()
def main():
    """Deploy the app"""
    print("🚀 Deploying CodeMedic with ReactAgent to Modal...")
    print("📡 Your API will be available at the Modal-generated URL") 