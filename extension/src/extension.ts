// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from "vscode";
import { GitHubService } from "./services/githubService";
import { IssueProvider } from "./providers/issueProvider";
import { AgentResponseProvider } from "./providers/agentResponseProvider";
import { AgentService } from "./services/agentService";
import { registerIssueCommands } from "./commands/issueCommands";
import { registerAgentCommands } from "./commands/agentCommands";
import { ISSUES_VIEW_ID, AGENT_RESPONSES_VIEW_ID, CMD_REFRESH_ISSUES, CMD_AUTHENTICATE } from "./utils/constants";
import axios from 'axios';
import * as path from 'path';
import { getIssueHtml } from "./utils/htmlTemplates";
import { fixIssue } from "./commands/issueCommands";

// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {
  // Use the console to output diagnostic information (console.log) and errors (console.error)
  // This line of code will only be executed once when your extension is activated
  console.log('CodeMedic extension is now active!');

  // Initialize services
  const githubService = new GitHubService(context);
  const agentService = new AgentService();
  
  // Create providers
  const agentResponseProvider = new AgentResponseProvider();
  const issueProvider = new IssueProvider(githubService);
  
  // Create tree views
  const agentResponseTreeView = vscode.window.createTreeView(AGENT_RESPONSES_VIEW_ID, {
    treeDataProvider: agentResponseProvider,
    showCollapseAll: true,
  });
  
  const issueTreeView = vscode.window.createTreeView(ISSUES_VIEW_ID, {
    treeDataProvider: issueProvider,
    showCollapseAll: true,
  });

  // Register tree views
  context.subscriptions.push(agentResponseTreeView, issueTreeView);

  // Store the agent response provider in global state
  context.globalState.update('agentResponseProvider', agentResponseProvider);

  // Register commands
  context.subscriptions.push(
    vscode.commands.registerCommand(CMD_REFRESH_ISSUES, () => {
      console.log('Refreshing issues...');
      issueProvider.refresh();
    }),
    vscode.commands.registerCommand(CMD_AUTHENTICATE, async () => {
      console.log('Authenticating with GitHub...');
      await githubService.authenticate();
      // Refresh issues after authentication
      issueProvider.refresh();
    })
  );
  
  // Register issue and agent commands
  registerIssueCommands(context, issueProvider, agentResponseProvider, githubService, agentService);
  registerAgentCommands(context, agentResponseProvider);

  // Verify GitHub repo on startup and refresh issues
  githubService.getRepoInfo().then((repoInfo) => {
    if (!repoInfo) {
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
            vscode.commands.executeCommand(CMD_AUTHENTICATE);
          }
        });
    } else {
      // If already authenticated, refresh issues
      issueProvider.refresh();
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
        const githubService = new GitHubService(context);
        const agentService = new AgentService();
        await fixIssue(issue, panel.webview, agentResponseProvider, githubService, agentService);
      }
    },
    undefined,
    context.subscriptions
  );
}

// This method is called when your extension is deactivated
export function deactivate() {}
