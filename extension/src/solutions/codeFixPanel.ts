import * as vscode from "vscode";
import * as path from "path";
import { CodeFix } from "./aiService";

/**
 * A panel that allows users to review and apply AI-generated code fixes
 */
export class CodeFixPanel {
  public static currentPanel: CodeFixPanel | undefined;
  private readonly panel: vscode.WebviewPanel;
  private readonly codeFixes: CodeFix[];
  private readonly issue: any;
  private disposables: vscode.Disposable[] = [];

  /**
   * Creates or shows the code fix panel
   */
  public static show(issue: any, codeFixes: CodeFix[]): CodeFixPanel {
    // If we already have a panel, show it
    if (CodeFixPanel.currentPanel) {
      CodeFixPanel.currentPanel.panel.reveal(vscode.ViewColumn.Beside);
      CodeFixPanel.currentPanel.update(issue, codeFixes);
      return CodeFixPanel.currentPanel;
    }

    // Otherwise, create a new panel
    const panel = vscode.window.createWebviewPanel(
      "codeFixPanel",
      `AI Fix for Issue #${issue.number}`,
      vscode.ViewColumn.Beside,
      {
        enableScripts: true,
        retainContextWhenHidden: true,
        localResourceRoots: [
          vscode.Uri.file(
            path.join(vscode.workspace.workspaceFolders?.[0].uri.fsPath || "")
          ),
        ],
      }
    );

    return new CodeFixPanel(panel, issue, codeFixes);
  }

  private constructor(
    panel: vscode.WebviewPanel,
    issue: any,
    codeFixes: CodeFix[]
  ) {
    this.panel = panel;
    this.issue = issue;
    this.codeFixes = codeFixes;

    // Set up initial content
    this.updateContent();

    // Listen for when the panel is disposed
    // This happens when the user closes the panel or when the panel is closed programmatically
    this.panel.onDidDispose(() => this.dispose(), null, this.disposables);

    // Handle messages from the webview
    this.panel.webview.onDidReceiveMessage(
      async (message) => {
        switch (message.command) {
          case "applyFix":
            await this.applyFix(message.filePath);
            return;
          case "applyAllFixes":
            await this.applyAllFixes();
            return;
          case "showDiff":
            await this.showDiff(message.filePath);
            return;
          case "openFile":
            await this.openFile(message.filePath);
            return;
        }
      },
      null,
      this.disposables
    );

    CodeFixPanel.currentPanel = this;
  }

  /**
   * Updates the panel with new data
   */
  public update(issue: any, codeFixes: CodeFix[]): void {
    this.codeFixes.length = 0;
    codeFixes.forEach((fix) => this.codeFixes.push(fix));
    this.updateContent();
  }

  /**
   * Applies a single fix to a file
   */
  private async applyFix(filePath: string): Promise<void> {
    const fix = this.codeFixes.find((f) => f.filePath === filePath);
    if (!fix) {
      vscode.window.showErrorMessage(`Could not find fix for ${filePath}`);
      return;
    }

    try {
      // Get workspace folder
      const workspaceFolders = vscode.workspace.workspaceFolders;
      if (!workspaceFolders) {
        throw new Error("No workspace folder open");
      }

      // Build full file path
      const fileUri = vscode.Uri.file(
        path.join(workspaceFolders[0].uri.fsPath, fix.filePath)
      );

      // Write the fixed code to the file
      await vscode.workspace.fs.writeFile(
        fileUri,
        Buffer.from(fix.fixedCode, "utf8")
      );

      vscode.window.showInformationMessage(
        `Successfully applied fix to ${fix.filePath}`
      );

      // Update the UI to show this fix has been applied
      this.updateContent();
    } catch (error) {
      vscode.window.showErrorMessage(
        `Error applying fix to ${filePath}: ${(error as Error).message}`
      );
    }
  }

  /**
   * Applies all fixes to their respective files
   */
  private async applyAllFixes(): Promise<void> {
    const confirmResult = await vscode.window.showWarningMessage(
      `Are you sure you want to apply all ${this.codeFixes.length} fixes?`,
      { modal: true },
      "Yes",
      "No"
    );

    if (confirmResult !== "Yes") {
      return;
    }

    let successCount = 0;
    let errorCount = 0;

    for (const fix of this.codeFixes) {
      try {
        // Get workspace folder
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders) {
          throw new Error("No workspace folder open");
        }

        // Build full file path
        const fileUri = vscode.Uri.file(
          path.join(workspaceFolders[0].uri.fsPath, fix.filePath)
        );

        // Write the fixed code to the file
        await vscode.workspace.fs.writeFile(
          fileUri,
          Buffer.from(fix.fixedCode, "utf8")
        );

        successCount++;
      } catch (error) {
        vscode.window.showErrorMessage(
          `Error applying fix to ${fix.filePath}: ${(error as Error).message}`
        );
        errorCount++;
      }
    }

