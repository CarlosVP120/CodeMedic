import * as vscode from 'vscode';
import { GitHubIssue } from '../models/issue';
import { AgentResponse } from '../models/agentResponse';

export class AgentResponseItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly response: AgentResponse,
        public readonly issue: GitHubIssue
    ) {
        super(label, vscode.TreeItemCollapsibleState.None);
        this.tooltip = this.response.details;
        this.contextValue = 'agentResponse';
        this.command = {
            command: 'codemedic.showAgentResponse',
            title: 'Show Agent Response',
            arguments: [this]
        };
    }
}

export class AgentResponseProvider implements vscode.TreeDataProvider<AgentResponseItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<AgentResponseItem | undefined | null | void> = new vscode.EventEmitter<AgentResponseItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<AgentResponseItem | undefined | null | void> = this._onDidChangeTreeData.event;
    
    private responses: AgentResponseItem[] = [];
    
    constructor() {}
    
    getTreeItem(element: AgentResponseItem): vscode.TreeItem {
        return element;
    }
    
    getChildren(element?: AgentResponseItem): AgentResponseItem[] {
        if (element) {
            return [];
        }
        return this.responses;
    }
    
    addResponse(issue: GitHubIssue, response: AgentResponse): void {
        const label = `Issue #${issue.number}: ${issue.title}`;
        const item = new AgentResponseItem(label, response, issue);
        this.responses.push(item);
        this._onDidChangeTreeData.fire();
    }
    
    clear(): void {
        this.responses = [];
        this._onDidChangeTreeData.fire();
    }
} 