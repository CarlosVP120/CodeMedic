import * as vscode from 'vscode';
import { GitHubIssue } from '../models/issue';
import { AgentResponse, AgentResponseItem } from '../models/agentResponse';

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
        const detailsText = response.result;
        const agentOutput = response.details;
        
        const item = new AgentResponseItem(
            label,
            response,
            detailsText,
            agentOutput,
            vscode.TreeItemCollapsibleState.None
        );
        
        // Set the command for showing the response
        item.command = {
            command: 'codemedic.showAgentResponse',
            title: 'Show Agent Response',
            arguments: [item]
        };
        
        this.responses.push(item);
        this._onDidChangeTreeData.fire();
    }
    
    clear(): void {
        this.responses = [];
        this._onDidChangeTreeData.fire();
    }
} 