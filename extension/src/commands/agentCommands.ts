import * as vscode from 'vscode';
import * as path from 'path';
import { AgentResponseItem } from '../models/agentResponse';
import { getAgentResponseHtml } from '../utils/htmlTemplates';

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
                
                // Get the logo path and convert it to a webview URI
                const logoPath = vscode.Uri.file(path.join(context.extensionPath, 'resources', 'logo.png'));
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

    // Command to show agent logo (just for UI, shows info about CodeMedic)
    context.subscriptions.push(
        vscode.commands.registerCommand("codemedic.showAgentLogo", () => {
            vscode.window.showInformationMessage('CodeMedic Agent - AI-powered issue resolution for your GitHub repositories');
        })
    );
} 