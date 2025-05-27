import * as vscode from 'vscode';
import * as path from 'path';
import { GitHubIssue } from '../models/issue';
import { getIssueHtml } from '../utils/htmlTemplates';
import { AgentResponseProvider } from '../providers/agentResponseProvider';
import { StructuredAgentService } from '../services/structuredAgentService';
import { GitHubService } from '../services/githubService';
import { ISSUES_VIEW_ID } from '../utils/constants';

export function registerIssueCommands(
    context: vscode.ExtensionContext,
    issueProvider: any,
    agentResponseProvider: AgentResponseProvider,
    githubService: GitHubService
): void {
    // Command to show issue panel
    context.subscriptions.push(
        vscode.commands.registerCommand(
            'codemedic.showIssuePanel',
            async (issueItem) => {                
                if (!issueItem) {
                    const treeView = vscode.window.createTreeView(ISSUES_VIEW_ID, {
                        treeDataProvider: issueProvider
                    });
                    const selectedItem = treeView.selection[0];
                    if (!selectedItem) {
                        vscode.window.showErrorMessage(
                            "No issue selected. Please select an issue first."
                        );
                        return;
                    }
                    issueItem = selectedItem;
                }
                if (issueItem.contextValue === "issue") {
                    console.log('🔧 Opening issue panel for issue:', issueItem.issue.number);
                    showIssuePanel(issueItem.issue, context, agentResponseProvider, githubService);
                } else {
                    vscode.window.showErrorMessage("Please select a valid GitHub issue.");
                }
            }
        )
    );


}

function showIssuePanel(issue: GitHubIssue, context: vscode.ExtensionContext, agentResponseProvider: AgentResponseProvider, githubService: GitHubService) {    
    const panel = vscode.window.createWebviewPanel(
        "issuePanel",
        `Issue #${issue.number}: ${issue.title}`,
        vscode.ViewColumn.Beside,
        { 
            enableScripts: true,
            retainContextWhenHidden: true,
            localResourceRoots: [vscode.Uri.file(path.join(context.extensionPath, 'resources'))]
        }
    );
    
    // Get the path to the logo image
    const logoPath = vscode.Uri.file(
        path.join(context.extensionPath, 'resources', 'logo.png')
    );
    
    // Convert the URI to a string that the webview can use
    const logoUri = panel.webview.asWebviewUri(logoPath);
    
    // Add fix button to the panel
    panel.webview.html = getIssueHtml(issue, logoUri.toString());
    
    // Handle messages from the webview
    panel.webview.onDidReceiveMessage(
        async (message) => {
            if (message.command === "fixIssueStructured") {
                await fixIssueStructured(issue, panel.webview, agentResponseProvider, githubService);
            } else {
                console.log('❓ Unknown command:', message.command);
            }
        },
        undefined,
        context.subscriptions
    );
}

export async function fixIssueStructured(
    issue: GitHubIssue, 
    webview?: vscode.Webview, 
    agentResponseProvider?: AgentResponseProvider,
    githubService?: GitHubService
): Promise<void> {
    try {
        if (!githubService) {
            const errorMsg = 'GitHub service not initialized';
            console.error('❌ Error:', errorMsg);
            throw new Error(errorMsg);
        }
        
        // Get GitHub credentials
        const githubCredentials = await githubService.getCredentials();
        
        // Create structured agent service
        const structuredAgentService = new StructuredAgentService();
        
        // Use the structured agent service to fix the issue
        const response = await structuredAgentService.fixIssue(issue, githubCredentials);

        // If webview is provided, send the response to it
        if (webview) {
            webview.postMessage({
                command: 'agentResponse',
                response: response
            });
        }

        // If agent response provider is provided, add the response to it
        if (agentResponseProvider) {
            agentResponseProvider.addResponse(issue, response);
        }
    } catch (error) {
        vscode.window.showErrorMessage(`Error fixing issue with structured agent: ${error}`);
    }
} 