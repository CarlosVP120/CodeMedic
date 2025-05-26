#!/usr/bin/env python3
"""
Ejemplo de uso de las funciones de filtrado de unit tests.
"""

from filter_valid_tests import filter_unit_tests_simple, filter_valid_unit_tests, unparsed_code


def example_usage():
    """Ejemplo de cómo usar las funciones de filtrado."""
    
    print("=== Ejemplo de uso de las funciones de filtrado ===\n")
    
    # Ejemplo 1: Usar la función simple
    print("1. Usando filter_unit_tests_simple:")
    try:
        stats = filter_unit_tests_simple(
            input_file="unit_tests_output_1-100.jsonl",
            output_file="unit_test_no_error_simple.jsonl"
        )
        print(f"   ✓ Procesados: {stats['total']}")
        print(f"   ✓ Válidos: {stats['valid']}")
        print(f"   ✓ Con errores: {stats['errors']}")
    except FileNotFoundError:
        print("   ⚠️ Archivo de entrada no encontrado")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Ejemplo 2: Usar la función con logging detallado
    print("2. Usando filter_valid_unit_tests (con logging detallado):")
    try:
        filter_valid_unit_tests(
            input_file="unit_tests_output_1-100.jsonl",
            output_file="unit_test_no_error_detailed.jsonl"
        )
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Ejemplo 3: Probar la función unparsed_code directamente
    print("3. Probando unparsed_code directamente:")
    
    test_codes = [
        # Código válido
        "def test_function():\n    return True",
        
        # Código válido con imports
        "import json\ndef check(candidate):\n    assert candidate() == True",
        
        # Código inválido (sintaxis incorrecta)
        "def test_function(\n    return True",
        
        # Código inválido (indentación incorrecta)
        "def test_function():\nreturn True"
    ]
    
    for i, code in enumerate(test_codes, 1):
        is_valid = unparsed_code(code)
        status = "✓ Válido" if is_valid else "✗ Inválido"
        print(f"   Código {i}: {status}")
        print(f"   {repr(code[:50])}...")
        print()


if __name__ == "__main__":
    example_usage() 