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
            const issues = await this.githubService.getIssues();
            return issues.map(issue => {
                const label = `#${issue.number}: ${issue.title}`;
                const description = issue.state;
                const item = new IssueItem(label, description, issue);
                
                // Keep the original showIssuePanel command
                item.command = {
                    command: 'codemedic.showIssuePanel',
                    title: 'Show Issue Details',
                    arguments: [item]
                };

                // Add laboratory icon
                item.iconPath = new vscode.ThemeIcon('beaker');
                
                return item;
            });
        } catch (error) {
            console.error('Error getting issues:', error);
            return [];
        }
    }

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }
} 