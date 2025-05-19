// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from "vscode";
import { GitHubService } from "./github/githubService";
import { IssueProvider } from "./github/issueProvider";
import axios from 'axios';
import * as path from 'path';

// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {
  // Use the console to output diagnostic information (console.log) and errors (console.error)
  // This line of code will only be executed once when your extension is activated
  console.log('Congratulations, your extension "codemedic" is now active!');

  // Initialize services
  const githubService = new GitHubService(context);

  // Create the issue tree view
  const issueProvider = new IssueProvider(githubService);
  const treeView = vscode.window.createTreeView("codemedic-issues", {
    treeDataProvider: issueProvider,
    showCollapseAll: true,
  });

  // Register the tree view
  context.subscriptions.push(treeView);

  // Register commands
  context.subscriptions.push(
    vscode.commands.registerCommand("codemedic.refreshIssues", () => {
      issueProvider.refresh();
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("codemedic.authenticate", async () => {
      await githubService.authenticate();
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand(
      "codemedic.showIssuePanel",
      async (issueItem) => {
        if (!issueItem) {
          const selectedItem = treeView.selection[0];
          if (!selectedItem) {
            vscode.window.showErrorMessage(
              "No issue selected. Please select an issue first."
            );
            return;
          }
          issueItem = selectedItem;
        }
        if (issueItem.contextValue === "issue") {
          showIssuePanel(issueItem.issue, context);
        } else {
          vscode.window.showErrorMessage("Please select a valid GitHub issue.");
        }
      }
    )
  );

  // New command to fix an issue using the agent
  context.subscriptions.push(
    vscode.commands.registerCommand(
      "codemedic.fixIssue",
      async (issueItem) => {
        if (!issueItem) {
          const selectedItem = treeView.selection[0];
          if (!selectedItem) {
            vscode.window.showErrorMessage(
              "No issue selected. Please select an issue first."
            );
            return;
          }
          issueItem = selectedItem;
        }
        
        if (issueItem.contextValue === "issue") {
          await fixIssue(issueItem.issue);
        } else {
          vscode.window.showErrorMessage("Please select a valid GitHub issue.");
        }
      }
    )
  );

  // Verify GitHub repo on startup
  githubService.getRepoInfo().then((repoInfo) => {
    if (!repoInfo) {
      // Already shows error message in the function
      return;
    }

    // If we have a valid GitHub repo, check if we're already authenticated
    if (!githubService.isAuthenticated()) {
      vscode.window
        .showInformationMessage(
          "Authenticate with GitHub to view and manage issues",
          "Authenticate"
        )
        .then((selection) => {
          if (selection === "Authenticate") {
            vscode.commands.executeCommand("codemedic.authenticate");
          }
        });
    }
  });
}

function showIssuePanel(issue: any, context: vscode.ExtensionContext) {
  const panel = vscode.window.createWebviewPanel(
    "issuePanel",
    `Issue #${issue.number}: ${issue.title}`,
    vscode.ViewColumn.Beside,
    { 
      enableScripts: true,
      localResourceRoots: [vscode.Uri.file(path.join(context.extensionPath, 'resources'))]
    }
  );
  
  // Get the path to the logo image
  const logoPath = vscode.Uri.file(
    path.join(context.extensionPath, 'resources', 'logo.png')
  );
  
  // Convert the URI to a string that the webview can use
  const logoUri = panel.webview.asWebviewUri(logoPath);
  
  // Add fix button to the panel
  panel.webview.html = getIssueHtml(issue, logoUri.toString());
  
  // Handle messages from the webview
  panel.webview.onDidReceiveMessage(
    async (message) => {
      if (message.command === "fixIssue") {
        await fixIssue(issue);
      }
    },
    undefined,
    context.subscriptions
  );
}

// New function to send issue to the API
async function fixIssue(issue: any): Promise<void> {
  try {
    vscode.window.showInformationMessage(`Starting to fix issue #${issue.number}...`);
    
    // Prepare issue data for the API
    const issueData = {
      number: issue.number,
      title: issue.title,
      body: issue.body || "",
      state: issue.state,
      created_at: issue.created_at,
      updated_at: issue.updated_at
    };
    
    // Configure progress notification
    await vscode.window.withProgress({
      location: vscode.ProgressLocation.Notification,
      title: `Fixing issue #${issue.number}`,
      cancellable: false
    }, async (progress) => {
      progress.report({ message: "Sending issue to CodeMedic agent..." });
      
      try {
        // Send the issue to the API
        const response = await axios.post("http://localhost:8000/api/fix", issueData);
        
        progress.report({ message: "Issue received by agent", increment: 50 });
        
        // Show success message
        vscode.window.showInformationMessage(
          `Issue #${issue.number} is being processed by the agent. Check the server logs for details.`
        );
        
        // Return response data for handling
        return response.data;
      } catch (error) {
        vscode.window.showErrorMessage(`Failed to connect to CodeMedic server: ${error}`);
        throw error;
      }
    });
    
  } catch (error) {
    vscode.window.showErrorMessage(`Error fixing issue: ${error}`);
  }
}

function getIssueHtml(issue: any, logoUrl: string): string {
  return `
    <!DOCTYPE html>
  <html lang="en">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Issue #${issue.number}</title>
    <style>
      :root {
        --primary-color: #2563eb;
        --primary-light: #3b82f6;
        --primary-dark: #1d4ed8;
        --success-color: #10b981;
        --success-hover: #059669;
        --text-primary: #1f2937;
        --text-secondary: #6b7280;
        --text-muted: #9ca3af;
        --bg-primary: #ffffff;
        --bg-secondary: #f9fafb;
        --bg-accent: #f3f4f6;
        --border-color: #e5e7eb;
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        --radius-sm: 4px;
        --radius-md: 6px;
        --radius-lg: 8px;
        --radius-full: 9999px;
        --transition: all 0.2s ease;
      }
      
      * {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
      }
      
      body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        line-height: 1.5;
        color: var(--text-primary);
        background-color: var(--bg-secondary);
        padding: 0;
        margin: 0;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
      }
      
      .container {
        max-width: 950px;
        margin: 0 auto;
        padding: 2rem;
        background-color: var(--bg-primary);
        box-shadow: var(--shadow-md);
        border-radius: var(--radius-lg);
        margin-top: 2rem;
        margin-bottom: 2rem;
        transition: var(--transition);
      }
      
      .container:hover {
        box-shadow: var(--shadow-lg);
      }
      
      .navbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.75rem 1.5rem;
        background: #15426d;
        color: white;
        box-shadow: var(--shadow-md);
        position: sticky;
        top: 0;
        z-index: 100;
      }
      
      .logo-container {
        display: flex;
        align-items: center;
        gap: 0.75rem;
      }
      
      .app-name {
        font-size: 1.25rem;
        font-weight: 600;
        letter-spacing: 0.5px;
      }
      
      .header {
        border-bottom: 1px solid var(--border-color);
        padding-bottom: 1.25rem;
        margin-bottom: 1.5rem;
      }
      
      .issue-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 0.75rem;
        line-height: 1.3;
      }
      
      .issue-number {
        color: var(--text-secondary);
        font-weight: 500;
        margin-right: 0.5rem;
      }
      
      .meta {
        display: flex;
        gap: 1.25rem;
        flex-wrap: wrap;
        align-items: center;
        color: var(--text-secondary);
        font-size: 0.875rem;
        margin-bottom: 1rem;
      }
      
      .meta-item {
        display: flex;
        align-items: center;
        gap: 0.375rem;
      }
      
      .status-badge {
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.75rem;
        border-radius: var(--radius-full);
        font-size: 0.75rem;
        font-weight: 500;
        background-color: #dcfce7;
        color: #166534;
        box-shadow: var(--shadow-sm);
      }
      
      .status-badge.closed {
        background-color: #fee2e2;
        color: #991b1b;
      }
      
      .labels {
        display: flex;
        flex-wrap: wrap;
        gap: 0.625rem;
        margin: 1rem 0;
      }
      
      .label {
        display: inline-block;
        background: #e0f2fe;
        color: #0369a1;
        border-radius: var(--radius-full);
        padding: 0.25rem 0.75rem;
        font-size: 0.75rem;
        font-weight: 500;
        box-shadow: var(--shadow-sm);
        transition: var(--transition);
      }
      
      .label:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      }
      
      .body {
        padding: 1.25rem;
        white-space: pre-wrap;
        line-height: 1.6;
        color: var(--text-primary);
        font-size: 0.95rem;
        border-bottom: 1px solid var(--border-color);
        margin-bottom: 1.5rem;
        background-color: var(--bg-accent);
        border-radius: var(--radius-md);
      }
      
      .actions {
        display: flex;
        gap: 1rem;
        margin-top: 1.5rem;
      }
      
      .fix-button {
        background: linear-gradient(to right, var(--success-color), #10b981);
        color: white;
        padding: 0.75rem 1.5rem;
        border: none;
        border-radius: var(--radius-md);
        font-size: 0.9375rem;
        font-weight: 500;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 0.625rem;
        box-shadow: var(--shadow-md);
        transition: var(--transition);
        position: relative;
        overflow: hidden;
      }
      
      .fix-button:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
        background: linear-gradient(to right, #059669, #047857);
      }
      
      .fix-button:active {
        transform: translateY(0);
      }
      
      .fix-button::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(to right, transparent, rgba(255, 255, 255, 0.3), transparent);
        transform: translateX(-100%);
      }
      
      .fix-button:hover::after {
        transform: translateX(100%);
        transition: transform 0.8s ease;
      }
      
      .fix-button-icon {
        display: inline-block;
        width: 18px;
        height: 18px;
      }
      
      /* Responsive adjustments */
      @media (max-width: 768px) {
        .container {
          margin-top: 1rem;
          margin-bottom: 1rem;
          padding: 1.25rem;
          border-radius: var(--radius-md);
        }
        
        .issue-title {
          font-size: 1.25rem;
        }
        
        .meta {
          gap: 0.75rem;
        }
      }
      
      @media (max-width: 480px) {
        .container {
          padding: 1rem;
          margin-top: 0.5rem;
          margin-bottom: 0.5rem;
        }
        
        .meta {
          flex-direction: column;
          align-items: flex-start;
          gap: 0.5rem;
        }
      }

      /* Robot icon for logo */
      .logo-image {
        width: 32px;
        height: 32px;
        filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.3));
      }
      
      /* Animate logo on hover */
      .logo-image:hover {
        animation: pulse 1.5s infinite;
      }
      
      @keyframes pulse {
        0% {
          transform: scale(1);
        }
        50% {
          transform: scale(1.05);
        }
        100% {
          transform: scale(1);
        }
      }
    </style>
  </head>
  <body>
    <div class="navbar">
      <div class="logo-container">
        <!-- CodeMedic Logo -->
        <img src="${logoUrl}" alt="CodeMedic Logo" class="logo-image" />
        <span class="app-name">CodeMedic</span>
      </div>
    </div>
    
    <div class="container">
      <div class="header">
        <h1 class="issue-title">
          <span class="issue-number">#${issue.number}</span> ${issue.title}
        </h1>
        <div class="meta">
          <div class="meta-item">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M8 8C10.2091 8 12 6.20914 12 4C12 1.79086 10.2091 0 8 0C5.79086 0 4 1.79086 4 4C4 6.20914 5.79086 8 8 8Z" fill="#6b7280"/>
              <path d="M8 9C3.58172 9 0 12.5817 0 17H16C16 12.5817 12.4183 9 8 9Z" fill="#6b7280"/>
            </svg>
            <span><b>${issue.user?.login || "Unknown user"}</b></span>
          </div>
          <div class="meta-item">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M8 0C3.58 0 0 3.58 0 8C0 12.42 3.58 16 8 16C12.42 16 16 12.42 16 8C16 3.58 12.42 0 8 0ZM8 14.5C4.41 14.5 1.5 11.59 1.5 8C1.5 4.41 4.41 1.5 8 1.5C11.59 1.5 14.5 4.41 14.5 8C14.5 11.59 11.59 14.5 8 14.5ZM8.75 8H12V9.5H7.25V4H8.75V8Z" fill="#6b7280"/>
            </svg>
            <span>Opened on ${new Date(issue.created_at).toLocaleString()}</span>
          </div>
          <div class="meta-item">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M8 0C3.58 0 0 3.58 0 8C0 12.42 3.58 16 8 16C12.42 16 16 12.42 16 8C16 3.58 12.42 0 8 0ZM8 14.5C4.41 14.5 1.5 11.59 1.5 8C1.5 4.41 4.41 1.5 8 1.5C11.59 1.5 14.5 4.41 14.5 8C14.5 11.59 11.59 14.5 8 14.5ZM8.75 8H12V9.5H7.25V4H8.75V8Z" fill="#6b7280"/>
            </svg>
            <span>Updated on ${new Date(issue.updated_at).toLocaleString()}</span>
          </div>
          <div class="status-badge ${issue.state === 'closed' ? 'closed' : ''}">
            ${issue.state === 'closed' ? 'Closed' : 'Open'}
          </div>
        </div>
        <div class="labels">
          ${(issue.labels || [])
            .map((l: { name: string }) => `<span class="label">${l.name}</span>`)
            .join("")}
        </div>
      </div>
      
      <div class="body">${
        issue.body
          ? issue.body.replace(/</g, "&lt;").replace(/\n/g, "<br>")
          : "<i>No description provided.</i>"
      }</div>
      
      <div class="actions">
        <button class="fix-button" onclick="fixIssue()">
          <svg class="fix-button-icon" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
          </svg>
          Fix this issue with CodeMedic
        </button>
      </div>
    </div>
    
    <script>
      const vscode = acquireVsCodeApi();
      
      function fixIssue() {
        vscode.postMessage({
          command: 'fixIssue'
        });
      }
    </script>
  </body>
  </html>
  `;
}

// This method is called when your extension is deactivated
export function deactivate() {}
