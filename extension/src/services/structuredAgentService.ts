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
                    // Send the issue to the structured API with streaming response
                    const response = await axios.post(API_FIX_ISSUE_STRUCTURED_ENDPOINT, fixCodeRequest, {
                        responseType: 'stream',
                        timeout: 300000, // 5 minutes timeout
                        headers: {
                            'Accept': 'text/event-stream',
                            'Cache-Control': 'no-cache'
                        }
                    });

                    let finalResponse: StructuredAgentResponse | null = null;
                    const stepUpdates: string[] = [];
                    
                    // Handle Server-Sent Events streaming response
                    for await (const chunk of response.data) {
                        const text = chunk.toString();
                        
                        // Parse SSE format (data: {...})
                        const lines = text.split('\n');
                        for (const line of lines) {
                            if (line.startsWith('data: ')) {
                                const jsonData = line.substring(6); // Remove 'data: ' prefix
                                
                                if (jsonData.trim()) {
                                    const parsedResponse = StructuredAgentResponseParser.parseStreamedResponse(jsonData);
                                    
                                    if (parsedResponse) {
                                        if (parsedResponse.type === 'status') {
                                            // Handle step updates
                                            const stepData = parsedResponse.data as AgentStepResponse;
                                            const stepMessage = StructuredAgentResponseParser.formatStepResponse(stepData);
                                            stepUpdates.push(stepMessage);
                                            
                                            progress.report({ 
                                                message: stepData.step,
                                                increment: 10
                                            });
                                            
                                            console.log('Step update:', stepMessage);
                                            
                                        } else if (parsedResponse.type === 'final_response') {
                                            // Handle final response
                                            finalResponse = parsedResponse.data as StructuredAgentResponse;
                                            console.log('Final structured response received:', finalResponse);
                                        }
                                    }
                                }
                            }
                        }
                    }

                    progress.report({ message: "Processing completed", increment: 100 });

                    // Show success message
                    const statusMessage = finalResponse?.status === 'success' ? 'successfully processed' :
                                         finalResponse?.status === 'error' ? 'processed with errors' :
                                         'partially processed';
                    
                    vscode.window.showInformationMessage(
                        `Issue #${issue.number} has been ${statusMessage} by the structured agent.`
                    );

                    // Format the response
                    if (finalResponse) {
                        const formattedDetails = this.formatStructuredResponse(finalResponse, stepUpdates);
                        
                        return {
                            result: finalResponse.status === 'error' ? 'error' : 'complete',
                            details: formattedDetails,
                            structuredData: finalResponse // Include structured data for advanced usage
                        };
                    } else {
                        // Fallback if no final response was received
                        return {
                            result: 'partial',
                            details: this.formatStepUpdates(stepUpdates),
                            error: 'No final response received from agent'
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
} 