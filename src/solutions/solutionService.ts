import * as vscode from "vscode";
import { simpleGit, SimpleGit } from "simple-git";
import * as path from "path";
import { IntelligentSearchService } from "./intelligentSearchService";
import { AIService } from "./aiService";
import { CodeFixPanel } from "./codeFixPanel";

export class SolutionService {
  private git: SimpleGit;
  private intelligentSearchService: IntelligentSearchService;
  private aiService: AIService;

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

    this.intelligentSearchService = new IntelligentSearchService();
    this.aiService = new AIService();
  }

  /**
   * Shows how to solve an issue by generating a step-by-step guide
   */
  public async showSolution(issue: any): Promise<vscode.WebviewPanel> {
    // Buscar archivos relevantes utilizando IA
    const relevantFiles = await this.intelligentSearchService.findRelevantFiles(
      issue
    );

    // Create the solution panel
    const solutionPanel = vscode.window.createWebviewPanel(
      "issueSolution",
      `Solution for #${issue.number}: ${issue.title}`,
      vscode.ViewColumn.Beside,
      {
        enableScripts: true,
      }
    );

    // Show loading message
    solutionPanel.webview.html = this.getLoadingContent(issue);

    // Generate AI-powered solution in the background
    this.generateAISolution(issue, relevantFiles).then((solution) => {
      if (solutionPanel.visible) {
        solutionPanel.webview.html = this.getWebviewContent(
          issue,
          solution,
          relevantFiles
        );
      }
    });

    // Configurar el manejo de mensajes para abrir archivos relacionados
    this.setupWebviewMessageHandling(solutionPanel, relevantFiles);

    return solutionPanel;
  }

  /**
   * Generates an AI-powered solution
   */
  private async generateAISolution(
    issue: any,
    relevantFiles: string[]
  ): Promise<string> {
    // Check if AI service is available
    if (!(await this.aiService.isConfigured())) {
      return `
      # Solution Guide for Issue #${issue.number}

      ## Issue Description
      ${issue.body || "No description provided"}

      ## AI Analysis
      To get AI-powered analysis, please configure your OpenAI API key in settings.

      ## Files Relacionados
      ${this.generateFileList(relevantFiles)}

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
    }

    try {
      // Generate solution using AI
      vscode.window.setStatusBarMessage("Generating AI solution...", 30000);

      const aiSolution = await this.aiService.analyzeSolution(
        issue,
        relevantFiles
      );

      vscode.window.setStatusBarMessage("AI solution generated", 3000);

      return aiSolution;
    } catch (error) {
      console.error("Error generating AI solution:", error);
      vscode.window.showErrorMessage(
        `Error generating AI solution: ${(error as Error).message}`
      );

      // Fall back to default solution
      return `
      # Solution Guide for Issue #${issue.number}

      ## Issue Description
      ${issue.body || "No description provided"}

      ## Files Relacionados
      ${this.generateFileList(relevantFiles)}

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
    }
  }

  /**
   * Gets HTML for loading screen
   */
  private getLoadingContent(issue: any): string {
    return `
      <!DOCTYPE html>
      <html lang="en">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline';">
        <title>Solution for Issue #${issue.number}</title>
        <style>
          :root {
            --container-padding: 20px;
            --input-padding-vertical: 6px;
            --input-padding-horizontal: 4px;
            --input-margin-vertical: 4px;
            --input-margin-horizontal: 0;
          }

          body {
            padding: 0 var(--container-padding);
            color: var(--vscode-foreground);
            font-size: var(--vscode-font-size);
            font-weight: var(--vscode-font-weight);
            font-family: var(--vscode-font-family);
            background-color: var(--vscode-editor-background);
          }
          
          h1 { 
            color: var(--vscode-editor-foreground);
            border-bottom: 1px solid var(--vscode-panel-border);
            padding-bottom: 10px;
          }
          
          .loading {
            margin-top: 30px;
            text-align: center;
          }
          
          .loading-text {
            margin-top: 20px;
            font-size: 16px;
            color: var(--vscode-foreground);
          }
          
          .spinner {
            display: inline-block;
            width: 50px;
            height: 50px;
            border: 5px solid rgba(120, 120, 120, 0.2);
            border-radius: 50%;
            border-top-color: var(--vscode-button-background);
            animation: spin 1s ease-in-out infinite;
          }
          
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
        </style>
      </head>
      <body>
        <h1>Analyzing Issue #${issue.number}</h1>
        <div class="loading">
          <div class="spinner"></div>
          <div class="loading-text">Generating AI-powered solution...</div>
        </div>
      </body>
      </html>
    `;
  }

  /**
   * Configura el manejo de mensajes para abrir archivos desde el webview
   */
  private setupWebviewMessageHandling(
    panel: vscode.WebviewPanel,
    files: string[]
  ): void {
    panel.webview.onDidReceiveMessage(async (message) => {
      if (message.command === "openFile" && message.filePath) {
        try {
          // Obtener la carpeta de trabajo
          const workspaceFolders = vscode.workspace.workspaceFolders;
          if (!workspaceFolders || workspaceFolders.length === 0) {
            throw new Error("No hay carpeta de trabajo abierta");
          }

          // Construir la ruta completa del archivo
          const fileUri = vscode.Uri.file(
            path.join(workspaceFolders[0].uri.fsPath, message.filePath)
          );

          // Abrir el archivo en el editor
          const document = await vscode.workspace.openTextDocument(fileUri);
          await vscode.window.showTextDocument(document);
        } catch (error) {
          vscode.window.showErrorMessage(
            `No se pudo abrir el archivo: ${message.filePath}`
          );
        }
      } else if (message.command === "generateFixes" && message.issue) {
        // Generate fixes for the issue
        this.generateCodeFixes(message.issue);
      }
    });
  }

  /**
   * Generates code fixes for an issue
   */
  private async generateCodeFixes(issue: any): Promise<void> {
    try {
      // Show progress indicator
      vscode.window.withProgress(
        {
          location: vscode.ProgressLocation.Notification,
          title: `Generating code fixes for issue #${issue.number}`,
          cancellable: false,
        },
        async (progress) => {
          // Find relevant files
          progress.report({ message: "Finding relevant files..." });
          const relevantFiles =
            await this.intelligentSearchService.findRelevantFiles(issue);

          if (relevantFiles.length === 0) {
            vscode.window.showWarningMessage(
              "No relevant files found for this issue."
            );
            return;
          }

          // Generate fixes
          progress.report({
            message: `Analyzing ${relevantFiles.length} files...`,
          });
          const codeFixes = await this.aiService.generateCodeFixes(
            issue,
            relevantFiles
          );

          if (codeFixes.length === 0) {
            vscode.window.showWarningMessage(
              "Could not generate any code fixes for this issue."
            );
            return;
          }

          // Show the code fix panel
          CodeFixPanel.show(issue, codeFixes);
        }
      );
    } catch (error) {
      vscode.window.showErrorMessage(
        `Error generating code fixes: ${(error as Error).message}`
      );
    }
  }

  /**
   * Genera HTML con la lista de archivos relevantes
   */
  private generateFileList(files: string[]): string {
    if (files.length === 0) {
      return "No se encontraron archivos relacionados.";
    }

    return `
    Los siguientes archivos pueden estar relacionados con este issue:

    ${files.map((file) => `* ${file}`).join("\n    ")}
    `;
  }

  /**
   * Automatically solves an issue by generating and applying a patch
   */
  public async solveIssue(issue: any): Promise<void> {
    // Buscar archivos relevantes utilizando IA
    const relevantFiles = await this.intelligentSearchService.findRelevantFiles(
      issue
    );

    // Create a branch for the fix
    const branchName = `fix-issue-${issue.number}`;

    try {
      // Create a new branch for the fix
      await this.git.checkoutLocalBranch(branchName);

      // Show the code fix panel with AI-generated fixes
      await this.generateCodeFixes(issue);

      // Show a message indicating the branch was created
      vscode.window.showInformationMessage(
        `Created branch '${branchName}' for fixing issue #${issue.number}. Review and apply the generated code fixes.`
      );
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
  private getWebviewContent(
    issue: any,
    solutionMarkdown: string,
    relevantFiles: string[]
  ): string {
    // Crear funciones para el navegador web
    const webviewFunctions = `
      function openFile(filePath) {
        const vscode = acquireVsCodeApi();
        vscode.postMessage({
          command: 'openFile',
          filePath: filePath
        });
      }
      
      function generateFixes() {
        const vscode = acquireVsCodeApi();
        vscode.postMessage({
          command: 'generateFixes',
          issue: ${JSON.stringify(issue)}
        });
      }
    `;

    return `
      <!DOCTYPE html>
      <html lang="en">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline';">
        <title>Solution for Issue #${issue.number}</title>
        <style>
          :root {
            --container-padding: 20px;
            --input-padding-vertical: 6px;
            --input-padding-horizontal: 4px;
            --input-margin-vertical: 4px;
            --input-margin-horizontal: 0;
          }

          body {
            padding: 0 var(--container-padding);
            color: var(--vscode-foreground);
            font-size: var(--vscode-font-size);
            font-weight: var(--vscode-font-weight);
            font-family: var(--vscode-font-family);
            background-color: var(--vscode-editor-background);
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
            background-color: var(--vscode-textBlockQuote-background);
            padding: 10px;
            border-radius: 3px;
            overflow-x: auto;
            color: var(--vscode-editor-foreground);
          }
          
          code {
            font-family: var(--vscode-editor-font-family);
            font-size: var(--vscode-editor-font-size);
            color: var(--vscode-textPreformat-foreground);
          }
          
          ul {
            padding-left: 20px;
          }
          
          li {
            margin-bottom: 8px;
          }
          
          a {
            color: var(--vscode-textLink-foreground);
          }
          
          a:hover {
            color: var(--vscode-textLink-activeForeground);
          }
          
          .file-link {
            cursor: pointer;
            color: var(--vscode-textLink-foreground);
            text-decoration: underline;
          }
          
          .file-link:hover {
            text-decoration: underline;
            color: var(--vscode-textLink-activeForeground);
          }
          
          .file-section {
            background-color: var(--vscode-editor-inactiveSelectionBackground);
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
          }
          
          .action-button {
            display: block;
            margin: 20px auto;
            padding: 8px 16px;
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            border-radius: 2px;
            cursor: pointer;
            font-size: 14px;
          }
          
          .action-button:hover {
            background-color: var(--vscode-button-hoverBackground);
          }
          
          *:focus {
            outline-color: var(--vscode-focusBorder) !important;
          }
        </style>
      </head>
      <body>
        <div id="content">
          ${this.markdownToHtml(solutionMarkdown)}
        </div>

        <div class="file-section">
          <h2>Archivos Relacionados</h2>
          <p>Haga clic en un archivo para abrirlo:</p>
          <ul>
            ${relevantFiles
              .map(
                (file) =>
                  `<li><span class="file-link" onclick="openFile('${file}')">${file}</span></li>`
              )
              .join("")}
          </ul>
        </div>
        
        <button class="action-button" onclick="generateFixes()">
          Generate AI Code Fixes
        </button>

        <script>
          ${webviewFunctions}
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
        // Code blocks
        .replace(/```([^`]*?)```/gs, "<pre><code>$1</code></pre>")
        // Inline code
        .replace(/`([^`]*?)`/g, "<code>$1</code>")
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
