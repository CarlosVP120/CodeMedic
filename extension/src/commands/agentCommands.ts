import * as vscode from 'vscode';
import { AgentResponseItem } from '../models/agentResponse';
import { getAgentResponseHtml } from '../utils/htmlTemplates';
import * as path from 'path';

export function registerAgentCommands(
    context: vscode.ExtensionContext,
    agentResponseProvider: any
): void {
    // Command to show agent response
    context.subscriptions.push(
        vscode.commands.registerCommand("codemedic.showAgentResponse", (item: AgentResponseItem) => {
            if (item && item.response) {
                const panel = vscode.window.createWebviewPanel(
                    "agentResponseDetail",
                    item.label,
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
                
                // Create a more detailed HTML view that includes the agent output
                const responseHtml = getAgentResponseHtml(item.label, {
                    ...item.response,
                    agent_output: item.agentOutput
                }, logoUri.toString());
                
                panel.webview.html = responseHtml;
            }
        })
    );

    // Command to clear agent responses
    context.subscriptions.push(
        vscode.commands.registerCommand("codemedic.clearResponses", () => {
            agentResponseProvider.clearResponses();
        })
    );
} 