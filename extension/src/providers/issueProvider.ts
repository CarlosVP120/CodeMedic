import * as vscode from 'vscode';
import { GitHubService } from '../services/githubService';
import { GitHubIssue, IssueItem } from '../models/issue';

export class IssueProvider implements vscode.TreeDataProvider<IssueItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<IssueItem | undefined | null | void> = new vscode.EventEmitter<IssueItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<IssueItem | undefined | null | void> = this._onDidChangeTreeData.event;

    private issues: IssueItem[] = [];

    constructor(private githubService: GitHubService) {
        // Initial refresh
        this.refresh();
    }

    getTreeItem(element: IssueItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: IssueItem): Thenable<IssueItem[]> {
        if (element) {
            return Promise.resolve([]);
        }
        return Promise.resolve(this.issues);
    }

    async refresh(): Promise<void> {
        try {
            console.log('Refreshing issues...');
            // Get repository information
            const repoInfo = await this.githubService.getRepoInfo();
            if (!repoInfo) {
                console.log('No repository info available');
                return;
            }

            // Get issues from GitHub
            const issues = await this.githubService.getIssues();
            console.log(`Retrieved ${issues.length} issues`);
            
            // Convert GitHub issues to tree items
            this.issues = issues.map(issue => {
                const label = `#${issue.number}: ${issue.title}`;
                const description = issue.state;
                const item = new IssueItem(label, description, issue);

                // Set icons based on issue labels
                if (issue.labels && issue.labels.length > 0) {
                    // Check for bug label
                    if (issue.labels.some(label => label.name.toLowerCase().includes('bug'))) {
                        item.iconPath = new vscode.ThemeIcon('bug');
                    } else if (issue.labels.some(label => label.name.toLowerCase().includes('feature'))) {
                        item.iconPath = new vscode.ThemeIcon('lightbulb');
                    } else {
                        item.iconPath = new vscode.ThemeIcon('issues');
                    }
                } else {
                    item.iconPath = new vscode.ThemeIcon('issues');
                }

                return item;
            });

            // Notify that the tree data has changed
            this._onDidChangeTreeData.fire();
            console.log('Issues refreshed successfully');
        } catch (error) {
            console.error('Error refreshing issues:', error);
            vscode.window.showErrorMessage(`Failed to refresh issues: ${error}`);
        }
    }
} 