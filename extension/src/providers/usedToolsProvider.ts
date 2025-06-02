import * as vscode from 'vscode';
import { GitHubIssue } from '../models/issue';

export interface ToolUsage {
    issueNumber: number;
    issueTitle: string;
    toolPath: string[];
    timestamp: Date;
}

export class UsedToolItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly toolUsage: ToolUsage,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly isToolName?: boolean
    ) {
        super(label, collapsibleState);
        
        if (isToolName) {
            this.tooltip = `Tool: ${label}`;
            this.iconPath = new vscode.ThemeIcon('tools');
            this.description = '';
            this.contextValue = 'usedTool';
        } else {
            this.tooltip = `Issue #${toolUsage.issueNumber}: ${toolUsage.issueTitle}`;
            this.iconPath = new vscode.ThemeIcon('bug');
            this.description = `Tools: ${toolUsage.toolPath.length}`;
            this.contextValue = 'issueWithTools';
        }
    }
}

export class UsedToolsProvider implements vscode.TreeDataProvider<UsedToolItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<UsedToolItem | undefined | null | void> = new vscode.EventEmitter<UsedToolItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<UsedToolItem | undefined | null | void> = this._onDidChangeTreeData.event;
    
    private toolUsages: ToolUsage[] = [];
    
    constructor() {}
    
    getTreeItem(element: UsedToolItem): vscode.TreeItem {
        return element;
    }
    
    getChildren(element?: UsedToolItem): UsedToolItem[] {
        if (element && !element.isToolName) {
            // Return tools for this issue
            return element.toolUsage.toolPath.map(tool => 
                new UsedToolItem(
                    tool,
                    element.toolUsage,
                    vscode.TreeItemCollapsibleState.None,
                    true
                )
            );
        } else if (!element) {
            // Return root items (issues)
            return this.toolUsages.map(usage => 
                new UsedToolItem(
                    `Issue #${usage.issueNumber}: ${usage.issueTitle}`,
                    usage,
                    vscode.TreeItemCollapsibleState.Collapsed,
                    false
                )
            );
        }
        return [];
    }
    
    addToolUsage(issue: GitHubIssue, toolPath: string[]): void {
        const existingIndex = this.toolUsages.findIndex(usage => usage.issueNumber === issue.number);
        
        const newUsage: ToolUsage = {
            issueNumber: issue.number,
            issueTitle: issue.title,
            toolPath: toolPath,
            timestamp: new Date()
        };
        
        if (existingIndex >= 0) {
            // Update existing usage
            this.toolUsages[existingIndex] = newUsage;
        } else {
            // Add new usage
            this.toolUsages.push(newUsage);
        }
        
        this._onDidChangeTreeData.fire();
    }
    
    clear(): void {
        this.toolUsages = [];
        this._onDidChangeTreeData.fire();
    }
    
    getToolUsages(): ToolUsage[] {
        return this.toolUsages;
    }
} 