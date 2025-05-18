import requests
import json

# URL del servidor local
API_URL = "http://localhost:8000/fix"

# Ejemplo de código OOP con un bug
test_code = """
class Calculator:
    def __init__(self):
        self.value = 0
    
    def add(self, x):
        bug  # Este es un bug que debería ser reemplazado por 'fix'
        self.value += x
        return self.value
"""

# Log de ejemplo
test_log = {
    "error_type": "SyntaxError",
    "line_number": 8,
    "error_message": "Invalid syntax"
}

# Preparar la petición
payload = {
    "code": test_code,
    "log": test_log
}

def test_api():
    try:
        # Hacer la petición POST
        response = requests.post(API_URL, json=payload)
        
        # Verificar el código de estado
        print(f"Status Code: {response.status_code}")
        
        # Imprimir la respuesta
        if response.status_code == 200:
            result = response.json()
            print("\nCódigo corregido:")
            print(result["fixed_code"])
        else:
            print("\nError en la respuesta:")
            print(response.json())
            
    except requests.exceptions.ConnectionError:
        print("Error: No se pudo conectar al servidor. Asegúrate de que el servidor esté corriendo en http://localhost:8000")
    except Exception as e:
        print(f"Error inesperado: {str(e)}")

if __name__ == "__main__":
    test_api() 