    def create_pull_request(pr_data: dict) -> str:
        """
        Crea un pull request en GitHub.
        Espera un diccionario con las claves: title, body, head_branch, base_branch, issue_number.
        """
        try:
            # Convertir el diccionario a un modelo PullRequestData
            pr = PullRequestData(**pr_data)
            
            # Obtener el repositorio
            repo = github_client.get_repo(GITHUB_REPOSITORY)
            
            # Crear el pull request
            pull_request = repo.create_pull(
                title=pr.title,
                body=pr.body,
                head=pr.head_branch,
                base=pr.base_branch
            )
            
            return f"Pull request creado exitosamente: {pull_request.html_url}"
        except Exception as e:
            return f"Error al crear el pull request: {str(e)}"
