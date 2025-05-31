# 🚀 Guía Completa: Deploy de CodeMedic en Modal

Esta guía documenta todos los pasos necesarios para migrar el servidor de CodeMedic de localhost a **Modal**, una plataforma serverless especializada en aplicaciones de IA con soporte para GPU.

## 📋 Tabla de Contenido

1. [Prerrequisitos](#prerrequisitos)
2. [¿Por qué Modal?](#por-qué-modal)
3. [Instalación y Setup](#instalación-y-setup)
4. [Configuración de la Aplicación](#configuración-de-la-aplicación)
5. [Configuración de Secrets](#configuración-de-secrets)
6. [Deploy y Correcciones](#deploy-y-correcciones)
7. [Actualización de la Extensión](#actualización-de-la-extensión)
8. [Corrección de Respuestas](#corrección-de-respuestas)
9. [Verificación y Testing](#verificación-y-testing)
10. [Monitoreo y Costos](#monitoreo-y-costos)
11. [Troubleshooting](#troubleshooting)

## 🔧 Prerrequisitos

- Python 3.8+ con pip
- Node.js y npm para la extensión
- Cuenta en [Modal](https://modal.com)
- Token de HuggingFace para el modelo Qwen/Qwen3-4B
- Proyecto CodeMedic existente
- VS Code para la extensión

## 🤔 ¿Por qué Modal?

**Problema Original**: Azure for Students no permite crear máquinas virtuales con GPU, limitando el uso de modelos de IA.

**Solución Modal**:
- ✅ Acceso inmediato a GPUs (H100, A100, L4, etc.)
- ✅ Pricing por segundo (solo pagas por uso)
- ✅ Escalado automático de 0 a múltiples instancias
- ✅ $30/mes de créditos gratuitos
- ✅ Especializado en aplicaciones de IA
- ✅ Sin contratos largos ni compromisos

## 📦 Instalación y Setup

### 1. Instalar Modal

```bash
# Navegar al directorio del servidor
cd server/

# Instalar Modal en tu entorno virtual
pip install modal
```

### 2. Configurar Autenticación

```bash
# Configurar Modal con tu cuenta
python3 -m modal setup
```

Este comando:
- Abrirá tu navegador para autenticación
- Generará un token de API
- Lo guardará en `~/.modal.toml`

## 🏗️ Configuración de la Aplicación

### 3. Crear `modal_app.py`

Crear el archivo `server/modal_app.py` con la configuración de la aplicación:

```python
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
    gpu="L4",  # GPU costo-efectiva para pruebas
    timeout=300,  # 5 minutos de timeout
    secrets=[modal.Secret.from_name("huggingface-secret")]
)
@modal.fastapi_endpoint(method="POST", label="codemedic-api")
def fix_issue_with_react_agent(request_data: Dict[str, Any]):
    """
    Endpoint para arreglar issues usando ReactAgent con HuggingFace
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
```

### 📝 Puntos Clave de la Configuración:

1. **Imagen Base**: `debian_slim` con todas las dependencias
2. **GPU**: L4 (equilibrio costo/rendimiento para pruebas)
3. **Timeout**: 5 minutos para operaciones largas
4. **Secrets**: Configuración segura para tokens
5. **Endpoints**: FastAPI compatible con Modal

## 🔐 Configuración de Secrets

### 4. Crear Secret de HuggingFace

```bash
# Crear secret con tu token de HuggingFace
modal secret create huggingface-secret HUGGINGFACE_HUB_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Ejemplo con token real**:
```bash
modal secret create huggingface-secret HUGGINGFACE_HUB_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## 🚀 Deploy y Correcciones

### 5. Primer Deploy

```bash
# Deploy inicial
modal deploy modal_app.py
```

### 6. Problemas Encontrados y Soluciones

#### Problema 1: Decorador Deprecado
**Error**: `@modal.web_endpoint` está deprecado
**Solución**: Actualizar a `@modal.fastapi_endpoint`

#### Problema 2: Importaciones Fallidas
**Error**: `No module named 'app'`
**Solución**: 
- Usar `.copy_local_dir("./app", "/root/app")` para copiar código
- Agregar `sys.path.append("/root")` en las funciones
- Importar módulos dentro de las funciones

#### Problema 3: Token de HuggingFace No Pasado
**Error**: `You must provide an api_key to work with nebius API`
**Solución**: Actualizar `ReactAgent.py` para usar el token:

```python
# En server/app/services/ReactAgent.py
def run(self, github_issue: GitHubIssue):
    # Get HuggingFace token from environment
    hf_token = os.getenv("HUGGINGFACE_HUB_TOKEN")
    if not hf_token:
        raise ValueError("HuggingFace token not found in environment variables")
    
    print(f"ReactAgent using HuggingFace token: {hf_token[:10]}...")

    # Create base LLM with authentication
    base_llm = HuggingFaceEndpoint(
        model="Qwen/Qwen3-4B",
        task="text-generation",
        max_new_tokens=1000,
        do_sample=False,
        repetition_penalty=1.03,
        temperature=0.1,
        huggingfacehub_api_token=hf_token  # ✅ LÍNEA CLAVE
    )
```

### 7. Deploy Final Exitoso

```bash
# Deploy final con todas las correcciones
modal deploy modal_app.py
```

**Resultado**:
```
✓ Created objects.
├── 🔨 Created web function fix_issue_with_react_agent => https://gerardosanchezz--codemedic-api.modal.run
└── 🔨 Created web function health_check => https://gerardosanchezz--health-check.modal.run
✓ App deployed in 16.051s! 🎉
```

## 🔗 Actualización de la Extensión

### 8. Actualizar Endpoints

Modificar `extension/src/utils/constants.ts`:

```typescript
// ANTES (localhost)
export const API_BASE_URL = 'http://localhost:8000';
export const API_FIX_ISSUE_STRUCTURED_ENDPOINT = 'http://localhost:8000/api/fix/issue/structured';

// DESPUÉS (Modal)
export const API_BASE_URL = 'https://gerardosanchezz--codemedic-api.modal.run';
export const API_FIX_ISSUE_STRUCTURED_ENDPOINT = 'https://gerardosanchezz--codemedic-api.modal.run';
```

## 🔧 Corrección de Respuestas

### 9. Problema de Estructura de Respuesta

**Problema Identificado**: La extensión no mostraba la respuesta de Modal.

**Causa**: Modal regresa la estructura `{status: "success", data: {...}}` pero la extensión esperaba `{messages: [...], summary: "..."}`

**Solución**: Actualizar `extension/src/services/structuredAgentService.ts`:

```typescript
// ANTES - Incorrecto
if (responseData && responseData.messages && responseData.summary) {
    return {
        result: 'complete',
        details: '',
        structuredData: responseData,
        agentMessages: responseData.messages,
        agentSummary: responseData.summary
    } as AgentResponse;
}

// DESPUÉS - Correcto
if (responseData && responseData.status === 'success' && responseData.data) {
    const agentData = responseData.data;
    
    if (agentData.messages && agentData.summary) {
        return {
            result: 'complete',
            details: this.formatFinalAgentOutput(agentData),
            structuredData: agentData,
            agentMessages: agentData.messages,
            agentSummary: agentData.summary
        } as AgentResponse;
    }
} else if (responseData && responseData.status === 'error') {
    return {
        result: 'error',
        details: `Agent error: ${responseData.detail || 'Unknown error'}`,
        error: responseData.detail || 'Unknown error'
    };
}
```

### 10. Compilar Extensión

```bash
# Compilar la extensión con los nuevos endpoints y correcciones
cd extension/
npm run compile
```

## ✅ Verificación y Testing

### 11. Probar Health Check

```bash
curl https://gerardosanchezz--health-check.modal.run
```

**Respuesta esperada**:
```json
{
  "message": "CodeMedic API is running on Modal!",
  "status": "healthy",
  "agent_type": "ReactAgent",
  "model": "Qwen/Qwen3-4B",
  "provider": "HuggingFace"
}
```

### 12. Probar API Principal

```bash
curl -X POST https://gerardosanchezz--codemedic-api.modal.run \
  -H "Content-Type: application/json" \
  -d '{
    "github_credentials": {
      "token": "test_token",
      "repository_name": "test_repo"
    },
    "issue_data": {
      "number": 1,
      "title": "Test issue",
      "body": "This is a test issue",
      "state": "open",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  }'
```

**Respuesta esperada**:
```json
{
  "status": "success",
  "data": {
    "messages": [...],
    "summary": "..."
  }
}
```

### 13. Probar Extensión de VS Code

1. **Abrir VS Code** con la extensión instalada
2. **Cargar la extensión actualizada**:
   - Presionar `F5` para abrir nueva ventana con extensión
   - O usar `Ctrl+Shift+P` → "Developer: Reload Window"
3. **Configurar credenciales de GitHub** en la extensión
4. **Seleccionar un issue** de GitHub
5. **Ejecutar "Fix Issue with Structured Agent"**
6. **Verificar que se muestra la respuesta** en el panel de CodeMedic

**Resultado esperado**:
- ✅ Notificación: "Starting to fix issue #X the agent..."
- ✅ Progress: "Connecting to CodeMedic agent..."
- ✅ Panel CodeMedic: Muestra mensajes y resumen del ReactAgent
- ✅ Notificación final: "Issue #X has been processed by the agent."

## 📊 Monitoreo y Costos

### URLs Importantes:
- **Dashboard**: https://modal.com/apps/gerardosanchezz/main/deployed/codemedic-server
- **Endpoint Principal**: https://gerardosanchezz--codemedic-api.modal.run
- **Health Check**: https://gerardosanchezz--health-check.modal.run

### Costos por GPU (por segundo):
- **L4**: $0.000222/sec (~$0.80/hora)
- **A100 40GB**: $0.000583/sec (~$2.10/hora)
- **A100 80GB**: $0.000694/sec (~$2.50/hora)
- **H100**: $0.001097/sec (~$3.95/hora)

### Créditos Gratuitos:
- **$30/mes** de créditos gratuitos
- Perfecto para desarrollo y pruebas

## 🔧 Troubleshooting

### Problemas Comunes:

#### 1. "No module named 'app'"
**Solución**: Verificar que `.copy_local_dir("./app", "/root/app")` esté en la imagen

#### 2. "HuggingFace token no encontrado"
**Solución**: Verificar que el secret esté creado correctamente:
```bash
modal secret list
```

#### 3. "You must provide an api_key to work with nebius API"
**Solución**: Asegurar que `huggingfacehub_api_token=hf_token` esté en `HuggingFaceEndpoint`

#### 4. Extensión no muestra respuesta
**Solución**: Verificar que la extensión maneje `responseData.data` en lugar de `responseData` directamente

#### 5. GPU no disponible
**Solución**: Cambiar a un tipo de GPU diferente o esperar disponibilidad

#### 6. Timeout en requests
**Solución**: Aumentar el `timeout` en la función o optimizar el código

### Comandos Útiles:

```bash
# Ver logs de la aplicación
modal app logs codemedic-server

# Ver secrets configurados
modal secret list

# Ver apps deployadas
modal app list

# Detener la aplicación
modal app stop codemedic-server

# Recompilar extensión
cd extension && npm run compile
```

## 🎯 Conclusión

La migración a Modal fue exitosa y resolvió todos los problemas:

✅ **Problema Resuelto**: Acceso a GPUs sin Azure VM limitations
✅ **Costo-Efectivo**: Solo pagas por uso real + $30 gratis/mes
✅ **Escalable**: De 0 a múltiples GPUs automáticamente
✅ **Funcional**: Extensión y API trabajando correctamente
✅ **Monitoreado**: Dashboard completo incluido

**Beneficios Adicionales**:
- Sin gestión de infraestructura
- Actualizaciones automáticas
- Respaldo y seguridad incluidos
- Soporte para múltiples tipos de GPU
- Integración perfecta con la extensión de VS Code

## 🚀 Estado Final

- 🟢 **Modal API**: Funcionando perfectamente
- 🟢 **ReactAgent**: Procesando issues correctamente
- 🟢 **HuggingFace**: Token configurado y funcionando
- 🟢 **Extensión**: Mostrando respuestas completas
- 🟢 **Integration**: End-to-end funcionando

---

## 📚 Referencias

- [Modal Documentation](https://modal.com/docs)
- [Modal GPU Guide](https://modal.com/docs/guide/gpu)
- [Modal Pricing](https://modal.com/pricing)
- [HuggingFace Models](https://huggingface.co/models)
- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)

---

**Nota**: Esta guía documenta el proceso completo realizado en enero 2025, incluyendo todas las correcciones necesarias para una integración exitosa. Los comandos y URLs pueden variar según tu configuración específica.

## ✨ Pasos de Replicación Rápida

Para replicar este setup desde cero:

1. `pip install modal` 
2. `python3 -m modal setup`
3. `modal secret create huggingface-secret HUGGINGFACE_HUB_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
4. Crear `modal_app.py` con el código proporcionado
5. Actualizar `ReactAgent.py` para incluir `huggingfacehub_api_token=hf_token`
6. `modal deploy modal_app.py`
7. Actualizar `constants.ts` con las URLs de Modal
8. Corregir `structuredAgentService.ts` para manejar `responseData.data`
9. `npm run compile` en la extensión
10. Probar en VS Code

¡Listo! 🎉 