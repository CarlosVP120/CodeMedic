import * as vscode from "vscode";
import { Octokit } from "@octokit/rest";
import simpleGit, { SimpleGit } from "simple-git";

export class GitHubService {
  private octokit: Octokit | undefined;
  private context: vscode.ExtensionContext;
  private _onDidChangeIssues = new vscode.EventEmitter<void>();
  readonly onDidChangeIssues = this._onDidChangeIssues.event;

  constructor(context: vscode.ExtensionContext) {
    this.context = context;
    this.initializeOctokit();
  }

  private async initializeOctokit() {
    const token = this.context.globalState.get<string>("github-token");
    if (token) {
      this.octokit = new Octokit({ auth: token });
    }
  }

  public isAuthenticated(): boolean {
    return !!this.octokit;
  }

  public async authenticate() {
    const token = await vscode.window.showInputBox({
      prompt: "Enter your GitHub personal access token",
      password: true,
      placeHolder: "GitHub token with repo scope",
    });

    if (token) {
      try {
        this.octokit = new Octokit({ auth: token });
        // Test the token by fetching user info
        await this.octokit.users.getAuthenticated();
        await this.context.globalState.update("github-token", token);
        vscode.window.showInformationMessage(
          "Successfully authenticated with GitHub"
        );
        this._onDidChangeIssues.fire();
        return true;
      } catch (error) {
        vscode.window.showErrorMessage(
          `Failed to authenticate: ${(error as Error).message}`
        );
        this.octokit = undefined;
        return false;
      }
    }
    return false;
  }

  public async getRepoInfo(): Promise<
    { owner: string; repo: string } | undefined
  > {
    try {
      const workspaceFolders = vscode.workspace.workspaceFolders;
      if (!workspaceFolders || workspaceFolders.length === 0) {
        return undefined;
      }

      const git: SimpleGit = simpleGit(workspaceFolders[0].uri.fsPath);

      // Check if git repository exists
      const isRepo = await git.checkIsRepo();
      if (!isRepo) {
        vscode.window.showErrorMessage(
          "Not a git repository. CodeMedic requires a git repository connected to GitHub."
        );
        return undefined;
      }

      // Get remote URL
      const remotes = await git.getRemotes(true);
      const origin = remotes.find(
        (remote: { name: string }) => remote.name === "origin"
      );

      if (!origin || !origin.refs.fetch) {
        vscode.window.showErrorMessage(
          "No GitHub remote repository found. CodeMedic requires a GitHub remote repository."
        );
        return undefined;
      }

      // Parse GitHub URL to extract owner and repo
      const url = origin.refs.fetch;
      const regex = /github\.com[:/]([^/]+)\/([^/\.]+)(?:\.git)?$/;
      const match = url.match(regex);

      if (!match) {
        vscode.window.showErrorMessage(
          "Remote repository is not hosted on GitHub. CodeMedic requires a GitHub remote repository."
        );
        return undefined;
      }

      return { owner: match[1], repo: match[2] };
    } catch (error) {
      vscode.window.showErrorMessage(
        `Error connecting to repository: ${(error as Error).message}`
      );
      return undefined;
    }
  }

  public async getIssues() {
    if (!this.octokit) {
      vscode.window.showWarningMessage(
        "Not authenticated with GitHub. Please authenticate first."
      );
      return [];
    }

    const repoInfo = await this.getRepoInfo();
    if (!repoInfo) {
      return [];
    }

    try {
      const { data } = await this.octokit.issues.listForRepo({
        owner: repoInfo.owner,
        repo: repoInfo.repo,
        state: "open",
      });

      // Filter out pull requests (which GitHub API treats as issues)
      return data.filter((issue) => !("pull_request" in issue));
    } catch (error) {
      vscode.window.showErrorMessage(
        `Failed to fetch issues: ${(error as Error).message}`
      );
      return [];
    }
  }
}
