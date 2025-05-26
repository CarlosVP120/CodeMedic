import json
import ast


def unparsed_code(code_str):
    """
    Verifica si el código es válido sintácticamente usando ast.parse y ast.unparse.
    Retorna True si el código es válido, False si hay errores.
    """
    try:
        tree = ast.parse(code_str)
        unparsed_code = ast.unparse(tree)
        return True
    except (SyntaxError, ValueError, TypeError) as e:
        return False


def filter_unit_tests_simple(input_file, output_file):
    """
    Versión simplificada de la función para filtrar unit tests válidos.
    
    Args:
        input_file (str): Ruta del archivo JSONL de entrada
        output_file (str): Ruta del archivo JSONL de salida
        
    Returns:
        dict: Estadísticas del proceso (total, válidos, errores)
    """
    valid_tests = []
    total_tests = 0
    valid_count = 0
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line.strip())
            total_tests += 1
            
            unit_test = data.get('unit_test', '')
            if unit_test and unparsed_code(unit_test):
                valid_tests.append(data)
                valid_count += 1
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for test_data in valid_tests:
            f.write(json.dumps(test_data, ensure_ascii=False) + '\n')
    
    return {
        'total': total_tests,
        'valid': valid_count,
        'errors': total_tests - valid_count
    }


def filter_valid_unit_tests(input_file="unit_tests_output_1-100.jsonl", output_file="unit_test_no_error.jsonl"):
    """
    Lee el archivo JSONL de entrada, extrae los unit_test de cada línea,
    los verifica usando unparsed_code, y guarda las líneas completas que no den error.
    
    Args:
        input_file (str): Ruta del archivo JSONL de entrada
        output_file (str): Ruta del archivo JSONL de salida
    """
    valid_tests = []
    total_tests = 0
    valid_count = 0
    
    print(f"[Filtrado] Leyendo archivo: {input_file}")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    # Parsear la línea JSON
                    data = json.loads(line.strip())
                    total_tests += 1
                    
                    # Extraer el unit_test
                    unit_test = data.get('unit_test', '')
                    
                    if not unit_test:
                        print(f"[Filtrado] Línea {line_num}: unit_test vacío, omitiendo...")
                        continue
                    
                    # Verificar si el unit_test es válido usando unparsed_code
                    if unparsed_code(unit_test):
                        valid_tests.append(data)
                        valid_count += 1
                        print(f"[Filtrado] Línea {line_num}: ✓ unit_test válido")
                    else:
                        print(f"[Filtrado] Línea {line_num}: ✗ unit_test con errores de sintaxis")
                        
                except json.JSONDecodeError as e:
                    print(f"[Filtrado] Error al parsear JSON en línea {line_num}: {e}")
                except Exception as e:
                    print(f"[Filtrado] Error inesperado en línea {line_num}: {e}")
    
    except FileNotFoundError:
        print(f"[Error] No se encontró el archivo: {input_file}")
        return
    except Exception as e:
        print(f"[Error] Error al leer el archivo: {e}")
        return
    
    # Guardar los tests válidos en el archivo de salida
    print(f"[Filtrado] Guardando {valid_count} tests válidos en: {output_file}")
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for test_data in valid_tests:
                f.write(json.dumps(test_data, ensure_ascii=False) + '\n')
        
        print(f"[Filtrado] ✓ Proceso completado:")
        print(f"  - Total de tests procesados: {total_tests}")
        print(f"  - Tests válidos: {valid_count}")
        print(f"  - Tests con errores: {total_tests - valid_count}")
        print(f"  - Archivo de salida: {output_file}")
        
    except Exception as e:
        print(f"[Error] Error al escribir el archivo de salida: {e}")


if __name__ == "__main__":
    # Ejecutar la función con los archivos por defecto
    filter_valid_unit_tests() 