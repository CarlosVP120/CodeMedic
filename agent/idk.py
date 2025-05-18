# def parse_llm_response(response: str) -> IssueAnalysis:
#     """Parsea la respuesta del LLM y la convierte en un IssueAnalysis."""
#     try:
#         # Intentar parsear la respuesta como JSON
#         data = json.loads(response)
#         return IssueAnalysis(**data)
#     except json.JSONDecodeError:
#         # Si no es JSON, intentar extraer la información de manera estructurada
#         lines = response.split('\n')
#         analysis = {
#             "issue_number": 0,  # Se actualizará después
#             "summary": "",
#             "impact": "",
#             "affected_areas": [],
#             "recommendations": [],
#             "technical_details": {},
#             "solution": ""
#         }
#
#         current_section = None
#         for line in lines:
#             line = line.strip()
#             if not line:
#                 continue
#
#             if line.startswith("Resumen:"):
#                 current_section = "summary"
#                 analysis["summary"] = line.replace("Resumen:", "").strip()
#             elif line.startswith("Impacto:"):
#                 current_section = "impact"
#                 analysis["impact"] = line.replace("Impacto:", "").strip()
#             elif line.startswith("Áreas afectadas:"):
#                 current_section = "affected_areas"
#                 areas = line.replace("Áreas afectadas:", "").strip()
#                 analysis["affected_areas"] = [area.strip() for area in areas.split(",")]
#             elif line.startswith("Recomendaciones:"):
#                 current_section = "recommendations"
#                 recs = line.replace("Recomendaciones:", "").strip()
#                 analysis["recommendations"] = [rec.strip() for rec in recs.split(",")]
#             elif line.startswith("Solución:"):
#                 current_section = "solution"
#                 analysis["solution"] = line.replace("Solución:", "").strip()
#             elif current_section and line.startswith("- "):
#                 if current_section == "recommendations":
#                     analysis["recommendations"].append(line[2:].strip())
#                 elif current_section == "affected_areas":
#                     analysis["affected_areas"].append(line[2:].strip())
#
#         return IssueAnalysis(**analysis)
#
# @tool
# def analyze_issue(issue_data: dict) -> str:
#     """
#     Analiza un issue de GitHub y proporciona un análisis detallado.
#     Espera un diccionario con las claves: number, title, body.
#     """
#     try:
#         # Convertir el diccionario a un modelo GitHubIssue
#         issue = GitHubIssue(**issue_data)
#
#         # Crear prompt para el análisis
#         analysis_prompt = f"""
#         Analiza el siguiente issue de GitHub y proporciona una respuesta estructurada:
#
#         Issue #{issue.number}: {issue.title}
#         Descripción: {issue.body}
#
#         Por favor, proporciona tu análisis en el siguiente formato JSON:
#         {{
#             "issue_number": {issue.number},
#             "summary": "Resumen conciso del problema",
#             "impact": "Impacto potencial del problema",
#             "affected_areas": ["Lista de áreas afectadas"],
#             "recommendations": ["Lista de recomendaciones"],
#             "technical_details": {{
#                 "created_at": "{issue.created_at.isoformat()}",
#                 "updated_at": "{issue.updated_at.isoformat()}",
#                 "state": "{issue.state}"
#             }},
#             "solution": "Solución propuesta para el problema"
#         }}
#         """
#
#         # Obtener respuesta del LLM
#         messages = [HumanMessage(content=analysis_prompt)]
#         response = model.invoke(messages)
#
#         # Parsear la respuesta y convertirla a IssueAnalysis
#         analysis = parse_llm_response(response.content)
#
#         # Actualizar el número de issue
#         analysis.issue_number = issue.number
#
#         return analysis.model_dump_json(indent=2)
#     except Exception as e:
#         return f"Error al analizar el issue: {str(e)}"
#
# @tool
# def create_pull_request(pr_data: dict) -> str:
#     """
#     Crea un pull request en GitHub.
#     Espera un diccionario con las claves: title, body, head_branch, base_branch, issue_number.
#     """
#     try:
#         # Convertir el diccionario a un modelo PullRequestData
#         pr = PullRequestData(**pr_data)
#
#         # Obtener el repositorio
#         repo = github_client.get_repo(GITHUB_REPOSITORY)
#
#         # Crear el pull request
#         pull_request = repo.create_pull(
#             title=pr.title,
#             body=pr.body,
#             head=f"{pr.head_branch}/issue-{pr.issue_number}",
#             base=pr.base_branch
#         )
#
#         return f"Pull request creado exitosamente: {pull_request.html_url}"
#     except Exception as e:
#         return f"Error al crear el pull request: {str(e)}"
