# Filtrado de Unit Tests

Este módulo contiene funciones para filtrar unit tests válidos sintácticamente desde archivos JSONL.

## Archivos

- `filter_valid_tests.py`: Contiene las funciones principales de filtrado
- `example_usage.py`: Script de ejemplo mostrando cómo usar las funciones
- `parse.py`: Script básico para parsing con AST

## Funciones Principales

### `unparsed_code(code_str)`

Verifica si un string de código Python es válido sintácticamente usando `ast.parse()` y `ast.unparse()`.

**Parámetros:**
- `code_str` (str): El código Python a verificar

**Retorna:**
- `bool`: `True` si el código es válido, `False` si hay errores de sintaxis

**Ejemplo:**
```python
from filter_valid_tests import unparsed_code

# Código válido
valid_code = "def test():\n    return True"
print(unparsed_code(valid_code))  # True

# Código inválido
invalid_code = "def test(\n    return True"
print(unparsed_code(invalid_code))  # False
```

### `filter_unit_tests_simple(input_file, output_file)`

Versión simplificada para filtrar unit tests válidos sin logging detallado.

**Parámetros:**
- `input_file` (str): Ruta del archivo JSONL de entrada
- `output_file` (str): Ruta del archivo JSONL de salida

**Retorna:**
- `dict`: Estadísticas del proceso con claves `total`, `valid`, `errors`

**Ejemplo:**
```python
from filter_valid_tests import filter_unit_tests_simple

stats = filter_unit_tests_simple(
    "unit_tests_output_1-100.jsonl",
    "unit_test_no_error.jsonl"
)
print(f"Procesados: {stats['total']}, Válidos: {stats['valid']}")
```

### `filter_valid_unit_tests(input_file, output_file)`

Versión completa con logging detallado para filtrar unit tests válidos.

**Parámetros:**
- `input_file` (str): Ruta del archivo JSONL de entrada (por defecto: "unit_tests_output_1-100.jsonl")
- `output_file` (str): Ruta del archivo JSONL de salida (por defecto: "unit_test_no_error.jsonl")

**Ejemplo:**
```python
from filter_valid_tests import filter_valid_unit_tests

# Usar con archivos por defecto
filter_valid_unit_tests()

# Usar con archivos personalizados
filter_valid_unit_tests("mi_input.jsonl", "mi_output.jsonl")
```

## Formato de Archivos

### Archivo de Entrada (JSONL)
Cada línea debe ser un objeto JSON con las siguientes claves:
```json
{
  "correct_code": "def example():\n    return 42",
  "unit_test": "def check(candidate):\n    assert candidate() == 42"
}
```

### Archivo de Salida (JSONL)
Contiene las mismas líneas del archivo de entrada, pero solo aquellas donde el `unit_test` es sintácticamente válido.

## Uso desde Línea de Comandos

```bash
# Ejecutar con archivos por defecto
python filter_valid_tests.py

# Ver ejemplos de uso
python example_usage.py
```

## Proceso de Filtrado

1. **Lectura**: Lee cada línea del archivo JSONL de entrada
2. **Extracción**: Extrae el campo `unit_test` de cada objeto JSON
3. **Validación**: Usa `ast.parse()` y `ast.unparse()` para verificar la sintaxis
4. **Filtrado**: Solo guarda las líneas completas donde el `unit_test` es válido
5. **Escritura**: Escribe las líneas válidas al archivo de salida

## Estadísticas de Ejemplo

```
[Filtrado] ✓ Proceso completado:
  - Total de tests procesados: 100
  - Tests válidos: 100
  - Tests con errores: 0
  - Archivo de salida: unit_test_no_error.jsonl
```

## Manejo de Errores

Las funciones manejan los siguientes tipos de errores:
- `SyntaxError`: Errores de sintaxis en el código Python
- `ValueError`: Errores de valor en el parsing
- `TypeError`: Errores de tipo
- `json.JSONDecodeError`: Errores al parsear JSON
- `FileNotFoundError`: Archivo de entrada no encontrado

## Requisitos

- Python 3.8+
- Módulos estándar: `json`, `ast`

## Notas Importantes

- **Preservación de datos**: Las líneas completas (incluyendo `correct_code` y `unit_test`) se mantienen en el archivo de salida
- **Encoding**: Los archivos se procesan con encoding UTF-8
- **Formato JSON**: Se preserva el formato JSON original sin modificaciones
- **Validación sintáctica**: Solo verifica sintaxis, no ejecución del código 