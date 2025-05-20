// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from "vscode";
import { GitHubService } from "./github/githubService";
import { IssueProvider } from "./github/issueProvider";
import axios from 'axios';
import * as path from 'path';

// Agent response provider for the new view
class AgentResponseProvider implements vscode.TreeDataProvider<AgentResponseItem> {
  private _onDidChangeTreeData: vscode.EventEmitter<AgentResponseItem | undefined | null | void> = new vscode.EventEmitter<AgentResponseItem | undefined | null | void>();
  readonly onDidChangeTreeData: vscode.Event<AgentResponseItem | undefined | null | void> = this._onDidChangeTreeData.event;
  
  private responses: AgentResponseItem[] = [];
  
  constructor() {}
  
  getTreeItem(element: AgentResponseItem): vscode.TreeItem {
    return element;
  }
  
  getChildren(element?: AgentResponseItem): Thenable<AgentResponseItem[]> {
    if (element) {
      return Promise.resolve([]);
    }
    return Promise.resolve(this.responses);
  }
  
  addResponse(issue: any, response: any): void {
    // Create a more descriptive label that includes the issue title
    const label = `Issue #${issue.number}: ${issue.title}`;
    
    // Extract status and agent output (if available)
    const status = response.result || 'Processing complete';
    const agentOutput = response.agent_output || '';
    
    // Create a description that includes status
    const description = `${status} - ${new Date().toLocaleString()}`;
    
    const item = new AgentResponseItem(
      label,
      response,
      description,
      agentOutput,
      vscode.TreeItemCollapsibleState.None
    );
    
    this.responses.unshift(item); // Add new responses at the top
    this._onDidChangeTreeData.fire();
  }
  
  clearResponses(): void {
    this.responses = [];
    this._onDidChangeTreeData.fire();
  }
}

class AgentResponseItem extends vscode.TreeItem {
  constructor(
    public readonly label: string,
    public readonly response: any,
    public readonly detailsText: string,
    public readonly agentOutput: string,
    public readonly collapsibleState: vscode.TreeItemCollapsibleState
  ) {
    super(label, collapsibleState);
    this.tooltip = `Agent response for ${label}`;
    this.description = detailsText;
    this.contextValue = 'agentResponse';
    
    // Add a custom icon
    this.iconPath = new vscode.ThemeIcon('rocket');
  }
}

// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {
  // Use the console to output diagnostic information (console.log) and errors (console.error)
  // This line of code will only be executed once when your extension is activated
  console.log('Congratulations, your extension "codemedic" is now active!');

  // Initialize services
  const githubService = new GitHubService(context);
  
  // Create agent response provider
  const agentResponseProvider = new AgentResponseProvider();
  const agentResponseTreeView = vscode.window.createTreeView("codemedic-agent-responses", {
    treeDataProvider: agentResponseProvider,
    showCollapseAll: true,
  });
  
  // Register the agent response tree view
  context.subscriptions.push(agentResponseTreeView);

  // Store the agent response provider in global state for access from other functions
  context.globalState.update('agentResponseProvider', agentResponseProvider);

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
    vscode.commands.registerCommand("codemedic.clearResponses", () => {
      agentResponseProvider.clearResponses();
    })
  );
  
  context.subscriptions.push(
    vscode.commands.registerCommand("codemedic.showAgentResponse", (item: AgentResponseItem) => {
      if (item && item.response) {
        const panel = vscode.window.createWebviewPanel(
          "agentResponseDetail",
          item.label,
          vscode.ViewColumn.Beside,
          { enableScripts: true }
        );
        
        // Create a more detailed HTML view that includes the agent output
        const responseHtml = getAgentResponseHtml(item.label, {
          ...item.response,
          agent_output: item.agentOutput
        });
        
        panel.webview.html = responseHtml;
      }
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
          showIssuePanel(issueItem.issue, context, agentResponseProvider);
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
          await fixIssue(issueItem.issue, undefined, agentResponseProvider);
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

function showIssuePanel(issue: any, context: vscode.ExtensionContext, agentResponseProvider: AgentResponseProvider) {
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
        // Pass both the webview and agent response provider
        await fixIssue(issue, panel.webview, agentResponseProvider);
      }
    },
    undefined,
    context.subscriptions
  );
}

