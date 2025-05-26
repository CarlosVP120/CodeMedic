import * as vscode from 'vscode';

export interface GitHubIssue {
    number: number;
    title: string;
    body: string;
    state: string;
    created_at: string;
    updated_at: string;
    user: {
        login: string;
    } | null;
    labels: Array<{
        name: string;
    }>;
}

export interface GitHubCredentials {
    token: string;
    repository_name: string;
}

export class IssueItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly description: string,
        public readonly issue: GitHubIssue
    ) {
        super(label, vscode.TreeItemCollapsibleState.None);
        this.tooltip = `${this.label} - ${this.description}`;
        this.contextValue = 'issue';
        this.command = {
            command: 'codemedic.showIssuePanel',
            title: 'Show Issue Details',
            arguments: [this]
        };
    }
}

export interface FixCodeRequest {
    github_credentials: GitHubCredentials;
    issue_data: GitHubIssue;
} 