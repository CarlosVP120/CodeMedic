import * as vscode from 'vscode';
import { ParsedAgentResponse } from '../utils/agentResponseParser';
import { StructuredAgentResponse } from '../utils/structuredAgentResponseParser';

export interface AgentResponse {
    result: 'processing' | 'complete' | 'error' | 'partial';
    details: string;
    error?: string;
    parsedData?: ParsedAgentResponse;
    structuredData?: StructuredAgentResponse | any;
    agentMessages?: string[];
    agentSummary?: string;
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