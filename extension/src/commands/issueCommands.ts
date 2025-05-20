import * as vscode from 'vscode';
import * as path from 'path';
import { GitHubIssue } from '../models/issue';
import { getIssueHtml } from '../utils/htmlTemplates';
import { AgentResponseProvider } from '../providers/agentResponseProvider';
import { AgentService } from '../services/agentService';
import { GitHubService } from '../services/githubService';
import { ISSUES_VIEW_ID } from '../utils/constants';

export function registerIssueCommands(
    context: vscode.ExtensionContext,
    issueProvider: any,
    agentResponseProvider: AgentResponseProvider,
    githubService: GitHubService,
    agentService: AgentService
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
                    showIssuePanel(issueItem.issue, context, agentResponseProvider);
                } else {
                    vscode.window.showErrorMessage("Please select a valid GitHub issue.");
                }
            }
        )
    );

    // Command to fix an issue using the agent
    context.subscriptions.push(
        vscode.commands.registerCommand(
            'codemedic.fixIssue',
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
                    await fixIssue(issueItem.issue, undefined, agentResponseProvider, githubService, agentService);
                } else {
                    vscode.window.showErrorMessage("Please select a valid GitHub issue.");
                }
            }
        )
    );
}

function showIssuePanel(issue: GitHubIssue, context: vscode.ExtensionContext, agentResponseProvider: AgentResponseProvider) {
    const panel = vscode.window.createWebviewPanel(
        "issuePanel",
        `Issue #${issue.number}: ${issue.title}`,
        vscode.ViewColumn.Beside,
        { 
            enableScripts: true,
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
            if (message.command === "fixIssue") {
                // Pass both the webview and agent response provider
                await fixIssue(issue, panel.webview, agentResponseProvider);
            }
        },
        undefined,
        context.subscriptions
    );
}

async function fixIssue(
    issue: GitHubIssue, 
    webview?: vscode.Webview, 
    agentResponseProvider?: AgentResponseProvider,
    githubService?: GitHubService,
    agentService?: AgentService
): Promise<void> {
    try {
        if (!githubService || !agentService) {
            throw new Error('GitHub service or Agent service not initialized');
        }

        const githubCredentials = githubService.getCredentials();
        const response = await agentService.fixIssue(issue, githubCredentials);

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
        vscode.window.showErrorMessage(`Error fixing issue: ${error}`);
    }
} 