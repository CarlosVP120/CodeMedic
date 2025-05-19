from github import Github
from models.models import *
from github.GithubException import GithubException


def get_github_issues(github_repository_data:GithubRepositoryData) -> List[GitHubIssue]:
    """Obtiene los issues abiertos del repositorio."""
    try:
        print(f"\n🔍 Intentando acceder al repositorio: {github_repository_data.repository}")
        github_client = Github(github_repository_data.github_token)
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
        print("Exception in get_github_issues")
        print(f"\n❌ Error al obtener issues: {str(e)}")
        print(f"Repositorio: {github_repository_data.repository}")
        print(f"Token válido: {'Sí' if github_repository_data.github_token else 'No'}")
        print("\nDetalles del error:")
        print(f"- Tipo de error: {type(e).__name__}")
        print(f"- Mensaje: {str(e)}")
        return []

def get_github_issue(issues:List[GitHubIssue],issue_number:int)-> GitHubIssue | None:
    for issue in issues:
        if issue.number == issue_number:
            return issue
    return None

def get_repository_file_names(github_token: str, repository: str) -> List[str]:
    """
    Returns the list of file names from the root of the given GitHub repository.
    """
    try:
        print(f"\n🔍 Intentando acceder al repositorio: {repository}")
        github_client = Github(github_token)
        repo = github_client.get_repo(repository)
        print("✓ Repositorio encontrado")
    except Exception as e:
        print(f"❌ Error al obtener issues: {str(e)}")
        return []

    contents = repo.get_contents("")
    files_list = []
    while contents:
        file_content = contents.pop(0)
        if file_content.type == "dir":
            contents.extend(repo.get_contents(file_content.path))
        else:
            files_list.append(file_content.name)
            print("File name: ", file_content.name)
    return files_list



def get_repository_file_content(github_token: str, repository: str, file_name: str) -> str:
    """
    Retrieves the content of a specific file from the GitHub repository.
    """
    try:
        print(f"\n🔍 Intentando acceder al repositorio: {repository}")
        github_client = Github(github_token)
        repo = github_client.get_repo(repository)
        print("✓ Repositorio encontrado")
    except Exception as e:
        return f"❌ Error al conectar con el repositorio: {str(e)}"

    try:
        print("Trying to retrieve file content")
        content = repo.get_contents(file_name)
        print("content file: ", content)
        return content.decoded_content.decode()
    except Exception as e:
        return f"Error al obtener el contenido del archivo: {str(e)}"


def create_or_modify_file_for_issue(file_path: str, content: str) -> str:
    """
    Creates or overwrites a local file with the given content.
    """
    try:
        print("📄 inside create_or_modify_file_for_issue")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"✅ Archivo local creado/actualizado en: {file_path}"
    except Exception as e:
        return f"❌ Error al crear el archivo local: {str(e)}"


def create_branch(
        github_token: str,
        repository: str,
        base_branch: str,
        new_branch: str
) -> str:
    """
    Creates a new branch from the specified base branch.

    Args:
        github_token: GitHub access token.
        repository: Repository name in 'owner/repo' format.
        base_branch: The branch to branch off from (e.g., 'main').
        new_branch: The name of the new branch to create.

    Returns:
        The name of the created branch or an error message.
    """
    try:
        print(f"🌿 Creating branch '{new_branch}' from '{base_branch}' in repo '{repository}'")

        github_client = Github(github_token)
        repo = github_client.get_repo(repository)

        # Get the commit SHA of the base branch
        base_ref = repo.get_git_ref(f"heads/{base_branch}")
        base_sha = base_ref.object.sha

        # Create new branch ref
        new_ref = f"refs/heads/{new_branch}"
        repo.create_git_ref(ref=new_ref, sha=base_sha)

        print(f"✅ Branch '{new_branch}' created")
        return f"Branch '{new_branch}' created successfully"

    except GithubException as e:
        if e.status == 422:
            return f"⚠️ Branch '{new_branch}' already exists."
        else:
            print(f"❌ GitHub Exception: {e.data}")
            return f"❌ GitHub error: {e.data.get('message', str(e))}"
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return f"❌ Error: {str(e)}"


def update_file_in_branch(
    github_token: str,
    repository: str,
    file_path: str,
    new_content: str,
    commit_message: str,
    branch: str
) -> str:
    """
    Updates a file in the specified GitHub branch.

    Args:
        github_token: GitHub token for authentication.
        repository: Repo name in 'owner/repo' format.
        file_path: Path to the file to update.
        new_content: New content for the file (as a string).
        commit_message: Commit message for the change.
        branch: Branch name to commit to.

    Returns:
        Status message indicating success or error.
    """
    try:
        github_client = Github(github_token)
        repo = github_client.get_repo(repository)

        # Get the current file SHA (required to update the file)
        contents = repo.get_contents(file_path, ref=branch)
        current_sha = contents.sha

        # Commit the updated content
        repo.update_file(
            path=file_path,
            message=commit_message,
            content=new_content,
            sha=current_sha,
            branch=branch
        )

        return f"✅ File '{file_path}' updated on branch '{branch}'"
    except Exception as e:
        print(f"❌ Error updating file: {str(e)}")
        return f"❌ Error: {str(e)}"

def create_pull_request(
    github_token: str,
    repository: str,
    title: str,
    body: str,
    head_branch: str,
    base_branch: str
) -> Any:
    """
    Creates a pull request with the given data.
    """
    try:
        print("📦 inside create_pull_request")
        print(repository)
        print(title)
        print(body)
        print(head_branch)
        print(base_branch)


        github_client = Github(github_token)
        repo = github_client.get_repo(repository)
        pull_request = repo.create_pull(
            title=title,
            body=body,
            head=head_branch,
            base=base_branch
        )
        print(f"✅ Pull request creado: {pull_request.html_url}")
        return pull_request.html_url
    except Exception as e:
        print(f"❌ Error al crear el pull request: {str(e)}")
        return str(e)
