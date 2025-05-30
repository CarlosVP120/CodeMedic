from dotenv import load_dotenv
import os
from github import Github
from github.GithubException import GithubException
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_huggingface import ChatHuggingFace, HuggingFacePipeline


@tool
def get_repository_file_names(github_token: str, repository: str) -> str:
    """
    Returns the list of file names from the root of the given GitHub repository.
    """
    try:
        github_client = Github(github_token)
        repo = github_client.get_repo(repository)
        contents = repo.get_contents("")
        files_list = []
        while contents:
            file_content = contents.pop(0)
            if file_content.type == "dir":
                contents.extend(repo.get_contents(file_content.path))
            else:
                files_list.append(file_content.name)
        return f"📄 Repository contains the following files: {', '.join(files_list)}"
    except Exception as e:
        return f"❌ Error retrieving files: {str(e)}"

@tool
def get_repository_file_content(github_token: str, repository: str, file_name: str) -> str:
    """
    Retrieves the content of a specific file from the GitHub repository.
    """
    try:
        github_client = Github(github_token)
        repo = github_client.get_repo(repository)
        content = repo.get_contents(file_name)
        return f"📄 The file `{file_name}` contains:\n\n```python\n{content.decoded_content.decode()}\n```"
    except Exception as e:
        return f"❌ Error getting file content: {str(e)}"

@tool
def create_branch(github_token: str, repository: str, base_branch: str, new_branch: str) -> str:
    """
    Creates a new branch from the specified base branch.
    """
    try:
        github_client = Github(github_token)
        repo = github_client.get_repo(repository)
        base_ref = repo.get_git_ref(f"heads/{base_branch}")
        base_sha = base_ref.object.sha
        new_ref = f"refs/heads/{new_branch}"
        repo.create_git_ref(ref=new_ref, sha=base_sha)
        return f"✅ Branch `{new_branch}` created from `{base_branch}` in `{repository}`"
    except GithubException as e:
        if e.status == 422:
            return f"⚠️ Branch `{new_branch}` already exists."
        return f"❌ GitHub error: {e.data.get('message', str(e))}"
    except Exception as e:
        return f"❌ Error creating branch: {str(e)}"

@tool
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
    """
    try:
        github_client = Github(github_token)
        repo = github_client.get_repo(repository)
        contents = repo.get_contents(file_path, ref=branch)
        current_sha = contents.sha

        repo.update_file(
            path=file_path,
            message=commit_message,
            content=new_content,
            sha=current_sha,
            branch=branch
        )
        return f"✅ File `{file_path}` updated on branch `{branch}` with commit message: '{commit_message}'"
    except Exception as e:
        return f"❌ Error updating file: {str(e)}"

@tool
def create_pull_request(
        github_token: str,
        repository: str,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str
) -> str:
    """
    Creates a pull request with the given data.
    """
    try:
        github_client = Github(github_token)
        repo = github_client.get_repo(repository)
        pull_request = repo.create_pull(
            title=title,
            body=body,
            head=head_branch,
            base=base_branch
        )
        return f"✅ Pull request created: {pull_request.html_url}"
    except Exception as e:
        return f"❌ Error creating pull request: {str(e)}"

@tool
def fix_code_issues(buggy_code: str) -> dict:
    """
        Analyzes the given Python code for syntax or logical errors and returns a corrected version.

        This tool uses a fine-tuned language model to automatically fix issues in the provided code snippet.
        It returns the result as a JSON dictionary in the format: { "fixed_code": "..." }.

        Args:
            buggy_code (str): A Python code snippet that contains one or more errors.

        Returns:
            dict: A dictionary containing the corrected version of the code. If the model fails to produce valid JSON,
                  an error message is included in the output.
        """
    load_dotenv(dotenv_path=".env")
    endpoint_gpt4 = os.getenv("AZURE_OPENAI_ENDPOINT_GPT4")
    # llm_test = AzureChatOpenAI(
    #     azure_endpoint=endpoint_gpt4,
    #     azure_deployment="gpt-4o",
    #     api_version="2025-01-01-preview",
    #     temperature=0,
    #     max_tokens=1000,
    #     timeout=None,
    #     max_retries=2,
    # )
    print("Generating code...")

    model_id = "TheCasvi/Qwen3-1.7B-35KD-adapter"
    llm = HuggingFacePipeline.from_model_id(
        model_id=model_id,
        task="text-generation",
        pipeline_kwargs={
            "max_new_tokens": 1000,
            "do_sample": False,
            "repetition_penalty": 1.03,
        }
    )
    chat_model = ChatHuggingFace(llm=llm, model_id=model_id)
    messages = [
        SystemMessage(content="You're a helpful code assistant"),
        HumanMessage(
            content=f"""
               Fix the following buggy Python code. Respond only with JSON using this format:
               {{ "fixed_code": "..." }}

               Code:
               {buggy_code}
            """
        ),
    ]
    print("prompt: ", messages)
    result = chat_model.invoke(messages)
    print("fine_tuned mode result: ", result)
    return result