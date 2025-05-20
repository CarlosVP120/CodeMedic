import * as vscode from 'vscode';
import { AgentResponseItem } from '../models/agentResponse';
import { GitHubIssue } from '../models/issue';

export class AgentResponseProvider implements vscode.TreeDataProvider<AgentResponseItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<AgentResponseItem | undefined | null | void> = new vscode.EventEmitter<AgentResponseItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<AgentResponseItem | undefined | null | void> = this._onDidChangeTreeData.event;
    
    private responses: AgentResponseItem[] = [];
    
    constructor() {}
    
    getTreeItem(element: AgentResponseItem): vscode.TreeItem {
        return element;
    }
    
    getChildren(element?: AgentResponseItem): Thenable<AgentResponseItem[]> {
        if (element) {
            return Promise.resolve([]);
        }
        return Promise.resolve(this.responses);
    }
    
    addResponse(issue: GitHubIssue, response: any): void {
        // Create a more descriptive label that includes the issue title
        const label = `Issue #${issue.number}: ${issue.title}`;
        
        // Extract status and agent output (if available)
        const status = response.result || 'Processing complete';
        const agentOutput = response.agent_output || '';
        
        // Create a description that includes status
        const description = `${status} - ${new Date().toLocaleString()}`;
        
        const item = new AgentResponseItem(
            label,
            response,
            description,
            agentOutput,
            vscode.TreeItemCollapsibleState.None
        );
        
        this.responses.unshift(item); // Add new responses at the top
        this._onDidChangeTreeData.fire();
    }
    
    clearResponses(): void {
        this.responses = [];
        this._onDidChangeTreeData.fire();
    }
} 