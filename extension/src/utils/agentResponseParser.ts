export interface ParsedAgentResponse {
    summary: string;
    solution?: string;
    filesModified?: string[];
    pullRequestUrl?: string;
    branchName?: string;
    errors?: string[];
    rawContent: string;
    status: 'success' | 'error' | 'partial';
}

export class AgentResponseParser {
    static parse(rawResponse: string): ParsedAgentResponse {
        const result: ParsedAgentResponse = {
            summary: '',
            rawContent: rawResponse,
            status: 'success'
        };

        try {
            // Limpiar la respuesta de caracteres especiales y formatear
            const cleanResponse = this.cleanResponse(rawResponse);
            
            // Intentar parsear como JSON primero
            const jsonResponse = this.tryParseJSON(cleanResponse);
            if (jsonResponse) {
                return this.parseJSONResponse(jsonResponse);
            }

            // Si no es JSON, parsear como texto
            return this.parseTextResponse(cleanResponse);
        } catch (error) {
            console.error('Error parsing agent response:', error);
            return {
                summary: 'Error parsing response',
                rawContent: rawResponse,
                status: 'error',
                errors: [String(error)]
            };
        }
    }

    private static cleanResponse(text: string): string {
        // Remover caracteres de escape y limpiar el texto
        return text
            .replace(/\\n/g, '\n')
            .replace(/\\"/g, '"')
            .replace(/\\'/g, "'")
            .trim();
    }

    private static tryParseJSON(text: string): any | null {
        try {
            return JSON.parse(text);
        } catch {
            // Intentar extraer JSON de texto que puede tener otras cosas
            const jsonMatch = text.match(/\{[\s\S]*\}/);
            if (jsonMatch) {
                try {
                    return JSON.parse(jsonMatch[0]);
                } catch {
                    return null;
                }
            }
            return null;
        }
    }

    private static parseJSONResponse(jsonData: any): ParsedAgentResponse {
        let summary = 'Response processed';
        let solution = '';
        let filesModified: string[] = [];
        let branchName = '';
        let errors: string[] = [];

        // Extraer información de estructuras complejas (LangChain, etc.)
        if (jsonData.agent && jsonData.agent.messages) {
            const messages = jsonData.agent.messages;
            for (const message of messages) {
                if (message.content) {
                    const content = typeof message.content === 'string' ? message.content : JSON.stringify(message.content);
                    
                    // Extraer resumen del primer mensaje
                    if (!summary || summary === 'Response processed') {
                        summary = this.extractSummaryFromContent(content);
                    }
                    
                    // Extraer solución
                    if (!solution) {
                        solution = this.extractSolutionFromContent(content);
                    }
                    
                    // Extraer archivos modificados
                    const files = this.extractFilesFromContent(content);
                    if (files.length > 0) {
                        filesModified = [...filesModified, ...files];
                    }
                    
                    // Extraer nombre de branch
                    if (!branchName) {
                        branchName = this.extractBranchFromContent(content);
                    }
                    
                    // Extraer errores
                    const contentErrors = this.extractErrorsFromContent(content);
                    if (contentErrors.length > 0) {
                        errors = [...errors, ...contentErrors];
                    }
                }
            }
        }

        // Buscar en la sección de tools para URLs de PR
        let pullRequestUrl = '';
        if (jsonData.tools && jsonData.tools.messages) {
            const toolMessages = jsonData.tools.messages;
            for (const toolMessage of toolMessages) {
                if (toolMessage.content && typeof toolMessage.content === 'string') {
                    const prUrl = this.extractPullRequestUrl(toolMessage.content);
                    if (prUrl) {
                        pullRequestUrl = prUrl;
                        break;
                    }
                }
            }
        }

        // Fallback a métodos originales si no se extrajo información
        if (!summary || summary === 'Response processed') {
            summary = jsonData.summary || this.extractSummary(JSON.stringify(jsonData));
        }

        const result: ParsedAgentResponse = {
            summary,
            rawContent: JSON.stringify(jsonData, null, 2),
            status: errors.length > 0 ? 'error' : 'success'
        };

        if (solution) result.solution = solution;
        if (filesModified.length > 0) result.filesModified = [...new Set(filesModified)]; // Remove duplicates
        if (branchName) result.branchName = branchName;
        if (pullRequestUrl) result.pullRequestUrl = pullRequestUrl;
        if (errors.length > 0) result.errors = [...new Set(errors)]; // Remove duplicates

        // Buscar campos estándar también
        if (jsonData.solution) result.solution = jsonData.solution;
        if (jsonData.files_modified || jsonData.filesModified) {
            result.filesModified = jsonData.files_modified || jsonData.filesModified;
        }
        if (jsonData.pull_request_url || jsonData.pullRequestUrl) {
            result.pullRequestUrl = jsonData.pull_request_url || jsonData.pullRequestUrl;
        }
        if (jsonData.branch_name || jsonData.branchName) {
            result.branchName = jsonData.branch_name || jsonData.branchName;
        }

        return result;
    }

    private static extractSummaryFromContent(content: string): string {
        // Buscar líneas que parezcan conclusiones o resultados finales
        const lines = content.split('\n').filter(line => line.trim());
        
        // Buscar patrones de conclusión exitosa
        const successPatterns = [
            /.*(?:fixed|resolved|created|completed|successful).*(?:error|issue|problem|function|file)/i,
            /.*(?:pull request|pr).*(?:created|submitted|opened)/i,
            /.*(?:has been|was).*(?:processed|fixed|updated|created)/i,
            /final answer:\s*(.+)/i
        ];

        for (const pattern of successPatterns) {
            for (const line of lines) {
                const match = line.match(pattern);
                if (match) {
                    const text = match[1] || line;
                    if (text.trim().length > 10 && text.trim().length < 200) {
                        return text.trim().substring(0, 150) + (text.length > 150 ? '...' : '');
                    }
                }
            }
        }
        
        // Buscar líneas que contengan acciones completadas
        const actionPatterns = [
            /(?:added|fixed|modified|updated|corrected).*(?:in|to|for)/i,
            /(?:syntax|error|issue|problem).*(?:resolved|fixed|corrected)/i
        ];

        for (const pattern of actionPatterns) {
            for (const line of lines) {
                if (pattern.test(line) && line.length > 20 && line.length < 200) {
                    return line.trim().substring(0, 150) + (line.length > 150 ? '...' : '');
                }
            }
        }
        
        // Buscar primera línea significativa que no sea fragmento técnico
        for (const line of lines) {
            if (line.length > 30 && 
                line.length < 200 &&
                !line.includes('github_token') &&
                !line.includes('chatcmpl-') &&
                !line.includes('AIMessage') &&
                !line.includes('def ') &&
                !line.match(/^[\{\[]/) && // No empiece con JSON
                line.includes(' ') && // Contenga espacios (oración)
                !line.startsWith('•') && // No sea bullet point
                line.split(' ').length > 3) { // Al menos 4 palabras
                return line.trim().substring(0, 150) + (line.length > 150 ? '...' : '');
            }
        }
        
        return 'Agent completed task successfully';
    }

    private static extractSolutionFromContent(content: string): string {
        // Buscar secciones de solución con múltiples patrones
        const solutionPatterns = [
            /(?:solution|fix|resolution):\s*(.*?)(?=\n\n|\n[A-Z]|$)/is,
            /(?:to resolve|to fix|the fix).*?:\s*(.*?)(?=\n\n|$)/is,
            /(?:steps?|approach).*?:\s*(.*?)(?=\n\n|$)/is,
            /(?:corrected|fixed|modified|updated).*?(?:by|to|with)\s*(.*?)(?=\n\n|$)/is
        ];

        for (const pattern of solutionPatterns) {
            const match = content.match(pattern);
            if (match && match[1] && match[1].trim().length > 15) {
                let solution = match[1].trim();
                // Formatear mejor
                solution = solution.replace(/^\d+\.\s*/gm, '• ');
                solution = solution.replace(/\*\*(.*?)\*\*/g, '$1'); // Remove bold markdown
                return solution.substring(0, 500); // Limitar longitud
            }
        }

        // Buscar bloques de pasos o instrucciones
        const stepPatterns = [
            /1\.\s*.*?(?:\n2\.|\n\n|$)/is,
            /•\s*.*?(?:\n•|\n\n|$)/is,
            /first.*?then.*?(?:\n\n|$)/is
        ];

        for (const pattern of stepPatterns) {
            const match = content.match(pattern);
            if (match && match[0] && match[0].trim().length > 20) {
                return match[0].replace(/^\d+\.\s*/gm, '• ').trim().substring(0, 500);
            }
        }

        // Buscar descripción de lo que se hizo
        const actionDescriptions = [
            /(?:added|fixed|modified|corrected|updated).*?(?:function|file|code|error).*?(?:\.|$)/i,
            /(?:created|opened|submitted).*?(?:pull request|pr|branch).*?(?:\.|$)/i
        ];

        for (const pattern of actionDescriptions) {
            const match = content.match(pattern);
            if (match && match[0] && match[0].length > 20 && match[0].length < 300) {
                return match[0].trim();
            }
        }

        return '';
    }

    private static extractFilesFromContent(content: string): string[] {
        const files: string[] = [];
        
        // Buscar archivos con extensiones comunes
        const fileExtensions = '(?:py|js|ts|jsx|tsx|java|cpp|c|h|html|css|json|xml|yaml|yml|md|txt|sql)';
        const filePattern = new RegExp(`\\b[\\w-]+\\.${fileExtensions}\\b`, 'gi');
        
        const fileMatches = content.match(filePattern);
        if (fileMatches) {
            files.push(...fileMatches.filter(file => 
                !file.match(/^\d+\.\d+$/) && // No versiones
                file.length > 3 &&
                !file.includes('ghp_') && // No tokens
                !file.startsWith('tool-') // No IDs de herramientas
            ));
        }

        // Buscar archivos mencionados específicamente
        const filePatterns = [
            /(?:file|script|document)(?:\s+named)?\s+['"`]?([^\s'"`]+\.${fileExtensions})['"`]?/gi,
            /(?:in|from|to|modify|update|edit)\s+['"`]?([^\s'"`]+\.${fileExtensions})['"`]?/gi,
            /['"`]([^\s'"`]+\.${fileExtensions})['"`]/gi
        ];

        for (const pattern of filePatterns) {
            const matches = content.matchAll(new RegExp(pattern.source.replace('${fileExtensions}', fileExtensions), 'gi'));
            for (const match of matches) {
                if (match[1] && !match[1].match(/^\d+\.\d+$/)) {
                    files.push(match[1]);
                }
            }
        }

        return [...new Set(files)].filter(file => file.length > 3);
    }

    private static extractBranchFromContent(content: string): string {
        // Buscar nombres de branch con patrones comunes
        const branchPatterns = [
            /['"`]([^'"`\s]*(?:fix|feature|bug|update|add)[^'"`\s]*)['"`]/gi,
            /(?:branch|head)(?:\s+name)?[:\s]+['"`]?([^\s'"`\n,]+)['"`]?/i,
            /(?:created|checkout|switch)\s+(?:branch\s+)?['"`]?([^\s'"`\n,]+)['"`]?/i,
            /(?:on|from|to)\s+branch\s+['"`]?([^\s'"`\n,]+)['"`]?/i
        ];

        for (const pattern of branchPatterns) {
            const match = content.match(pattern);
            if (match && match[1] && 
                match[1] !== 'for' && 
                match[1] !== 'main' && 
                match[1] !== 'master' &&
                match[1].length > 2 &&
                match[1].length < 50) {
                return match[1];
            }
        }
        return '';
    }

    private static extractErrorsFromContent(content: string): string[] {
        const errors: string[] = [];
        
        // Buscar errores específicos y conocidos
        const errorPatterns = [
            /(?:SyntaxError|TypeError|ValueError|RuntimeError|FileNotFoundError|ImportError)[:\s]+(.*?)(?=\n|$)/gi,
            /(?:404|500|403|401).*?(?:error|not found|server error)/gi,
            /(?:failed to|error|exception).*?(?:file|function|syntax|compile).*?(?=\n|$)/gi,
            /compilation.*?(?:error|failed)/gi
        ];

        for (const pattern of errorPatterns) {
            const matches = content.matchAll(pattern);
            for (const match of matches) {
                const errorText = match[1] || match[0];
                if (errorText && errorText.trim().length > 5 && errorText.trim().length < 200) {
                    errors.push(errorText.trim());
                }
            }
        }

        // Filtrar errores que son realmente fragmentos de análisis interno
        return errors.filter(error => 
            !error.includes('wait, maybe') &&
            !error.includes('hmm,') &&
            !error.includes('alternatively,') &&
            !error.includes('perhaps the') &&
            !error.includes('i think') &&
            !error.includes('maybe the') &&
            error.split(' ').length < 20 && // No muy largos
            !error.toLowerCase().includes('message shows') &&
            !error.toLowerCase().includes('user\'s code')
        );
    }

    private static parseTextResponse(text: string): ParsedAgentResponse {
        const result: ParsedAgentResponse = {
            summary: this.extractSummary(text),
            rawContent: text,
            status: 'success'
        };

        // Extraer información usando regex mejorados
        result.solution = this.extractSection(text, ['solution', 'fix', 'resolution', 'final answer']);
        result.filesModified = this.extractFilesList(text);
        result.pullRequestUrl = this.extractPullRequestUrl(text);
        result.branchName = this.extractBranchName(text);
        result.errors = this.extractErrors(text);

        if (result.errors && result.errors.length > 0) {
            result.status = 'error';
        }

        return result;
    }

    private static extractSummary(text: string): string {
        // Extraer las primeras líneas como resumen
        const lines = text.split('\n').filter(line => line.trim());
        if (lines.length > 0) {
            return lines[0].substring(0, 150) + (lines[0].length > 150 ? '...' : '');
        }
        return 'Agent response processed';
    }

    private static extractSection(text: string, keywords: string[]): string | undefined {
        for (const keyword of keywords) {
            const regex = new RegExp(`${keyword}[:\\s]+(.*?)(?=\\n\\n|\\n[A-Z]|$)`, 'is');
            const match = text.match(regex);
            if (match) {
                return match[1].trim();
            }
        }
        return undefined;
    }

    private static extractFilesList(text: string): string[] | undefined {
        const patterns = [
            /files?\s+(?:modified|changed|updated)[:\s]+(.*?)(?=\n\n|\n[A-Z]|$)/is,
            /modified\s+files?[:\s]+(.*?)(?=\n\n|\n[A-Z]|$)/is,
            /\b\w+\.\w+\b/g // Buscar nombres de archivos con extensión
        ];

        for (const pattern of patterns) {
            const match = text.match(pattern);
            if (match && match[1]) {
                return match[1].split(/[,\n]/).map((f: string) => f.trim()).filter((f: string) => f);
            }
        }
        
        // Buscar archivos con extensiones comunes
        const fileMatches = text.match(/\b[\w-]+\.(py|js|ts|java|cpp|c|html|css|json)\b/g);
        return fileMatches ? [...new Set(fileMatches)] : undefined;
    }

    private static extractPullRequestUrl(text: string): string | undefined {
        const urlPattern = /https:\/\/github\.com\/[^\/]+\/[^\/]+\/pull\/\d+/;
        const match = text.match(urlPattern);
        return match ? match[0] : undefined;
    }

    private static extractBranchName(text: string): string | undefined {
        const patterns = [
            /branch[:\s]+([^\s\n]+)/i,
            /created\s+branch[:\s]+([^\s\n]+)/i
        ];

        for (const pattern of patterns) {
            const match = text.match(pattern);
            if (match && match[1] !== 'for') {
                return match[1];
            }
        }
        return undefined;
    }

    private static extractErrors(text: string): string[] | undefined {
        const errorPatterns = [
            /error[:\s]+(.*?)(?=\n\n|\n[A-Z]|$)/gis,
            /failed[:\s]+(.*?)(?=\n\n|\n[A-Z]|$)/gis,
            /exception[:\s]+(.*?)(?=\n\n|\n[A-Z]|$)/gis
        ];

        const errors: string[] = [];
        for (const pattern of errorPatterns) {
            const matches = text.matchAll(pattern);
            for (const match of matches) {
                if (match[1]) {
                    errors.push(match[1].trim());
                }
            }
        }

        return errors.length > 0 ? errors : undefined;
    }
} 