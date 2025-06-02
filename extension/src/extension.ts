// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from "vscode";
import { GitHubService } from "./services/githubService";
import { IssueProvider } from "./providers/issueProvider";
import { AgentResponseProvider } from "./providers/agentResponseProvider";
import { UsedToolsProvider } from "./providers/usedToolsProvider";
import { registerIssueCommands } from "./commands/issueCommands";
import { registerAgentCommands } from "./commands/agentCommands";
import { ISSUES_VIEW_ID, AGENT_RESPONSES_VIEW_ID, USED_TOOLS_VIEW_ID, CMD_REFRESH_ISSUES, CMD_AUTHENTICATE, CMD_CLEAR_USED_TOOLS } from "./utils/constants";

// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {
  // Use the console to output diagnostic information (console.log) and errors (console.error)
  // This line of code will only be executed once when your extension is activated
  console.log('CodeMedic extension is now active!');

  // Initialize services
  const githubService = new GitHubService(context);
  
  // Create providers
  const agentResponseProvider = new AgentResponseProvider();
  const usedToolsProvider = new UsedToolsProvider();
  const issueProvider = new IssueProvider(githubService);
  
  // Create tree views
  const agentResponseTreeView = vscode.window.createTreeView(AGENT_RESPONSES_VIEW_ID, {
    treeDataProvider: agentResponseProvider,
    showCollapseAll: true,
  });
  
  const usedToolsTreeView = vscode.window.createTreeView(USED_TOOLS_VIEW_ID, {
    treeDataProvider: usedToolsProvider,
    showCollapseAll: true,
  });
  
  const issueTreeView = vscode.window.createTreeView(ISSUES_VIEW_ID, {
    treeDataProvider: issueProvider,
    showCollapseAll: true,
  });

  // Register tree views
  context.subscriptions.push(agentResponseTreeView, usedToolsTreeView, issueTreeView);

  // Store providers in global state
  context.globalState.update('agentResponseProvider', agentResponseProvider);
  context.globalState.update('usedToolsProvider', usedToolsProvider);

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
    }),
    vscode.commands.registerCommand(CMD_CLEAR_USED_TOOLS, () => {
      console.log('Clearing used tools...');
      usedToolsProvider.clear();
    })
  );
  
  // Register issue and agent commands
  registerIssueCommands(context, issueProvider, agentResponseProvider, githubService, usedToolsProvider);
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
          `🩺 Welcome to CodeMedic! Authenticate with GitHub to start fixing issues with AI`,
          "🔐 Authenticate",
          "Later"
        )
        .then((selection) => {
          if (selection === "🔐 Authenticate") {
            vscode.commands.executeCommand(CMD_AUTHENTICATE);
          }
        });
    } else {
      // If already authenticated, refresh issues
      issueProvider.refresh();
    }
  });
}

// This method is called when your extension is deactivated
export function deactivate() {}
