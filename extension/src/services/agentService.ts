import * as vscode from 'vscode';
import axios from 'axios';
import { GitHubIssue, FixCodeRequest } from '../models/issue';
import { AgentResponse } from '../models/agentResponse';
import { API_FIX_ISSUE_ENDPOINT } from '../utils/constants';

export class AgentService {
    async fixIssue(issue: GitHubIssue, githubCredentials: { token: string; repository_name: string }): Promise<AgentResponse> {
        try {
            vscode.window.showInformationMessage(`Starting to fix issue #${issue.number}...`);

            const fixCodeRequest: FixCodeRequest = {
                github_credentials: githubCredentials,
                issue_data: {
                    number: issue.number,
                    title: issue.title,
                    body: issue.body || "",
                    state: issue.state,
                    created_at: issue.created_at,
                    updated_at: issue.updated_at,
                    user: {
                        login: '',
                    },
                    labels: []
                }
            };

            // Configure progress notification
            return await vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: `Fixing issue #${issue.number}`,
                cancellable: false
            }, async (progress) => {
                progress.report({ message: "Sending issue to CodeMedic agent..." });

                try {
                    // Send the issue to the API
                    const response = await axios.post(API_FIX_ISSUE_ENDPOINT, fixCodeRequest);

                    progress.report({ message: "Issue processed by agent", increment: 100 });

                    // Show success message
                    vscode.window.showInformationMessage(
                        `Issue #${issue.number} has been processed by the agent.`
                    );

                    return response.data;
                } catch (error) {
                    vscode.window.showErrorMessage(`Failed to connect to CodeMedic server: ${error}`);
                    throw error;
                }
            });
        } catch (error) {
            vscode.window.showErrorMessage(`Error fixing issue: ${error}`);
            throw error;
        }
    }
} 