export interface StructuredAgentResponse {
    summary: string;
    solution?: string;
    files_modified?: string[];
    pull_request_url?: string;
    branch_name?: string;
    errors?: string[];
    status: 'success' | 'error' | 'partial';
    next_steps?: string[];
}

export interface AgentStepResponse {
    step: string;
    status: 'in_progress' | 'completed' | 'failed';
    details?: string;
}

export interface StreamedResponse {
    type: 'status' | 'final_response';
    data: AgentStepResponse | StructuredAgentResponse;
}

export class StructuredAgentResponseParser {
    static parseStreamedResponse(jsonString: string): StreamedResponse | null {
        try {
            const response = JSON.parse(jsonString);
            
            // Validate the response structure
            if (!response.type || !response.data) {
                console.warn('Invalid response structure:', response);
                return null;
            }

            // Validate response type
            if (!['status', 'final_response'].includes(response.type)) {
                console.warn('Invalid response type:', response.type);
                return null;
            }

            return response as StreamedResponse;
        } catch (error) {
            console.error('Error parsing streamed response:', error);
            return null;
        }
    }

    static formatStructuredResponse(response: StructuredAgentResponse): string {
        let formatted = '';
        
        // Status indicator
        const statusIcon = response.status === 'success' ? '✅' : 
                          response.status === 'error' ? '❌' : '⚠️';
        
        // Summary
        formatted += `${statusIcon} **Status**: ${response.status.toUpperCase()}\n\n`;
        formatted += `📋 **Summary**: ${response.summary}\n\n`;
        
        // Solution
        if (response.solution) {
            formatted += `🔧 **Solution**:\n${response.solution}\n\n`;
        }
        
        // Files modified
        if (response.files_modified && response.files_modified.length > 0) {
            formatted += `📁 **Files Modified**:\n`;
            response.files_modified.forEach(file => {
                formatted += `  • ${file}\n`;
            });
            formatted += '\n';
        }
        
        // Pull Request
        if (response.pull_request_url) {
            formatted += `🔗 **Pull Request**: [View PR](${response.pull_request_url})\n\n`;
        }
        
        // Branch
        if (response.branch_name) {
            formatted += `🌿 **Branch**: ${response.branch_name}\n\n`;
        }
        
        // Next steps
        if (response.next_steps && response.next_steps.length > 0) {
            formatted += `📝 **Next Steps**:\n`;
            response.next_steps.forEach((step, index) => {
                formatted += `  ${index + 1}. ${step}\n`;
            });
            formatted += '\n';
        }
        
        // Errors
        if (response.errors && response.errors.length > 0) {
            formatted += `❌ **Errors**:\n`;
            response.errors.forEach(error => {
                formatted += `  • ${error}\n`;
            });
            formatted += '\n';
        }
        
        return formatted.trim();
    }

    static formatStepResponse(response: AgentStepResponse): string {
        const statusIcon = response.status === 'completed' ? '✅' : 
                          response.status === 'failed' ? '❌' : '🔄';
        
        let formatted = `${statusIcon} ${response.step}`;
        
        if (response.details) {
            formatted += `\n   ${response.details}`;
        }
        
        return formatted;
    }

    static isStructuredResponse(data: any): data is StructuredAgentResponse {
        return data && 
               typeof data.summary === 'string' && 
               ['success', 'error', 'partial'].includes(data.status);
    }

    static isStepResponse(data: any): data is AgentStepResponse {
        return data && 
               typeof data.step === 'string' && 
               ['in_progress', 'completed', 'failed'].includes(data.status);
    }
} 