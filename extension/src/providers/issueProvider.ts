import * as vscode from 'vscode';
import { GitHubIssue, IssueItem } from '../models/issue';
import { GitHubService } from '../services/githubService';

export class IssueProvider implements vscode.TreeDataProvider<IssueItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<IssueItem | undefined | null | void> = new vscode.EventEmitter<IssueItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<IssueItem | undefined | null | void> = this._onDidChangeTreeData.event;

    constructor(private githubService: GitHubService) {}

    getTreeItem(element: IssueItem): vscode.TreeItem {
        return element;
    }

    async getChildren(element?: IssueItem): Promise<IssueItem[]> {
        if (element) {
            return [];
        }

        try {
            // First check if we have a GitHub repository
            const repoInfo = await this.githubService.getRepoInfo();
            if (!repoInfo) {
                return [this.createInfoItem(
                    "No GitHub Repository",
                    "Open a project with a GitHub remote repository to use CodeMedic",
                    "folder-opened"
                )];
            }

            // Check if authenticated
            if (!this.githubService.isAuthenticated()) {
                return [this.createActionItem(
                    "🔐 Authenticate with GitHub",
                    "Click here to authenticate with your GitHub account",
                    "codemedic.authenticate",
                    "key"
                )];
            }

            // Get issues
            const issues = await this.githubService.getIssues();
            
            if (issues.length === 0) {
                return [this.createInfoItem(
                    "🎉 No Issues Found",
                    "Great! No open issues in this repository",
                    "check"
                )];
            }

            return issues.map(issue => {
                const label = `#${issue.number}: ${issue.title}`;
                const description = issue.state;
                const item = new IssueItem(label, description, issue);
                
                item.command = {
                    command: 'codemedic.showIssuePanel',
                    title: 'Show Issue Details',
                    arguments: [item]
                };

                item.iconPath = new vscode.ThemeIcon('beaker');
                
                return item;
            });
        } catch (error) {
            console.error('Error getting issues:', error);
            return [this.createInfoItem(
                "❌ Error Loading Issues",
                `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
                "error"
            )];
        }
    }

    private createActionItem(title: string, description: string, command: string, icon: string): IssueItem {
        const item = new IssueItem(title, description, {} as GitHubIssue);
        item.command = {
            command: command,
            title: title
        };
        item.iconPath = new vscode.ThemeIcon(icon);
        item.contextValue = "action";
        return item;
    }

    private createInfoItem(title: string, description: string, icon: string): IssueItem {
        const item = new IssueItem(title, description, {} as GitHubIssue);
        item.iconPath = new vscode.ThemeIcon(icon);
        item.contextValue = "info";
        return item;
    }

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }
} 