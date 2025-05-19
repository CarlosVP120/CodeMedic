// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from "vscode";
import { GitHubService } from "./github/githubService";
import { IssueProvider } from "./github/issueProvider";
import axios from 'axios';

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
    { enableScripts: true }
  );
  
  // Add fix button to the panel
  panel.webview.html = getIssueHtml(issue);
  
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

function getIssueHtml(issue: any): string {
  const codeBlock =
    `GitHubIssue(\n` +
    `  number: ${JSON.stringify(issue.number)},\n` +
    `  title: ${JSON.stringify(issue.title)},\n` +
    `  body: ${JSON.stringify(issue.body)},\n` +
    `  state: ${JSON.stringify(issue.state)},\n` +
    `  created_at: ${JSON.stringify(issue.created_at)},\n` +
    `  updated_at: ${JSON.stringify(issue.updated_at)}\n)`;
  return `
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Issue #${issue.number}</title>
      <style>
        body { font-family: sans-serif; padding: 2rem; color: #222; background: #fff; }
        .header { margin-bottom: 1rem; }
        .number { color: #888; }
        .labels { margin: 0.5rem 0; }
        .label { display: inline-block; background: #eee; color: #333; border-radius: 3px; padding: 2px 8px; margin-right: 4px; font-size: 0.9em; }
        .meta { color: #666; font-size: 0.95em; margin-bottom: 1rem; }
        .body { white-space: pre-wrap; margin-top: 1.5rem; }
        .code-block { background: #23272e; color: #e6e6e6; border-radius: 6px; padding: 1rem; margin-top: 2rem; font-family: 'Fira Mono', 'Consolas', 'Menlo', monospace; font-size: 1em; overflow-x: auto; box-shadow: 0 2px 8px #0001; }
        .fix-button { 
          background-color: #2ea44f;
          color: white;
          padding: 8px 16px;
          border: none;
          border-radius: 6px;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          margin-top: 1rem;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .fix-button:hover {
          background-color: #2c974b;
          box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }
      </style>
    </head>
    <body>
      <div class="header">
        <h2>Issue #${issue.number}: ${issue.title}</h2>
        <div class="meta">
          Opened by <b>${issue.user?.login || "?"}</b> on ${new Date(
    issue.created_at
  ).toLocaleString()}
        </div>
        <div class="labels">
          ${(issue.labels || [])
            .map((l: any) => `<span class="label">${l.name}</span>`)
            .join(" ")}
        </div>
      </div>
      <div class="body">${
        issue.body
          ? issue.body.replace(/</g, "&lt;")
          : "<i>No description provided.</i>"
      }</div>
      <div class="code-block"><pre>${codeBlock}</pre></div>
      
      <button class="fix-button" onclick="fixIssue()">Fix this issue with CodeMedic</button>
      
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
