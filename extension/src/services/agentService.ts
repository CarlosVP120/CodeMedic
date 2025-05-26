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
                    user: issue.user || { login: '' },
                    labels: issue.labels || []
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
                    // Send the issue to the API with streaming response
                    const response = await axios.post(API_FIX_ISSUE_ENDPOINT, fixCodeRequest, {
                        responseType: 'stream',
                        timeout: 300000 // 5 minutes timeout
                    });

                    let responseData = '';
                    
                    // Handle streaming response
                    for await (const chunk of response.data) {
                        const text = chunk.toString();
                        responseData += text;
                        
                        // Update progress with current status
                        progress.report({ 
                            message: "Processing issue...",
                            increment: 10
                        });
                    }

                    progress.report({ message: "Issue processed by agent", increment: 100 });

                    // Show success message
                    vscode.window.showInformationMessage(
                        `Issue #${issue.number} has been processed by the agent.`
                    );

                    try {
                        // Try to parse the response as JSON
                        const parsedResponse = JSON.parse(responseData);
                        return {
                            result: 'complete',
                            details: parsedResponse.details || responseData
                        };
                    } catch (parseError) {
                        // If parsing fails, return the raw response
                        return {
                            result: 'complete',
                            details: responseData
                        };
                    }
                } catch (error: any) {
                    console.error('Error in fixIssue:', error);
                    
                    // Handle different types of errors
                    if (error.response) {
                        // The request was made and the server responded with a status code
                        // that falls out of the range of 2xx
                        const errorMessage = error.response.data?.message || error.response.statusText || 'Unknown error';
                        vscode.window.showErrorMessage(`Server error: ${errorMessage}`);
                        return {
                            result: 'error',
                            details: `Server error: ${errorMessage}`,
                            error: errorMessage
                        };
                    } else if (error.request) {
                        // The request was made but no response was received
                        vscode.window.showErrorMessage('No response from server. Please check if the server is running.');
                        return {
                            result: 'error',
                            details: 'No response from server. Please check if the server is running.',
                            error: 'Server not responding'
                        };
                    } else {
                        // Something happened in setting up the request that triggered an Error
                        vscode.window.showErrorMessage(`Error: ${error.message}`);
                        return {
                            result: 'error',
                            details: error.message,
                            error: error.message
                        };
                    }
                }
            });
        } catch (error: any) {
            console.error('Error in fixIssue:', error);
            vscode.window.showErrorMessage(`Error fixing issue: ${error.message || error}`);
            return {
                result: 'error',
                details: error.message || 'Unknown error occurred',
                error: error.message || 'Unknown error'
            };
        }
    }
} 