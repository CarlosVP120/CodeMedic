import * as vscode from 'vscode';

export interface AgentResponse {
    result: 'processing' | 'complete' | 'error';
    details: string;
    error?: string;
}

export class AgentResponseItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly response: any,
        public readonly detailsText: string,
        public readonly agentOutput: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState
    ) {
        super(label, collapsibleState);
        this.tooltip = `Agent response for ${label}`;
        this.description = detailsText;
        this.contextValue = 'agentResponse';
        
        // Add a custom icon
        this.iconPath = new vscode.ThemeIcon('rocket');
    }
} 