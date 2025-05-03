// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from "vscode";
import { GitHubService } from "./github/githubService";
import { IssueProvider } from "./github/issueProvider";
import { SolutionService } from "./solutions/solutionService";

// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {
  // Use the console to output diagnostic information (console.log) and errors (console.error)
  // This line of code will only be executed once when your extension is activated
  console.log('Congratulations, your extension "codemedic" is now active!');

  // Initialize services
  const githubService = new GitHubService(context);
  const solutionService = new SolutionService();

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
      "codemedic.showSolution",
      async (issueItem) => {
        // If called from command palette without context
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

        // Only process actual issues (not placeholder items)
        if (issueItem.contextValue === "issue") {
          await solutionService.showSolution(issueItem.issue);
        } else {
          vscode.window.showErrorMessage("Please select a valid GitHub issue.");
        }
      }
    )
  );

  context.subscriptions.push(
    vscode.commands.registerCommand(
      "codemedic.solveIssue",
      async (issueItem) => {
        // If called from command palette without context
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

        // Only process actual issues (not placeholder items)
        if (issueItem.contextValue === "issue") {
          await solutionService.solveIssue(issueItem.issue);
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

// This method is called when your extension is deactivated
export function deactivate() {}
