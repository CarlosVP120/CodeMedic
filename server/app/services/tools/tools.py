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
        dirs_list = []
        
        while contents:
            file_content = contents.pop(0)
            if file_content.type == "dir":
                dirs_list.append(file_content.path)
                contents.extend(repo.get_contents(file_content.path))
            else:
                files_list.append(file_content.path)
        
        result = f"📁 Repository `{repository}` structure:\n\n"
        
        if dirs_list:
            result += "📂 Directories:\n"
            for dir_name in sorted(dirs_list):
                result += f"  - {dir_name}/\n"
            result += "\n"
        
        if files_list:
            result += "📄 Files:\n"
            for file_name in sorted(files_list):
                result += f"  - {file_name}\n"
        
        return result
        
    except Exception as e:
        return f"❌ Error retrieving repository structure: {str(e)}"

@tool
def get_repository_file_content(github_token: str, repository: str, file_name: str) -> str:
    """
    Retrieves the content of a specific file from the GitHub repository.
    """
    try:
        github_client = Github(github_token)
        repo = github_client.get_repo(repository)
        
        # Try to get the file content
        content = repo.get_contents(file_name)
        
        # Check if it's a file (not a directory)
        if content.type == "file":
            decoded_content = content.decoded_content.decode('utf-8')
            return f"📄 The file `{file_name}` contains:\n\n```\n{decoded_content}\n```"
        else:
            return f"❌ `{file_name}` is a directory, not a file. Use get_repository_file_names to list contents."
            
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
            return f"❌ File `{file_name}` not found in repository `{repository}`. Please check the file path and try again. Use get_repository_file_names to see available files."
        else:
            return f"❌ Error getting file content: {error_msg}"

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

    model_id = "TheCasvi/Qwen3-4B-CodeMedic-adapter"
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