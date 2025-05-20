import * as vscode from 'vscode';
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
                    { enableScripts: true }
                );
                
                // Create a more detailed HTML view that includes the agent output
                const responseHtml = getAgentResponseHtml(item.label, {
                    ...item.response,
                    agent_output: item.agentOutput
                });
                
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