    vscode.window.showInformationMessage(
      `Applied ${successCount} fixes successfully${
        errorCount > 0 ? `, ${errorCount} files had errors` : ""
      }.`
    );

    // Update the UI
    this.updateContent();
  }

  /**
   * Shows a diff view for a file
   */
  private async showDiff(filePath: string): Promise<void> {
    const fix = this.codeFixes.find((f) => f.filePath === filePath);
    if (!fix) {
      vscode.window.showErrorMessage(`Could not find fix for ${filePath}`);
      return;
    }

    try {
      // Get workspace folder
      const workspaceFolders = vscode.workspace.workspaceFolders;
      if (!workspaceFolders) {
        throw new Error("No workspace folder open");
      }

      // Create URIs for the diff editor
      const fileUri = vscode.Uri.file(
        path.join(workspaceFolders[0].uri.fsPath, fix.filePath)
      );

      // Create a temporary file for the fixed code
      const fileName = path.basename(fix.filePath);
      const fileExt = path.extname(fix.filePath);
      const baseName = fileName.replace(fileExt, "");

      const tempFileUri = vscode.Uri.file(
        path.join(
          workspaceFolders[0].uri.fsPath,
          `.vscode/${baseName}.fixed${fileExt}`
        )
      );

      // Ensure .vscode directory exists
      try {
        await vscode.workspace.fs.createDirectory(
          vscode.Uri.file(path.join(workspaceFolders[0].uri.fsPath, ".vscode"))
        );
      } catch (e) {
        // Directory may already exist
      }

      // Write fixed content to temp file
      await vscode.workspace.fs.writeFile(
        tempFileUri,
        Buffer.from(fix.fixedCode, "utf8")
      );

      // Show diff
      const title = `Diff for ${fix.filePath}`;
      await vscode.commands.executeCommand(
        "vscode.diff",
        fileUri,
        tempFileUri,
        title
      );
    } catch (error) {
      vscode.window.showErrorMessage(
        `Error showing diff for ${filePath}: ${(error as Error).message}`
      );
    }
  }

  /**
   * Opens a file in the editor
   */
  private async openFile(filePath: string): Promise<void> {
    try {
      // Get workspace folder
      const workspaceFolders = vscode.workspace.workspaceFolders;
      if (!workspaceFolders) {
        throw new Error("No workspace folder open");
      }

      // Build full file path
      const fileUri = vscode.Uri.file(
        path.join(workspaceFolders[0].uri.fsPath, filePath)
      );

      // Open the file
      const document = await vscode.workspace.openTextDocument(fileUri);
      await vscode.window.showTextDocument(document);
    } catch (error) {
      vscode.window.showErrorMessage(
        `Error opening file ${filePath}: ${(error as Error).message}`
      );
    }
  }

  /**
   * Updates the webview content
   */
  private updateContent(): void {
    const { title, number, body } = this.issue;
    this.panel.webview.html = this.getHtmlContent(
      title,
      number,
      body || "No description provided"
    );
  }

  /**
   * Generates HTML content for the webview
   */
  private getHtmlContent(
    title: string,
    issueNumber: number,
    description: string
  ): string {
    // Create HTML for each code fix
    const codeFixes = this.codeFixes
      .map((fix, index) => {
        return `
        <div class="code-fix">
          <div class="file-header">
            <h3>${fix.filePath}</h3>
            <div class="file-actions">
              <button class="action-button" onclick="showDiff('${
                fix.filePath
              }')">
                <i class="codicon codicon-diff"></i> View Diff
              </button>
              <button class="action-button" onclick="applyFix('${
                fix.filePath
              }')">
                <i class="codicon codicon-check"></i> Apply Fix
              </button>
              <button class="action-button" onclick="openFile('${
                fix.filePath
              }')">
                <i class="codicon codicon-go-to-file"></i> Open File
              </button>
            </div>
          </div>
          <div class="fix-explanation">
            <h4>Changes:</h4>
            <div class="explanation-content">${this.formatExplanation(
              fix.explanation
            )}</div>
          </div>
        </div>
      `;
      })
      .join("");

    return `
      <!DOCTYPE html>
      <html lang="en">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline';">
        <title>AI Fix for Issue #${issueNumber}</title>
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

          ol, ul {
            padding-left: var(--container-padding);
          }

          body > *,
          form > * {
            margin-block-start: var(--input-margin-vertical);
            margin-block-end: var(--input-margin-vertical);
          }

          *:focus {
            outline-color: var(--vscode-focusBorder) !important;
          }

          a {
            color: var(--vscode-textLink-foreground);
          }

          a:hover, a:active {
            color: var(--vscode-textLink-activeForeground);
          }

          code {
            font-size: var(--vscode-editor-font-size);
            font-family: var(--vscode-editor-font-family);
            color: var(--vscode-textPreformat-foreground);
          }

          button {
            border: none;
            padding: var(--input-padding-vertical) var(--input-padding-horizontal);
            text-align: center;
            outline: 1px solid transparent;
            color: var(--vscode-button-foreground);
            background: var(--vscode-button-background);
            cursor: pointer;
          }

          button:hover {
            background: var(--vscode-button-hoverBackground);
          }

          button:focus {
            outline-color: var(--vscode-focusBorder);
          }

          button.secondary {
            color: var(--vscode-button-secondaryForeground);
            background: var(--vscode-button-secondaryBackground);
          }

          button.secondary:hover {
            background: var(--vscode-button-secondaryHoverBackground);
          }

          .action-button {
            margin-right: 8px;
            padding: 4px 8px;
            font-size: 12px;
            border-radius: 2px;
          }

          .issue-header {
            padding: 10px;
            margin-bottom: 20px;
            background-color: var(--vscode-sideBar-background);
            border-left: 4px solid var(--vscode-activityBarBadge-background);
            border-radius: 4px;
          }

          .issue-description {
            margin-bottom: 16px;
            padding: 10px;
            background-color: var(--vscode-editor-inactiveSelectionBackground);
            border-radius: 4px;
            font-size: 14px;
          }

          .code-fix {
            margin-bottom: 20px;
            border: 1px solid var(--vscode-panel-border);
            border-radius: 4px;
            overflow: hidden;
          }

          .file-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 12px;
            background-color: var(--vscode-sideBarSectionHeader-background);
            border-bottom: 1px solid var(--vscode-panel-border);
          }

          .file-header h3 {
            margin: 0;
            font-size: 14px;
          }

          .file-actions {
            display: flex;
          }

          .fix-explanation {
            padding: 12px;
            background-color: var(--vscode-editor-background);
          }

          .fix-explanation h4 {
            margin-top: 0;
            margin-bottom: 8px;
            font-size: 14px;
          }

          .explanation-content {
            font-size: 13px;
            line-height: 1.4;
          }

          .explanation-content ul {
            margin-top: 0;
          }

          .apply-all-container {
            margin-top: 20px;
            margin-bottom: 30px;
            text-align: center;
          }

          .apply-all-button {
            padding: 8px 16px;
            font-size: 14px;
          }

          .no-fixes {
            padding: 20px;
            text-align: center;
            color: var(--vscode-descriptionForeground);
          }

          h1, h2, h3, h4, h5, h6 {
            color: var(--vscode-editor-foreground);
          }
        </style>
      </head>
      <body>
        <div class="issue-header">
          <h2>Issue #${issueNumber}: ${title}</h2>
          <div class="issue-description">
            ${description.replace(/\n/g, "<br>")}
          </div>
        </div>

        <h2>AI-Generated Code Fixes</h2>
        
        ${
          this.codeFixes.length === 0
            ? '<div class="no-fixes">No code fixes generated yet.</div>'
            : `
            <div class="apply-all-container">
              <button class="apply-all-button" onclick="applyAllFixes()">
                Apply All Fixes
              </button>
            </div>
            
            ${codeFixes}
          `
        }

        <script>
          const vscode = acquireVsCodeApi();
          
          function applyFix(filePath) {
            vscode.postMessage({
              command: 'applyFix',
              filePath: filePath
            });
          }
          
          function applyAllFixes() {
            vscode.postMessage({
              command: 'applyAllFixes'
            });
          }
          
          function showDiff(filePath) {
            vscode.postMessage({
              command: 'showDiff',
              filePath: filePath
            });
          }
          
          function openFile(filePath) {
            vscode.postMessage({
              command: 'openFile',
              filePath: filePath
            });
          }
        </script>
      </body>
      </html>
    `;
  }

  /**
   * Formats the explanation from OpenAI to HTML
   */
  private formatExplanation(explanation: string): string {
    // Simple formatting for common markdown patterns
    let formatted = explanation
      // Convert bullet points to HTML list
      .replace(/^[\s]*[-*][\s]+(.*)/gm, "<li>$1</li>")
      // Bold
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      // Italic
      .replace(/\*(.*?)\*/g, "<em>$1</em>")
      // Code
      .replace(/`(.*?)`/g, "<code>$1</code>");

    // Wrap lists in <ul> tags
    if (formatted.includes("<li>")) {
      formatted = "<ul>" + formatted + "</ul>";
    }

    return formatted;
  }

  /**
   * Disposes of the panel
   */
  private dispose(): void {
    CodeFixPanel.currentPanel = undefined;

    // Clean up our resources
    this.panel.dispose();

    while (this.disposables.length) {
      const x = this.disposables.pop();
      if (x) {
        x.dispose();
      }
    }
  }
}
