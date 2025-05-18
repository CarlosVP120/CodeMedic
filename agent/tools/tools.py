from typing import List, Any
from models.GitHubIssueModel import GitHubIssue
from models.GithubRepositoryDataModel import GithubRepositoryData


def get_github_issues(github_repository_data:GithubRepositoryData) -> List[GitHubIssue]:
    """Obtiene los issues abiertos del repositorio."""
    try:
        print(f"\n🔍 Intentando acceder al repositorio: {github_repository_data.repository}")
        github_client=github_repository_data.client
        repo = github_client.get_repo(github_repository_data.repository)
        print("✓ Repositorio encontrado")

        print("\n📋 Obteniendo issues abiertos...")
        issues = repo.get_issues(state='open')
        issues_list = []

        for issue in issues:
            print(f"  - Issue #{issue.number}: {issue.title}")
            issues_list.append(GitHubIssue(
                number=issue.number,
                title=issue.title,
                body=issue.body or "",
                state=issue.state,
                created_at=issue.created_at,
                updated_at=issue.updated_at
            ))

        if not issues_list:
            print("⚠️ No se encontraron issues abiertos")
        else:
            print(f"✓ Se encontraron {len(issues_list)} issues abiertos")

        return issues_list
    except Exception as e:
        print(f"\n❌ Error al obtener issues: {str(e)}")
        print(f"Repositorio: {github_repository_data.repository}")
        print(f"Token válido: {'Sí' if github_repository_data.token else 'No'}")
        print("\nDetalles del error:")
        print(f"- Tipo de error: {type(e).__name__}")
        print(f"- Mensaje: {str(e)}")
        return []

def get_github_issue(issues:List[GitHubIssue],issue_number:int)-> GitHubIssue | None:
    for issue in issues:
        if issue.number == issue_number:
            return issue
    return None

def get_repository_file_names(github_repository_data:GithubRepositoryData)->List[str]:
    """
       Returns the list of file names from the root of the given GitHub repository.

       Args:
           github_repository_data: Object containing the GitHub client and repository name.

       Returns:
           A list of file names found in the repository.
       """
    try:
        print(f"\n🔍 Intentando acceder al repositorio: {github_repository_data.repository}")
        github_client=github_repository_data.client
        repo = github_client.get_repo(github_repository_data.repository)
        print("✓ Repositorio encontrado")

    except Exception as e:
        print(f"\n❌ Error al obtener issues: {str(e)}")
        print(f"Repositorio: {github_repository_data.repository}")
        print(f"Token válido: {'Sí' if github_repository_data.token else 'No'}")
        print("\nDetalles del error:")
        print(f"- Tipo de error: {type(e).__name__}")
        print(f"- Mensaje: {str(e)}")
        return []

    contents = repo.get_contents("")
    files_list = []
    while contents:
        file_content = contents.pop(0)
        if file_content.type == "dir":
            contents.extend(repo.get_contents(file_content.path))
        else:
            files_list.append(file_content.name)
            print("File name: ",file_content.name)
    return files_list

def get_repository_file_content(github_repository_data:GithubRepositoryData,file_name:str)-> str:
    """
       Retrieves the content of a specific file from the GitHub repository.

       Args:
           github_repository_data: Object containing the GitHub client and repository name.
           file_name: Name of the file to fetch from the repository.

       Returns:
           The decoded content of the file as a string.
       """
    try:
        print(f"\n🔍 Intentando acceder al repositorio: {github_repository_data.repository}")
        github_client = github_repository_data.client
        repo = github_client.get_repo(github_repository_data.repository)
        print("✓ Repositorio encontrado")

    except Exception as e:
        print(f"\n❌ Error al obtener issues: {str(e)}")
        print(f"Repositorio: {github_repository_data.repository}")
        print(f"Token válido: {'Sí' if github_repository_data.token else 'No'}")
        print("\nDetalles del error:")
        print(f"- Tipo de error: {type(e).__name__}")
        print(f"- Mensaje: {str(e)}")
        return []

    try:
        content = repo.get_contents(file_name)
        return content.decoded_content.decode()
    except Exception as e:
        return f"Error al obtener el contenido del archivo: {str(e)}"


def create_local_file(file_path: str, content: str) -> str:
    """
    Creates or overwrites a local file with the given content.
    Args:
        file_path: Ruta local donde se creará el archivo.
        content: Contenido que se escribirá en el archivo.
    Returns:
        str: Success message or error.
    """
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Archivo local creado/actualizado exitosamente en: {file_path}"
    except Exception as e:
        return f"Error al crear el archivo local: {str(e)}"