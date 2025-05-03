import * as vscode from "vscode";
import { simpleGit, SimpleGit } from "simple-git";
import * as path from "path";

export class SolutionService {
  private git: SimpleGit;

  constructor() {
    // Initialize git once we know we have a workspace folder
    if (
      vscode.workspace.workspaceFolders &&
      vscode.workspace.workspaceFolders.length > 0
    ) {
      this.git = simpleGit(vscode.workspace.workspaceFolders[0].uri.fsPath);
    } else {
      // We'll initialize later when needed
      this.git = simpleGit();
    }
  }

  /**
   * Shows how to solve an issue by generating a step-by-step guide
   */
  public async showSolution(issue: any): Promise<void> {
    // In a real implementation, this would use an LLM to generate a detailed solution
    const solutionPanel = vscode.window.createWebviewPanel(
      "issueSolution",
      `Solution for #${issue.number}: ${issue.title}`,
      vscode.ViewColumn.One,
      {
        enableScripts: true,
      }
    );

    // For now, we'll generate a simple markdown solution
    const solution = `
    # Solution Guide for Issue #${issue.number}

    ## Issue Description
    ${issue.body || "No description provided"}

    ## Proposed Solution
    Here's a step-by-step guide on how to solve this issue:

    1. **Analyze the issue**: Understand what needs to be fixed.
    2. **Locate the relevant code**: Find files related to this issue.
    3. **Make changes**: Implement the required fix.
    4. **Test your solution**: Ensure the issue is resolved.
    5. **Commit and create a PR**: Push your changes to GitHub.

    ## Helpful Resources
    * [GitHub Documentation](https://docs.github.com)
    * [VS Code Documentation](https://code.visualstudio.com/docs)
    `;

    solutionPanel.webview.html = this.getWebviewContent(issue, solution);
  }

  /**
   * Automatically solves an issue by generating and applying a patch
   */
  public async solveIssue(issue: any): Promise<void> {
    // In a real implementation, this would:
    // 1. Use an LLM to analyze the issue and generate a patch
    // 2. Apply the patch to the codebase
    // 3. Create a commit and propose a PR

    // For now, we'll just show a dialog saying this would be automated
    const branchName = `fix-issue-${issue.number}`;

    try {
      // Create a new branch for the fix
      await this.git.checkoutLocalBranch(branchName);

      // Show a message indicating what would happen in a real implementation
      const result = await vscode.window.showInformationMessage(
        `In a production version, CodeMedic would:
        
        1. Analyze issue #${issue.number}
        2. Generate and apply a fix 
        3. Create a commit on branch ${branchName}
        4. Open a PR for you to review`,
        "Simulate Success",
        "Return to Main Branch"
      );

      if (result === "Return to Main Branch") {
        // Check out the previous branch
        await this.git.checkout("-");
      } else if (result === "Simulate Success") {
        // Simulate a successful PR creation
        vscode.window.showInformationMessage(
          `PR created successfully for issue #${issue.number}`,
          "View PR"
        );
      }
    } catch (error) {
      vscode.window.showErrorMessage(
        `Error solving issue: ${(error as Error).message}`
      );

      // Try to return to the previous branch
      try {
        await this.git.checkout("-");
      } catch (e) {
        // Ignore errors when trying to recover
      }
    }
  }

  /**
   * Generates the HTML content for the solution webview
   */
  private getWebviewContent(issue: any, solutionMarkdown: string): string {
    return `
      <!DOCTYPE html>
      <html lang="en">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Solution for Issue #${issue.number}</title>
        <style>
          body {
            font-family: var(--vscode-font-family);
            padding: 20px;
            color: var(--vscode-foreground);
          }
          h1 { 
            color: var(--vscode-editor-foreground);
            border-bottom: 1px solid var(--vscode-panel-border);
            padding-bottom: 10px;
          }
          h2 { 
            color: var(--vscode-editor-foreground);
            margin-top: 20px;
          }
          pre {
            background-color: var(--vscode-editor-background);
            padding: 10px;
            border-radius: 5px;
            overflow-x: auto;
          }
          ul {
            padding-left: 20px;
          }
          li {
            margin-bottom: 8px;
          }
        </style>
      </head>
      <body>
        <div id="content">
          ${this.markdownToHtml(solutionMarkdown)}
        </div>
        <script>
          // Script for interactivity could be added here
        </script>
      </body>
      </html>
    `;
  }

  /**
   * Very simple markdown to HTML converter
   */
  private markdownToHtml(markdown: string): string {
    return (
      markdown
        // Headers
        .replace(/^# (.*$)/gm, "<h1>$1</h1>")
        .replace(/^## (.*$)/gm, "<h2>$1</h2>")
        .replace(/^### (.*$)/gm, "<h3>$1</h3>")
        // Bold
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        // Italic
        .replace(/\*(.*?)\*/g, "<em>$1</em>")
        // Lists
        .replace(/^\d+\. (.*$)/gm, "<li>$1</li>")
        .replace(/^- (.*$)/gm, "<li>$1</li>")
        // Links
        .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2">$1</a>')
        // Line breaks
        .replace(/\n/g, "<br>")
        // Fix lists
        .replace(/<br><li>/g, "<li>")
        .replace(/<li>(.*?)<\/li>/g, function (match) {
          if (match.indexOf("<li>1. ") === 0) {
            return "<ol>" + match + "</ol>";
          } else {
            return "<ul>" + match + "</ul>";
          }
        })
    );
  }
}
