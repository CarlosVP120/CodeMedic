import * as vscode from "vscode";
import { GitHubIssue, GitHubCredentials } from "../models/issue";
import { Octokit } from "@octokit/rest";
import simpleGit, { SimpleGit } from "simple-git";

export class GitHubService {
  private context: vscode.ExtensionContext;
  private octokit: Octokit | undefined;
  private _onDidChangeIssues = new vscode.EventEmitter<void>();
  readonly onDidChangeIssues = this._onDidChangeIssues.event;

  constructor(context: vscode.ExtensionContext) {
    this.context = context;
    this.initializeOctokit();
  }

  private initializeOctokit() {
    const token = this.context.globalState.get<string>("githubToken");
    if (token) {
      this.octokit = new Octokit({ auth: token });
    }
  }

  async authenticate(): Promise<void> {
    try {
      console.log("Starting authentication...");

      // Prompt for token
      const token = await vscode.window.showInputBox({
        prompt: "Enter your GitHub Personal Access Token",
        password: true,
        ignoreFocusOut: true,
      });

      if (!token) {
        throw new Error("No token provided");
      }

      this.octokit = new Octokit({ auth: token });

      await this.context.globalState.update("githubToken", token);

      // Test the token by fetching user info
      await this.octokit.users.getAuthenticated();

      vscode.window.showInformationMessage(
        "Successfully authenticated with GitHub"
      );
      this._onDidChangeIssues.fire();
    } catch (error) {
      console.error("Authentication failed:", error);
      vscode.window.showErrorMessage(
        `Failed to authenticate with GitHub: ${error}`
      );
      this.octokit = undefined;
      throw error;
    }
  }

  isAuthenticated(): boolean {
    return !!this.octokit;
  }

  async getRepoInfo(): Promise<{ owner: string; repo: string } | null> {
    try {
      const workspaceFolders = vscode.workspace.workspaceFolders;
      if (!workspaceFolders || workspaceFolders.length === 0) {
        return null;
      }

      const git: SimpleGit = simpleGit(workspaceFolders[0].uri.fsPath);

      // Check if git repository exists
      const isRepo = await git.checkIsRepo();
      if (!isRepo) {
        vscode.window.showErrorMessage(
          "Not a git repository. CodeMedic requires a git repository connected to GitHub."
        );
        return null;
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
        return null;
      }

      // Parse GitHub URL to extract owner and repo
      const url = origin.refs.fetch;
      const regex = /github\.com[:/]([^/]+)\/([^/\.]+)(?:\.git)?$/;
      const match = url.match(regex);

      if (!match) {
        vscode.window.showErrorMessage(
          "Remote repository is not hosted on GitHub. CodeMedic requires a GitHub remote repository."
        );
        return null;
      }

      console.log("Repository info:", { owner: match[1], repo: match[2] });
      return { owner: match[1], repo: match[2] };
    } catch (error) {
      console.error("Error getting repository info:", error);
      vscode.window.showErrorMessage(
        `Error connecting to repository: ${(error as Error).message}`
      );
      return null;
    }
  }

  async getCredentials(): Promise<GitHubCredentials> {
    try {
      if (!this.octokit) {
        console.log("Credentials not configured");
        throw new Error("GitHub credentials not configured");
      }

      const token = this.context.globalState.get<string>("githubToken");
      if (!token) {
        throw new Error("GitHub token not found");
      }

      const repoInfo = await this.getRepoInfo();
      if (!repoInfo) {
        throw new Error("Repository information not found");
      }

      return {
        token: token,
        repository_name: `${repoInfo.owner}/${repoInfo.repo}`,
      };
    } catch (error) {
      console.error("Error getting credentials:", error);
      throw error;
    }
  }

  async getIssues(): Promise<GitHubIssue[]> {
    try {
      console.log("Getting issues...");
      if (!this.octokit) {
        console.log("No Octokit instance available - not authenticated");
        // Don't show error message here, let the IssueProvider handle the UI
        return [];
      }

      const repoInfo = await this.getRepoInfo();
      if (!repoInfo) {
        console.log("No repository info available");
        return [];
      }

      console.log("Making API request to get issues with:", {
        owner: repoInfo.owner,
        repo: repoInfo.repo,
      });

      const { data } = await this.octokit.issues.listForRepo({
        owner: repoInfo.owner,
        repo: repoInfo.repo,
        state: "open",
      });

      // Filter out pull requests
      const issues = data.filter((issue) => !("pull_request" in issue));

      console.log("Received response:", {
        issueCount: issues.length,
      });

      return issues.map((issue) => ({
        number: issue.number,
        title: issue.title,
        body: issue.body || "",
        state: issue.state,
        created_at: issue.created_at,
        updated_at: issue.updated_at,
        user: issue.user ? { login: issue.user.login } : null,
        labels: issue.labels.map((label) => ({
          name: typeof label === "string" ? label : label.name || "",
        })),
      }));
    } catch (error: any) {
      console.error("Error fetching issues:", error);
      if (error.response) {
        console.error("Response status:", error.response.status);
        console.error("Response data:", error.response.data);
      }
      
      // Only show error for actual API errors, not authentication issues
      if (this.octokit) {
        vscode.window.showErrorMessage(
          `Failed to fetch issues: ${error.message}`
        );
      }
      return [];
    }
  }
}
