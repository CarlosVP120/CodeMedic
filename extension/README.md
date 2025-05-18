# CodeMedic

A VS Code extension designed to assist developers in managing and resolving GitHub issues directly within their development environment. CodeMedic streamlines the issue-handling process by integrating with GitHub repositories, allowing developers to either receive a guided solution or apply an automated fix.

## Features

### Automatic Repository Verification

- Detects if the workspace contains a GitHub-connected Git repository
- Provides clear feedback if GitHub integration is not available

### GitHub Issue Management

- Authenticate with GitHub using personal access tokens
- View all open issues from the current repository in a dedicated side panel
- Display issue details including title, creation date, and labels

### Action Selector

When you select an issue, you can choose from two options:

1. **Show me how to solve it** - Displays a detailed action plan to help you solve the issue yourself
2. **Solve it for me** - Simulates generating a commit with the patch and proposing a Pull Request

## Getting Started

1. Open a project with a GitHub remote repository
2. Click on the CodeMedic icon in the activity bar
3. Authenticate with GitHub when prompted
4. View and manage your repository's issues directly in VS Code

## Requirements

- VS Code 1.99.0 or higher
- A GitHub account and repository with issues
- Git installed on your system

## Extension Settings

- `codemedic.authenticate`: Authenticate with GitHub using a personal access token

## Future Development

In future versions, CodeMedic will:

- Integrate an LLM to analyze issues more deeply
- Generate intelligent solutions based on issue context
- Create automatic patches using AI-assisted code generation
- Support additional issue providers beyond GitHub

## Release Notes

### 0.0.1

Initial release of CodeMedic with basic GitHub issue management capabilities.

## Known Issues

Calling out known issues can help limit users opening duplicate issues against your extension.

## Following extension guidelines

Ensure that you've read through the extensions guidelines and follow the best practices for creating your extension.

- [Extension Guidelines](https://code.visualstudio.com/api/references/extension-guidelines)

## Working with Markdown

You can author your README using Visual Studio Code. Here are some useful editor keyboard shortcuts:

- Split the editor (`Cmd+\` on macOS or `Ctrl+\` on Windows and Linux).
- Toggle preview (`Shift+Cmd+V` on macOS or `Shift+Ctrl+V` on Windows and Linux).
- Press `Ctrl+Space` (Windows, Linux, macOS) to see a list of Markdown snippets.

## For more information

- [Visual Studio Code's Markdown Support](http://code.visualstudio.com/docs/languages/markdown)
- [Markdown Syntax Reference](https://help.github.com/articles/markdown-basics/)

**Enjoy!**