// New function to send issue to the API
async function fixIssue(issue: any, webview?: vscode.Webview, agentResponseProvider?: AgentResponseProvider): Promise<void> {
  try {
    vscode.window.showInformationMessage(`Starting to fix issue #${issue.number}...`);

    // Prepare issue data for the API

    const github_credentials={
      token:"",
      repository_name: "Elcasvi/Code-Fixer-LLM-Agent"
    };

    const issue_data={
      number: issue.number,
      title: issue.title,
      body: issue.body || "",
      state: issue.state,
      created_at: issue.created_at,
      updated_at: issue.updated_at
    };

    const FixCodeRequest = {
      github_credentials: github_credentials,
      issue_data: issue_data
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
        const response = await axios.post("http://localhost:8000/api/fix/issue", FixCodeRequest);

        progress.report({ message: "Issue processed by agent", increment: 100 });

        // Show success message
        vscode.window.showInformationMessage(
          `Issue #${issue.number} has been processed by the agent.`
        );

        // If webview is provided, send the response to it
        if (webview) {
          webview.postMessage({
            command: 'agentResponse',
            response: response.data
          });
        }

        // If agent response provider is provided, add the response to it
        if (agentResponseProvider) {
          agentResponseProvider.addResponse(issue, response.data);
        }

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
        gap: 0.5rem;
        margin-top: 0.75rem;
      }
      
      .label {
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.75rem;
        border-radius: var(--radius-full);
        font-size: 0.75rem;
        font-weight: 500;
        background-color: var(--bg-accent);
        color: var(--text-secondary);
      }
      
      .body-section {
        margin-top: 2rem;
      }
      
      .body-content {
        background-color: var(--bg-accent);
        padding: 1.25rem;
        border-radius: var(--radius-md);
        font-size: 0.9375rem;
        white-space: pre-wrap;
      }
      
      .code-block {
        background-color: #1e1e1e;
        color: #e6e6e6;
        font-family: 'Fira Mono', 'Consolas', 'Menlo', monospace;
        font-size: 0.875rem;
        padding: 1.25rem;
        border-radius: var(--radius-md);
        margin-top: 1.5rem;
        margin-bottom: 1.5rem;
        overflow-x: auto;
        white-space: pre;
      }
      
      .actions {
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
        margin-top: 2rem;
        border-top: 1px solid var(--border-color);
        padding-top: 1.5rem;
      }
      
      .button {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.625rem 1.25rem;
        border-radius: var(--radius-md);
        font-size: 0.875rem;
        font-weight: 500;
        cursor: pointer;
        transition: var(--transition);
        border: none;
        outline: none;
      }
      
      .fix-button {
        background-color: var(--success-color);
        color: white;
      }
      
      .fix-button:hover {
        background-color: var(--success-hover);
      }
      
      .fix-button-icon {
        width: 1rem;
        height: 1rem;
      }
      
      .agent-response-section {
        margin-top: 2rem;
        border-top: 1px solid var(--border-color);
        padding-top: 1.5rem;
        display: none;
      }
      
      .agent-response-section.visible {
        display: block;
      }
      
      .agent-response-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
      }
      
      .agent-response-content {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: var(--radius-md);
        padding: 1.25rem;
        font-size: 0.9375rem;
        white-space: pre-wrap;
      }
      
      .agent-log {
        margin-top: 1.5rem;
      }
      
      .agent-log-title {
        font-size: 1.125rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 0.75rem;
      }
      
      .agent-log-content {
        background-color: #1e1e1e;
        color: #e6e6e6;
        font-family: 'Fira Mono', 'Consolas', 'Menlo', monospace;
        font-size: 0.875rem;
        padding: 1.25rem;
        border-radius: var(--radius-md);
        max-height: 400px;
        overflow-y: auto;
        white-space: pre-wrap;
      }
      
      .loading {
        display: none;
        align-items: center;
        justify-content: center;
        margin: 2rem 0;
      }
      
      .loading.visible {
        display: flex;
      }
      
      .loading-spinner {
        border: 4px solid rgba(0, 0, 0, 0.1);
        border-radius: 50%;
        border-top: 4px solid var(--primary-color);
        width: 24px;
        height: 24px;
        animation: spin 1s linear infinite;
        margin-right: 1rem;
      }
      
      @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
      }
    </style>
  </head>
  <body>
    <div class="navbar">
      <div class="logo-container">
        <img src="${logoUrl}" alt="CodeMedic Logo" style="height: 24px; width: 24px;" />
        <span class="app-name">CodeMedic</span>
      </div>
    </div>
    
    <div class="container">
      <div class="header">
        <h1 class="issue-title">
          <span class="issue-number">#${issue.number}</span>
          ${issue.title}
        </h1>
        
        <div class="meta">
          <div class="meta-item">
            <span class="status-badge ${issue.state === 'closed' ? 'closed' : ''}">
              ${issue.state}
            </span>
          </div>
          
          <div class="meta-item">
            Opened by <b>${issue.user?.login || "Unknown"}</b> on ${new Date(issue.created_at).toLocaleString()}
          </div>
        </div>
        
        <div class="labels">
          ${(issue.labels || [])
            .map((l: { name: string }) => `<span class="label">${l.name}</span>`)
            .join("")}
        </div>
      </div>
      
      <div class="body-section">
        <div class="body-content">${
          issue.body
            ? issue.body.replace(/</g, "&lt;").replace(/\n/g, "<br>")
            : "<i>No description provided.</i>"
        }</div>
      </div>
      
      <div class="actions">
        <button class="button fix-button" id="fix-button">
          <svg class="fix-button-icon" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
          </svg>
          Fix this issue with CodeMedic
        </button>
      </div>
      
      <div id="loading" class="loading">
        <div class="loading-spinner"></div>
        <span>Processing issue with CodeMedic agent...</span>
      </div>
      
      <div id="agent-response" class="agent-response-section">
        <h2 class="agent-response-title">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M9 11.24V7.5C9 6.12 10.12 5 11.5 5S14 6.12 14 7.5v3.74c1.21-.81 2-2.18 2-3.74C16 5.01 13.99 3 11.5 3S7 5.01 7 7.5c0 1.56.79 2.93 2 3.74zm9.84 4.63l-4.54-2.26c-.17-.07-.35-.11-.54-.11H13v-6c0-.83-.67-1.5-1.5-1.5S10 6.67 10 7.5v10.74c-3.6-.76-3.54-.75-3.67-.75-.31 0-.59.13-.79.33l-.79.8 4.94 4.94c.27.27.65.44 1.06.44h6.79c.75 0 1.33-.55 1.44-1.28l.75-5.27c.01-.07.02-.14.02-.2 0-.62-.38-1.16-.91-1.38z" fill="currentColor"/>
          </svg>
          Agent Solution
        </h2>
        <div id="agent-response-content" class="agent-response-content">
          The agent's response will appear here after processing the issue.
        </div>
        
        <div id="agent-log" class="agent-log" style="display: none;">
          <h3 class="agent-log-title">Agent Log Output</h3>
          <div id="agent-log-content" class="agent-log-content"></div>
        </div>
      </div>
    </div>
    
    <script>
      const vscode = acquireVsCodeApi();
      const loadingElement = document.getElementById('loading');
      const agentResponseSection = document.getElementById('agent-response');
      const agentResponseContent = document.getElementById('agent-response-content');
      const agentLogSection = document.getElementById('agent-log');
      const agentLogContent = document.getElementById('agent-log-content');
      const fixButton = document.getElementById('fix-button');
      
      // Add event listener to the fix button
      fixButton.addEventListener('click', () => {
        fixIssue();
      });
      
      function fixIssue() {
        // Show loading indicator
        loadingElement.classList.add('visible');
        
        // Hide agent response section while loading
        agentResponseSection.classList.remove('visible');
        
        vscode.postMessage({
          command: 'fixIssue'
        });
      }
      
      // Handle messages from the extension
      window.addEventListener('message', event => {
        const message = event.data;
        
        if (message.command === 'agentResponse') {
          // Hide loading indicator
          loadingElement.classList.remove('visible');
          
          // Show agent response section
          agentResponseSection.classList.add('visible');
          
          // Update agent response content
          let formattedResponse = '';
          
          try {
            // Try to format the response as JSON
            const response = message.response;
            formattedResponse = 
              '<strong>Status:</strong> ' + (response.result || 'Processing complete') + '<br><br>' +
              '<strong>Details:</strong><br>' + 
              JSON.stringify(response.details, null, 2)
                .replace(/\\n/g, '<br>')
                .replace(/\\"/g, '"')
                .replace(/\n/g, '<br>')
                .replace(/ /g, '&nbsp;');
                
            // Update the response content
            agentResponseContent.innerHTML = formattedResponse;
            
            // If we have agent output log, show it
            if (response.agent_output) {
              agentLogSection.style.display = 'block';
              agentLogContent.textContent = response.agent_output;
            } else {
              agentLogSection.style.display = 'none';
            }
          } catch (e) {
            // Fallback to simple string representation
            formattedResponse = JSON.stringify(message.response, null, 2)
              .replace(/\n/g, '<br>')
              .replace(/ /g, '&nbsp;');
              
            agentResponseContent.innerHTML = formattedResponse;
            agentLogSection.style.display = 'none';
          }
        }
      });
    </script>
  </body>
  </html>
  `;
}

function getAgentResponseHtml(title: string, response: any): string {
  return `
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>${title}</title>
      <style>
        :root {
          --primary-color: #2563eb;
          --primary-light: #3b82f6;
          --primary-dark: #1d4ed8;
          --success-color: #10b981;
          --text-primary: #1f2937;
          --text-secondary: #6b7280;
          --text-muted: #9ca3af;
          --bg-primary: #ffffff;
          --bg-secondary: #f9fafb;
          --bg-accent: #f3f4f6;
          --border-color: #e5e7eb;
          --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
          --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
          --radius-sm: 4px;
          --radius-md: 6px;
          --radius-lg: 8px;
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
          padding: 1rem;
        }
        
        .container {
          max-width: 950px;
          margin: 0 auto;
          padding: 2rem;
          background-color: var(--bg-primary);
          box-shadow: var(--shadow-md);
          border-radius: var(--radius-lg);
        }
        
        .header {
          border-bottom: 1px solid var(--border-color);
          padding-bottom: 1.25rem;
          margin-bottom: 1.5rem;
        }
        
        .title {
          font-size: 1.5rem;
          font-weight: 600;
          color: var(--text-primary);
          margin-bottom: 0.75rem;
        }
        
        .response-section {
          margin-top: 1.5rem;
        }
        
        .response-title {
          font-size: 1.25rem;
          font-weight: 600;
          color: var(--text-primary);
          margin-bottom: 1rem;
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }
        
        .response-content {
          background-color: #f8fafc;
          border: 1px solid #e2e8f0;
          border-radius: var(--radius-md);
          padding: 1.25rem;
          font-size: 0.9375rem;
          white-space: pre-wrap;
          overflow-x: auto;
        }
        
        .status {
          font-weight: 500;
          margin-bottom: 1rem;
        }
        
        .status-success {
          color: var(--success-color);
        }
        
        pre {
          background-color: #f1f5f9;
          padding: 1rem;
          border-radius: var(--radius-sm);
          overflow-x: auto;
          white-space: pre-wrap;
          font-family: 'Fira Mono', 'Consolas', 'Menlo', monospace;
          font-size: 0.875rem;
        }
        
        .agent-log {
          margin-top: 2rem;
          border-top: 1px solid var(--border-color);
          padding-top: 1.5rem;
        }
        
        .agent-log-title {
          font-size: 1.25rem;
          font-weight: 600;
          color: var(--text-primary);
          margin-bottom: 1rem;
        }
        
        .agent-log-content {
          background-color: #1e1e1e;
          color: #e6e6e6;
          font-family: 'Fira Mono', 'Consolas', 'Menlo', monospace;
          font-size: 0.875rem;
          padding: 1.25rem;
          border-radius: var(--radius-md);
          white-space: pre-wrap;
          overflow-x: auto;
          max-height: 500px;
          overflow-y: auto;
        }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1 class="title">
            ${title}
          </h1>
        </div>
        
        <div class="response-section">
          <h2 class="response-title">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M9 11.24V7.5C9 6.12 10.12 5 11.5 5S14 6.12 14 7.5v3.74c1.21-.81 2-2.18 2-3.74C16 5.01 13.99 3 11.5 3S7 5.01 7 7.5c0 1.56.79 2.93 2 3.74zm9.84 4.63l-4.54-2.26c-.17-.07-.35-.11-.54-.11H13v-6c0-.83-.67-1.5-1.5-1.5S10 6.67 10 7.5v10.74c-3.6-.76-3.54-.75-3.67-.75-.31 0-.59.13-.79.33l-.79.8 4.94 4.94c.27.27.65.44 1.06.44h6.79c.75 0 1.33-.55 1.44-1.28l.75-5.27c.01-.07.02-.14.02-.2 0-.62-.38-1.16-.91-1.38z" fill="currentColor"/>
            </svg>
            Agent Response
          </h2>
          
          <div class="status status-success">
            Status: ${response.result || 'Processing complete'}
          </div>
          
          <div class="response-content">
            <pre>${JSON.stringify(response.details, null, 2)}</pre>
          </div>
        </div>
        
        ${response.agent_output ? `
        <div class="agent-log">
          <h2 class="agent-log-title">Agent Log Output</h2>
          <div class="agent-log-content">${response.agent_output.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</div>
        </div>
        ` : ''}
      </div>
    </body>
    </html>
  `;
}

// This method is called when your extension is deactivated
export function deactivate() {}
