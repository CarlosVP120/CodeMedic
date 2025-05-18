import * as vscode from "vscode";
import { GitHubService } from "./githubService";

export class IssueItem extends vscode.TreeItem {
  constructor(
    public readonly issue: any,
    public readonly collapsibleState: vscode.TreeItemCollapsibleState
  ) {
    super(issue.title, collapsibleState);

    this.tooltip = issue.body;
    this.description = `#${issue.number} opened ${new Date(
      issue.created_at
    ).toLocaleDateString()}`;
    this.contextValue = "issue";

    // Set icons based on issue labels
    if (issue.labels && issue.labels.length > 0) {
      // Check for bug label
      if (
        issue.labels.some((label: any) =>
          label.name.toLowerCase().includes("bug")
        )
      ) {
        this.iconPath = new vscode.ThemeIcon("bug");
      } else if (
        issue.labels.some((label: any) =>
          label.name.toLowerCase().includes("feature")
        )
      ) {
        this.iconPath = new vscode.ThemeIcon("lightbulb");
      } else {
        this.iconPath = new vscode.ThemeIcon("issues");
      }
    } else {
      this.iconPath = new vscode.ThemeIcon("issues");
    }
  }
}

export class IssueProvider implements vscode.TreeDataProvider<IssueItem> {
  private _onDidChangeTreeData: vscode.EventEmitter<
    IssueItem | undefined | null | void
  > = new vscode.EventEmitter<IssueItem | undefined | null | void>();
  readonly onDidChangeTreeData: vscode.Event<
    IssueItem | undefined | null | void
  > = this._onDidChangeTreeData.event;

  constructor(private githubService: GitHubService) {
    // Refresh views when GitHub service issues change
    this.githubService.onDidChangeIssues(() => {
      this.refresh();
    });
  }

  refresh(): void {
    this._onDidChangeTreeData.fire();
  }

  getTreeItem(element: IssueItem): vscode.TreeItem {
    return element;
  }

  async getChildren(element?: IssueItem): Promise<IssueItem[]> {
    if (element) {
      // No children for issue items
      return [];
    } else {
      try {
        // Check if repo has GitHub remote
        const repoInfo = await this.githubService.getRepoInfo();
        if (!repoInfo) {
          // No GitHub repo or not authenticated
          return [
            new IssueItem(
              {
                title: "GitHub repository not found",
                body: "Please open a workspace with a GitHub remote repository",
                number: "",
                created_at: new Date().toISOString(),
                labels: [],
              },
              vscode.TreeItemCollapsibleState.None
            ),
          ];
        }

        // Check if authenticated with GitHub
        if (!this.githubService.isAuthenticated()) {
          return [
            new IssueItem(
              {
                title: "GitHub authentication required",
                body: "Click 'Authenticate with GitHub' to connect to your account",
                number: "",
                created_at: new Date().toISOString(),
                labels: [],
              },
              vscode.TreeItemCollapsibleState.None
            ),
          ];
        }

        // Get issues from GitHub
        const issues = await this.githubService.getIssues();

        if (issues.length === 0) {
          return [
            new IssueItem(
              {
                title: "No open issues found",
                body: "Great job! There are no open issues in this repository",
                number: "",
                created_at: new Date().toISOString(),
                labels: [],
              },
              vscode.TreeItemCollapsibleState.None
            ),
          ];
        }

        return issues.map((issue: any) => {
          return new IssueItem(issue, vscode.TreeItemCollapsibleState.None);
        });
      } catch (error) {
        vscode.window.showErrorMessage(
          `Error loading issues: ${(error as Error).message}`
        );
        return [
          new IssueItem(
            {
              title: "Error loading issues",
              body: (error as Error).message,
              number: "",
              created_at: new Date().toISOString(),
              labels: [],
            },
            vscode.TreeItemCollapsibleState.None
          ),
        ];
      }
    }
  }
}
