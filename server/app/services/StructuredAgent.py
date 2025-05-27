from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from app.models.models import *
from app.models.agent_response import AgentResponse, AgentStepResponse
from github import Github
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
import json
from typing import Generator, Dict, Any

from app.services.tools.tools import *


class StructuredAgent:
    def __init__(self, github_credentials: GitHubCredentials):
        self.github_credentials = github_credentials
        self.parser = JsonOutputParser(pydantic_object=AgentResponse)
        
    def _setup_llm(self):
        """Setup the language model"""
        llm = HuggingFaceEndpoint(
            model="Qwen/Qwen3-4B",
            task="text-generation",
            max_new_tokens=2048,  # Increased token limit
            do_sample=False,
            repetition_penalty=1.03,
            temperature=0.1,  # Lower temperature for more consistent behavior
        )
        return ChatHuggingFace(llm=llm)

    def _create_tools_with_credentials(self):
        """Create tools with GitHub credentials pre-configured"""
        
        # Create partial functions with credentials already bound
        @tool
        def get_repo_files() -> list:
            """Get list of files in the repository"""
            return get_repository_file_names(
                self.github_credentials.token, 
                self.github_credentials.repository_name
            )
        
        @tool
        def get_file_content(file_name: str) -> str:
            """Get content of a specific file from the repository"""
            print(f"🔧 DEBUG: Getting file content for {file_name}")
            return get_repository_file_content(
                self.github_credentials.token,
                self.github_credentials.repository_name,
                file_name
            )
        
        @tool
        def create_file(file_path: str, content: str) -> str:
            """Create or modify a local file with given content"""
            return create_or_modify_file_for_issue(file_path, content)
        
        @tool
        def create_new_branch(base_branch: str, new_branch: str) -> str:
            """Create a new branch from the specified base branch"""
            return create_branch(
                self.github_credentials.token,
                self.github_credentials.repository_name,
                base_branch,
                new_branch
            )
        
        @tool
        def update_file(file_path: str, new_content: str, commit_message: str, branch: str) -> str:
            """Update a file in the specified GitHub branch"""
            return update_file_in_branch(
                self.github_credentials.token,
                self.github_credentials.repository_name,
                file_path,
                new_content,
                commit_message,
                branch
            )
        
        @tool
        def create_pr(title: str, body: str, head_branch: str, base_branch: str) -> str:
            """Create a pull request with the changes"""
            return create_pull_request(
                self.github_credentials.token,
                self.github_credentials.repository_name,
                title,
                body,
                head_branch,
                base_branch
            )
        
        return [
            get_repo_files,
            get_file_content,
            create_file,
            create_new_branch,
            update_file,
            create_pr
        ]

    def _create_structured_prompt(self, issue_data: GitHubIssue) -> str:
        """Create a prompt that includes format instructions for structured output"""
        
        format_instructions = self.parser.get_format_instructions()
        
        prompt_template = PromptTemplate(
            template="""You are CodeMedic, an AI assistant specialized in fixing GitHub issues.

Your task is to analyze the given issue and implement a solution following these steps:
1. Examine the repository structure and relevant files
2. Identify the root cause of the issue
3. Implement the necessary fixes
4. Create a pull request with the solution

## ISSUE TO FIX:
{issue_data}

## GITHUB CREDENTIALS:
Repository: {repository}
Token: Available for API calls

## TOOLS AVAILABLE:
- get_repo_files: Get list of files in repository
- get_file_content: Read content of specific files
- create_file: Create or modify files
- create_new_branch: Create a new branch for the fix
- update_file: Update files in a specific branch
- create_pr: Create a pull request with the changes

## OUTPUT FORMAT:
{format_instructions}

Please analyze the issue, implement the solution, and provide a structured response with all the details of what was accomplished.

IMPORTANT: 
- Always create a new branch for your changes
- Provide clear commit messages
- Include detailed information about what was fixed
- If you encounter any errors, include them in the errors field
- Set status to "success" only if everything completed successfully
""",
            input_variables=["issue_data", "repository", "format_instructions"],
            partial_variables={"format_instructions": format_instructions}
        )
        
        return prompt_template.format(
            issue_data=issue_data.model_dump_json(indent=2),
            repository=self.github_credentials.repository_name,
            format_instructions=format_instructions
        )

    def fix_github_issue(self, issue_data: GitHubIssue) -> Generator[Dict[str, Any], None, None]:
        """Fix a GitHub issue and return structured responses"""
        
        # Verify GitHub connection
        try:
            print("\n🔍 Verificando conexión con GitHub...")
            github_client = Github(self.github_credentials.token)
            user = github_client.get_user()
            print(f"✓ Conectado como: {user.login}")
            
        except Exception as e:
            error_response = AgentResponse(
                summary=f"Failed to connect to GitHub: {str(e)}",
                status="error",
                errors=[f"GitHub connection error: {str(e)}"]
            )
            yield {
                "type": "final_response",
                "data": error_response.model_dump()
            }
            return

        # Setup tools with credentials pre-configured
        tools = self._create_tools_with_credentials()
        
        model = self._setup_llm()
        checkpointer = MemorySaver() 
        
        # Create the agent
        graph = create_react_agent(
            model=model,
            tools=tools,
            checkpointer=checkpointer
        )
        
        # Create structured prompt
        structured_prompt = self._create_structured_prompt(issue_data)
        
        # Prepare messages
        initial_messages = [
            SystemMessage(content="""You are CodeMedic, an AI assistant that fixes GitHub issues. You MUST follow this exact process:

STEP 1: Use get_repo_files() to understand repository structure
STEP 2: Use get_file_content() to read relevant files
STEP 3: Use create_new_branch() to create a new branch (use format: fix-issue-{issue_number})
STEP 4: Use update_file() to modify files on the new branch
STEP 5: Use create_pr() to create a pull request

YOU MUST COMPLETE ALL 5 STEPS. The process is not complete without creating a pull request.

Example workflow:
1. create_new_branch("main", "fix-issue-123")
2. update_file("path/to/file.py", "fixed content", "Fix issue #123", "fix-issue-123")  
3. create_pr("Fix issue #123", "Description of fix", "fix-issue-123", "main")

IMPORTANT: Always create the pull request as the final step. If you don't create a PR, the fix is incomplete.
"""),
            HumanMessage(content=structured_prompt)
        ]

        inputs = {"messages": initial_messages}
        config = {"configurable": {"thread_id": f"thread-issue-{issue_data.number}"}}

        # Track the conversation to extract final response
        conversation_history = []
        
        try:
            # Stream the agent execution
            for event in graph.stream(inputs, config=config):
                conversation_history.append(event)
                print(f"Event: {event}")
                
                # Enhanced debugging - look for tool calls
                if 'tools' in event and 'messages' in event['tools']:
                    for message in event['tools']['messages']:
                        if hasattr(message, 'content'):
                            content = str(message.content)
                            print(f"🔧 TOOL RESULT: {content[:200]}...")
                            
                            # Specifically look for pull request creation
                            if 'github.com' in content and 'pull' in content:
                                print(f"🎉 PULL REQUEST DETECTED: {content}")
                
                # Look for agent thinking/reasoning
                if 'agent' in event and 'messages' in event['agent']:
                    for message in event['agent']['messages']:
                        if hasattr(message, 'content'):
                            content = str(message.content)
                            if 'create_pr' in content:
                                print(f"🤖 AGENT CALLING create_pr: {content[:200]}...")
            
            # Extract and parse the final response
            final_response = self._extract_final_response(conversation_history, issue_data)
            
            yield {
                "type": "final_response",
                "data": final_response.model_dump()
            }
            
        except Exception as e:
            print(f"Error during agent execution: {str(e)}")
            error_response = AgentResponse(
                summary=f"Error during execution: {str(e)}",
                status="error",
                errors=[str(e)]
            )
            yield {
                "type": "final_response",
                "data": error_response.model_dump()
            }

    def _extract_final_response(self, conversation_history: list, issue_data: GitHubIssue) -> AgentResponse:
        """Extract and parse the final structured response from conversation history"""
        
        # Look for JSON responses in the conversation
        for event in reversed(conversation_history):
            if 'agent' in event and 'messages' in event['agent']:
                for message in event['agent']['messages']:
                    if hasattr(message, 'content'):
                        content = str(message.content)
                        
                        # Try to parse as JSON
                        try:
                            # Look for JSON in the content
                            json_start = content.find('{')
                            json_end = content.rfind('}') + 1
                            
                            if json_start != -1 and json_end > json_start:
                                json_content = content[json_start:json_end]
                                parsed_data = json.loads(json_content)
                                
                                # Validate and create AgentResponse
                                return AgentResponse(**parsed_data)
                                
                        except (json.JSONDecodeError, ValueError, TypeError):
                            continue
        
        # If no structured response found, create a fallback response
        return self._create_fallback_response(conversation_history, issue_data)
    
    def _create_fallback_response(self, conversation_history: list, issue_data: GitHubIssue) -> AgentResponse:
        """Create a fallback response when structured parsing fails"""
        
        # Extract information from conversation history
        summary = f"Processed issue #{issue_data.number}: {issue_data.title}"
        files_modified = []
        errors = []
        has_pr = False
        branch_name = None
        
        # Analyze conversation for key information
        pull_request_url = None
        
        for event in conversation_history:
            if 'tools' in event and 'messages' in event['tools']:
                for message in event['tools']['messages']:
                    if hasattr(message, 'content'):
                        content = str(message.content)
                        
                        # Look for file modifications
                        if 'updated on branch' in content.lower() or 'created' in content.lower():
                            # Extract file names (basic pattern matching)
                            import re
                            file_matches = re.findall(r"'([^']+\.[^']+)'", content)
                            files_modified.extend(file_matches)
                        
                        # Look for pull request creation - check for GitHub URLs
                        if 'github.com' in content and 'pull' in content:
                            has_pr = True
                            # Extract PR URL
                            url_match = re.search(r'https://github\.com/[^/]+/[^/]+/pull/\d+', content)
                            if url_match:
                                pull_request_url = url_match.group(0)
                        
                        # Look for pull request creation messages
                        if ('pull request creado' in content.lower() or 
                            'pull request created' in content.lower()):
                            has_pr = True
                        
                        # Look for branch creation
                        if 'branch' in content.lower() and ('created' in content.lower() or 'creado' in content.lower()):
                            branch_matches = re.findall(r"'([^']+)'.*created", content, re.IGNORECASE)
                            if branch_matches:
                                branch_name = branch_matches[0]
                        
                        # Look for errors
                        if ('error' in content.lower() or 'failed' in content.lower() or 
                            '❌' in content):
                            errors.append(content[:200])
        
        # Determine status
        status = "error" if errors else ("success" if has_pr else "partial")
        
        # Create better summary based on what was accomplished
        if has_pr:
            summary = f"Successfully fixed issue #{issue_data.number} and created pull request"
            solution = f"Created pull request with fixes for '{issue_data.title}'. The issue has been resolved."
        elif branch_name:
            summary = f"Partially fixed issue #{issue_data.number} - branch created but no pull request"
            solution = f"Created branch '{branch_name}' with fixes, but pull request creation failed."
        else:
            summary = f"Attempted to fix issue #{issue_data.number} but process incomplete"
            solution = "Issue analysis completed but fixes were not successfully applied."
        
        return AgentResponse(
            summary=summary,
            solution=solution,
            files_modified=list(set(files_modified)) if files_modified else None,
            pull_request_url=pull_request_url,
            branch_name=branch_name,
            errors=errors if errors else None,
            status=status
        ) 