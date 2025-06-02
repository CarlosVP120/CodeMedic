import * as vscode from 'vscode';
import axios from 'axios';
import { GitHubIssue, FixCodeRequest } from '../models/issue';
import { AgentResponse } from '../models/agentResponse';
import { API_FIX_ISSUE_STRUCTURED_ENDPOINT } from '../utils/constants';
import { 
    StructuredAgentResponseParser, 
    StructuredAgentResponse, 
    AgentStepResponse, 
} from '../utils/structuredAgentResponseParser';

export class StructuredAgentService {
    async fixIssue(issue: GitHubIssue, githubCredentials: { token: string; repository_name: string }): Promise<AgentResponse> {
        try {
            vscode.window.showInformationMessage(`Starting to fix issue #${issue.number} the agent...`);

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
                progress.report({ message: "Connecting to CodeMedic agent..." });

                try {
                    // Send the issue to the structured API with regular JSON response
                    const response = await axios.post(API_FIX_ISSUE_STRUCTURED_ENDPOINT, fixCodeRequest, {
                        timeout: 300000, // 5 minutes timeout
                        headers: {
                            'Content-Type': 'application/json',
                            'Accept': 'application/json'
                        }
                    });

                    progress.report({ message: "Processing completed", increment: 100 });

                    // Handle the response data directly
                    const responseData = response.data;
                    console.log('Response received:', responseData);

                    // Show success message
                    vscode.window.showInformationMessage(
                        `Issue #${issue.number} has been processed by the agent.`
                    );

                    // Format the response from Modal's structure {status, data}
                    if (responseData && responseData.status === 'success' && responseData.data) {
                        const agentData = responseData.data;
                        
                        if (agentData.messages && agentData.summary) {
                            return {
                                result: 'complete',
                                details: this.formatFinalAgentOutput(agentData),
                                structuredData: agentData,
                                agentMessages: agentData.messages,
                                agentSummary: agentData.summary,
                                tool_path: agentData.tool_path || []
                            } as AgentResponse;
                        } else {
                            return {
                                result: 'error',
                                details: 'Invalid agent response format - missing messages or summary',
                                error: 'Invalid agent response format'
                            };
                        }
                    } else if (responseData && responseData.status === 'error') {
                        return {
                            result: 'error',
                            details: `Agent error: ${responseData.detail || 'Unknown error'}`,
                            error: responseData.detail || 'Unknown error'
                        };
                    } else {
                        return {
                            result: 'error',
                            details: 'Invalid response format received from Modal API',
                            error: 'Invalid response format'
                        };
                    }
                } catch (error: any) {
                    console.error('Error in structured fixIssue:', error);
                    
                    // Handle different types of errors
                    if (error.response) {
                        const errorMessage = error.response.data?.message || error.response.statusText || 'Unknown error';
                        vscode.window.showErrorMessage(`Server error: ${errorMessage}`);
                        return {
                            result: 'error',
                            details: `Server error: ${errorMessage}`,
                            error: errorMessage
                        };
                    } else if (error.request) {
                        vscode.window.showErrorMessage('No response from structured agent server. Please check if the server is running.');
                        return {
                            result: 'error',
                            details: 'No response from structured agent server. Please check if the server is running.',
                            error: 'Server not responding'
                        };
                    } else {
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
            console.error('Error in structured fixIssue:', error);
            vscode.window.showErrorMessage(`Error fixing issue: ${error.message || error}`);
            return {
                result: 'error',
                details: error.message || 'Unknown error occurred',
                error: error.message || 'Unknown error'
            };
        }
    }
    
    private formatStructuredResponse(response: StructuredAgentResponse, stepUpdates: string[]): string {
        // Return only the structured response without process steps
        return StructuredAgentResponseParser.formatStructuredResponse(response);
    }
    
    private formatStepUpdates(stepUpdates: string[]): string {
        if (stepUpdates.length === 0) {
            return 'Processing completed. No detailed steps available.';
        }
        
        // Return a generic message instead of showing process steps
        return 'Issue processing completed successfully.';
    }

    private formatFinalAgentOutput(responseData: any): string {
        // Format the FinalAgentOutput response from the server into a readable format
        const { messages, summary } = responseData;
        
        let formattedOutput = '';
        
        // Add summary at the top
        if (summary) {
            formattedOutput += `## Summary\n${summary}\n\n`;
        }
        
        // Add detailed messages if available
        if (messages && Array.isArray(messages) && messages.length > 0) {
            formattedOutput += `## Agent Messages\n\n`;
            
            messages.forEach((message: string, index: number) => {
                // Skip the summary message if it's the last one and matches the summary
                if (index === messages.length - 1 && message === summary) {
                    return;
                }
                
                formattedOutput += `**Step ${index + 1}:**\n${message}\n\n`;
            });
        }
        
        // If no detailed messages, just show the summary
        if (!messages || messages.length === 0) {
            formattedOutput = summary || 'No response details available.';
        }
        
        return formattedOutput.trim();
    }
} 