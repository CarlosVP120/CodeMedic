import json
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict
from langchain_ollama import ChatOllama
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler


model = ChatOllama(
    model="phi4:14b",
    temperature=0,
    callbacks=[StreamingStdOutCallbackHandler()],
    # other params...
)


# ---- Estado del agente ----
class CodeTestPair(TypedDict):
    correct_code: str
    unit_test: str

class AgentState(TypedDict):
    code_tests: List[Dict[str, str]]

#i
def read_jsonl_node(state: AgentState) -> AgentState:
    print("[Lectura] Leyendo archivo python_bugs.jsonl ...")
    with open("simple_python_bugs.jsonl", "r") as f:
        lines = f.readlines()
    code_tests = [{"correct_code": json.loads(line)["correct_code"], "unit_test": ""} for line in lines]
    print(f"[Lectura] Se leyeron {len(code_tests)} códigos. Ejemplo:")
    if code_tests:
        print(f"[Lectura] Código ejemplo:\n{code_tests[0]['correct_code'][:200]}\n---")
    return {"code_tests": code_tests}

# ---- Función 2: generar pruebas con LLM ----
import json
import re
from typing import Dict

def lm_call_node(state: Dict) -> Dict:
    print("[Generación] Generando pruebas unitarias para cada código...")
    output_path = "unit_tests_output.jsonl"
    code_tests = []

    # Abrir el archivo en modo append al inicio
    with open(output_path, "a") as f:
        for idx, item in enumerate(state["code_tests"]):
            code = item["correct_code"]
            print(f"[Generación] Generando test para código #{idx + 1} (primeros 100 chars):\n{code[:100]}\n...")

            prompt = f"""You are a code evaluation assistant.

Your task is to generate a Python function named `check(candidate)` that tests the correctness of the given implementation.
The function named `candidate` will be passed into `check()`.

Instructions:
- Use only `assert` statements to validate that `candidate(...)` produces the correct results.
- Derive inputs and expected outputs from the function’s docstring if available.
- If there is no docstring, make reasonable assumptions based on the function logic.
- Do not include the implementation of the function in the output — only the check() function.

Example format:
def check(candidate):
    assert candidate(2, 3) == 5
    assert candidate(-1, 1) == 0

Code to test:
{code}
"""

            response = model.invoke(prompt)
            unit_test_raw = response.content.strip()

            # Extraer solo el bloque de código si está presente
            unit_test = unit_test_raw
            if '```' in unit_test_raw:
                matches = re.findall(r'```(?:python)?\n([\s\S]*?)```', unit_test_raw)
                if matches:
                    unit_test = matches[0].strip()

            print(f"[Generación] Test generado (primeros 100 chars):\n{unit_test[:100]}\n---")

            record = {
                "correct_code": code,
                "unit_test": unit_test
            }

            # Guardar inmediatamente en disco
            f.write(json.dumps(record) + "\n")
            f.flush()  # Asegura que se escriba incluso si hay una interrupción

            code_tests.append(record)

    print(f"[Generación] Se generaron {len(code_tests)} pruebas unitarias.")
    return {"code_tests": code_tests}


# ---- Función 3: guardar pruebas al archivo ----
def add_to_jsonl_node(state: AgentState) -> AgentState:
    print("[Guardado] Guardando resultados en unit_tests_output.jsonl ...")
    with open("unit_tests_output.jsonl", "w") as f:
        for item in state["code_tests"]:
            f.write(json.dumps({
                "correct_code": item["correct_code"],
                "unit_test": item["unit_test"]
            }) + "\n")
    print(f"[Guardado] Se guardaron {len(state['code_tests'])} pares código/test en unit_tests_output.jsonl.")
    return state

# ---- Construcción del grafo ----
builder = StateGraph(AgentState)
builder.set_entry_point("read_jsonl")
builder.add_node("read_jsonl", read_jsonl_node)
builder.add_node("lm_call", lm_call_node)
builder.add_node("add_to_jsonl", add_to_jsonl_node)

builder.add_edge("read_jsonl", "lm_call")
builder.add_edge("lm_call", "add_to_jsonl")
builder.add_edge("add_to_jsonl", END)

graph = builder.compile()

# ---- Ejecución ----
print("[Ejecución] Iniciando pipeline de generación de tests unitarios...")
for event in graph.stream({}):
    print(f"[Evento] {event}")
print("[Ejecución] Pipeline finalizado. Revisa unit_tests_output.jsonl para los resultados.")