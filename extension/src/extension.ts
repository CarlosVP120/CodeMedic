// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from "vscode";
import { GitHubService } from "./github/githubService";
import { IssueProvider } from "./github/issueProvider";

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
          showIssuePanel(issueItem.issue);
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

function showIssuePanel(issue: any) {
  const panel = vscode.window.createWebviewPanel(
    "issuePanel",
    `Issue #${issue.number}: ${issue.title}`,
    vscode.ViewColumn.Beside,
    { enableScripts: false }
  );
  panel.webview.html = getIssueHtml(issue);
}

function getIssueHtml(issue: any): string {
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
    </body>
    </html>
  `;
}

// This method is called when your extension is deactivated
export function deactivate() {}
