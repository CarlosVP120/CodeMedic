# CodeMedic

CodeMedic es una solución integral que combina:
- Una extensión de VS Code para gestionar issues de GitHub
- Un servidor FastAPI que expone endpoints para procesar issues
- Un agente basado en LangGraph que utiliza LLM para analizar y resolver problemas de código

## Arquitectura

El sistema consta de tres componentes principales:

1. **Extensión de VS Code**: Interfaz de usuario que permite a los desarrolladores ver y seleccionar issues de GitHub para ser solucionados automáticamente.
2. **Servidor FastAPI**: Backend que recibe los issues y los pasa al agente para su procesamiento.
3. **Agente LangGraph**: Sistema basado en LLM que analiza los issues y propone soluciones.

## Requisitos Previos

- Node.js y npm (para la extensión)
- Python 3.8+ (para el servidor y el agente)
- Token de GitHub con permisos para acceder a los repositorios
- VS Code (para ejecutar la extensión)

## Configuración

1. **Configurar el token de GitHub**
   ```bash
   # Crear archivo .env en la raíz del proyecto
   echo "GITHUB_TOKEN=tu_token_de_github" > .env
   ```

2. **Instalar dependencias del servidor y agente**
   ```bash
   # Opcional pero recomendado: crear entorno virtual
   python -m venv venv
   source venv/bin/activate  # Unix/macOS
   # venv\Scripts\activate  # Windows
   
   # Instalar dependencias
   pip install -r server/requirements.txt
   ```

3. **Instalar dependencias de la extensión**
   ```bash
   cd extension
   npm install
   ```

## Ejecución

### 1. Iniciar el servidor FastAPI (API Backend)

```bash
# Navegar al directorio del servidor
cd server

# Activar el entorno virtual si es necesario
# source ../venv/bin/activate  # Descomenta si usas un entorno virtual

# Iniciar el servidor FastAPI
uvicorn main:app --reload
```

Mantén esta terminal abierta para ver los logs del servidor y el procesamiento del agente.

### 2. Compilar y ejecutar la extensión de VS Code

En una nueva terminal:

```bash
# Navegar al directorio de la extensión
cd extension

# Instalar dependencias (si no lo has hecho antes)
npm install

# Compilar la extensión
npm run compile

# Iniciar VS Code con la extensión
code --extensionDevelopmentPath=$PWD ..
```

### 3. Usar la extensión en VS Code

1. Una vez que VS Code se abra, verás el icono de CodeMedic en la barra de actividad (icono de insecto)
2. Haz clic en el icono para abrir la vista de GitHub Issues
3. Si es necesario, autentícate con GitHub haciendo clic en "Authenticate"
4. Verás la lista de issues del repositorio actual
5. Para resolver un issue:
   - Opción 1: Haz clic en el icono de "Fix Issue with CodeMedic" (icono de probeta) junto al issue
   - Opción 2: Haz clic en el issue para abrir el panel de detalles y luego haz clic en el botón "Fix this issue with CodeMedic"

### 4. Ver los resultados

- En la terminal donde ejecutaste el servidor (paso 1), verás los logs del agente analizando y resolviendo el issue
- En VS Code, verás una notificación de progreso seguida de un mensaje de éxito cuando el issue sea procesado

### 5. Probar el sistema con un script (opcional)

Si prefieres probar el sistema sin VS Code:

```bash
# Asegúrate de estar en el directorio raíz del proyecto
cd /ruta/al/proyecto/CodeMedic

# Ejecutar el script de prueba
python test_fix_code.py
```

## Estructura del Proyecto

```
CodeMedic/
├── agent/                     # Agente LangGraph
│   ├── models/                # Modelos de datos
│   ├── tools/                 # Herramientas del agente
│   └── ollama_langgraph_agent.py  # Implementación principal del agente
├── extension/                 # Extensión de VS Code
│   ├── src/                   # Código fuente de la extensión
│   ├── package.json           # Configuración de la extensión
│   └── README.md              # Documentación de la extensión
├── server/                    # Servidor FastAPI
│   ├── app/                   # Aplicación FastAPI
│   └── main.py                # Punto de entrada del servidor
├── .env                       # Variables de entorno (token de GitHub)
├── test_fix_code.py           # Script de prueba
└── README.md                  # Este archivo
```

## Solución de Problemas

### Error de importación en Python
Si encuentras problemas con las importaciones, revisa las rutas en los archivos:
- server/app/routes.py
- agent/ollama_langgraph_agent.py
- agent/tools/tools.py

### Problemas de conexión con el servidor
Asegúrate de que:
- El servidor está ejecutándose en http://localhost:8000
- No hay otro proceso utilizando el puerto 8000
- La extensión está configurada para usar la URL correcta del servidor

### Error de autenticación con GitHub
Verifica que:
- Tu token de GitHub es válido y tiene los permisos necesarios
- El token está correctamente configurado en el archivo .env

## Contribuciones

Las contribuciones son bienvenidas. Para contribuir:
1. Haz fork del repositorio
2. Crea una rama para tu característica (`git checkout -b feature/amazing-feature`)
3. Haz commit de tus cambios (`git commit -m 'Add some amazing feature'`)
4. Push a la rama (`git push origin feature/amazing-feature`)
5. Abre un Pull Request

## Licencia

Este proyecto está licenciado bajo [MIT License](LICENSE).

## Contacto

Para más información o soporte, abre un issue en este repositorio. 