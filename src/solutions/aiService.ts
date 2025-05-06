import * as vscode from "vscode";
import axios from "axios";

export interface CodeFix {
  filePath: string;
  originalCode: string;
  fixedCode: string;
  explanation: string;
}

export class AIService {
  private apiKey: string | undefined;

  constructor() {
    this.loadApiKey();
  }

  private async loadApiKey(): Promise<void> {
    // Try to get the API key from the settings
    this.apiKey = vscode.workspace
      .getConfiguration("codemedic")
      .get<string>("openaiApiKey");

    if (!this.apiKey) {
      // If not found, prompt the user
      const key = await vscode.window.showInputBox({
        prompt: "Enter your OpenAI API key to enable AI-powered solutions",
        password: true,
        ignoreFocusOut: true,
        placeHolder: "sk-...",
      });

      if (key) {
        this.apiKey = key;
        // Save the API key in the settings
        await vscode.workspace
          .getConfiguration("codemedic")
          .update("openaiApiKey", key, vscode.ConfigurationTarget.Global);
      }
    }
  }

  public async isConfigured(): Promise<boolean> {
    if (!this.apiKey) {
      await this.loadApiKey();
    }
    return !!this.apiKey;
  }

  /**
   * Analyzes an issue and generates a solution
   * @param issue GitHub issue object
   * @param relevantFiles Array of relevant file paths
   * @returns A detailed solution with step-by-step guidance
   */
  public async analyzeSolution(
    issue: any,
    relevantFiles: string[]
  ): Promise<string> {
    if (!(await this.isConfigured())) {
      return "Please configure your OpenAI API key to generate AI-powered solutions.";
    }

    try {
      // Get content of relevant files
      const fileContents: { [key: string]: string } = {};
      for (const filePath of relevantFiles.slice(0, 5)) {
        // Limit to first 5 files to avoid token limits
        try {
          const workspaceFolders = vscode.workspace.workspaceFolders;
          if (!workspaceFolders) continue;

          const fileUri = vscode.Uri.file(
            `${workspaceFolders[0].uri.fsPath}/${filePath}`
          );
          const document = await vscode.workspace.openTextDocument(fileUri);
          fileContents[filePath] = document.getText();
        } catch (error) {
          // Skip files that can't be read
          console.error(`Error reading file ${filePath}:`, error);
        }
      }

      // Prepare prompt for OpenAI API
      const prompt = `
You are a skilled software engineer tasked with resolving GitHub issues.

ISSUE #${issue.number}: ${issue.title}
DESCRIPTION: ${issue.body || "No description provided"}

I've identified these potentially relevant files to fix this issue:
${Object.keys(fileContents)
  .map((filename) => `- ${filename}`)
  .join("\n")}

For the MOST relevant files, here are their contents:

${Object.entries(fileContents)
  .map(
    ([filename, content]) =>
      `--- ${filename} ---\n${content}\n--- End of ${filename} ---\n`
  )
  .join("\n")}

Please analyze this issue and provide:
1. A detailed understanding of the problem
2. The root cause of the issue
3. A step-by-step explanation of how to solve it
4. Specific code changes needed for each relevant file

Format your response in markdown, focusing on clarity and actionable steps.
`;

      // Call OpenAI API
      const response = await axios.post(
        "https://api.openai.com/v1/chat/completions",
        {
          model: "gpt-4-turbo-preview",
          messages: [
            {
              role: "system",
              content:
                "You are a helpful software engineering assistant that specializes in analyzing and fixing code issues.",
            },
            { role: "user", content: prompt },
          ],
          temperature: 0.3,
          max_tokens: 2000,
        },
        {
          headers: {
            Authorization: `Bearer ${this.apiKey}`,
            "Content-Type": "application/json",
          },
        }
      );

      return response.data.choices[0].message.content;
    } catch (error) {
      console.error("Error calling OpenAI API:", error);
      return `Failed to generate solution: ${
        (error as any).message || "Unknown error"
      }`;
    }
  }

  /**
   * Generates specific code fixes for relevant files
   * @param issue GitHub issue object
   * @param relevantFiles Array of relevant file paths
   * @returns Array of CodeFix objects
   */
  public async generateCodeFixes(
    issue: any,
    relevantFiles: string[]
  ): Promise<CodeFix[]> {
    if (!(await this.isConfigured())) {
      vscode.window.showErrorMessage(
        "Please configure your OpenAI API key to generate code fixes."
      );
      return [];
    }

    try {
      const codeFixes: CodeFix[] = [];

      // Get content of relevant files
      const fileContents: { [key: string]: string } = {};
      for (const filePath of relevantFiles.slice(0, 3)) {
        // Limit to first 3 files to reduce token usage
        try {
          const workspaceFolders = vscode.workspace.workspaceFolders;
          if (!workspaceFolders) continue;

          const fileUri = vscode.Uri.file(
            `${workspaceFolders[0].uri.fsPath}/${filePath}`
          );
          const document = await vscode.workspace.openTextDocument(fileUri);
          fileContents[filePath] = document.getText();
        } catch (error) {
          // Skip files that can't be read
          console.error(`Error reading file ${filePath}:`, error);
        }
      }

      // For each file, generate a fix
      for (const [filePath, originalCode] of Object.entries(fileContents)) {
        // Prepare prompt for OpenAI API
        const prompt = `
You are a master programmer tasked with fixing a specific issue in a code file. 
You MUST return ONLY a complete, fixed version of the file with the necessary changes.

ISSUE #${issue.number}: ${issue.title}
DESCRIPTION: ${issue.body || "No description provided"}

FILE TO FIX: ${filePath}

CURRENT CODE:
\`\`\`
${originalCode}
\`\`\`

Instructions:
1. Carefully analyze the issue and the code
2. Make ONLY the necessary changes to fix the issue
3. Return the ENTIRE fixed file content, not just the changes
4. Be conservative in your changes - fix ONLY what's needed for this specific issue
5. Do NOT change functionality not related to the issue
6. Preserve all existing formatting, comments, and style as much as possible

Return ONLY the fixed code content with no additional explanation.
`;

        // Status notification for user
        vscode.window.setStatusBarMessage(`Analyzing ${filePath}...`, 5000);

        try {
          // Call OpenAI API
          const response = await axios.post(
            "https://api.openai.com/v1/chat/completions",
            {
              model: "gpt-4-turbo-preview",
              messages: [
                {
                  role: "system",
                  content:
                    "You are a code fixing assistant that returns ONLY fixed code with no additional text.",
                },
                { role: "user", content: prompt },
              ],
              temperature: 0.2,
              max_tokens: 4000,
            },
            {
              headers: {
                Authorization: `Bearer ${this.apiKey}`,
                "Content-Type": "application/json",
              },
            }
          );

          const fixedCode = response.data.choices[0].message.content.trim();

          // Now get an explanation of the changes
          const explanationPrompt = `
I've fixed an issue in a code file. Please provide a BRIEF explanation of the changes I made:

ISSUE: ${issue.title}
FILE: ${filePath}

ORIGINAL CODE:
\`\`\`
${originalCode}
\`\`\`

FIXED CODE:
\`\`\`
${fixedCode}
\`\`\`

Provide a concise explanation (max 3 bullet points) of what was changed and why.
`;

          const explanationResponse = await axios.post(
            "https://api.openai.com/v1/chat/completions",
            {
              model: "gpt-3.5-turbo",
              messages: [
                {
                  role: "system",
                  content:
                    "You are a code review assistant that explains code changes clearly and concisely.",
                },
                { role: "user", content: explanationPrompt },
              ],
              temperature: 0.3,
              max_tokens: 300,
            },
            {
              headers: {
                Authorization: `Bearer ${this.apiKey}`,
                "Content-Type": "application/json",
              },
            }
          );

          const explanation =
            explanationResponse.data.choices[0].message.content.trim();

          // Add to fixes
          codeFixes.push({
            filePath,
            originalCode,
            fixedCode,
            explanation,
          });
        } catch (error) {
          console.error(`Error generating fix for ${filePath}:`, error);
        }
      }

      return codeFixes;
    } catch (error) {
      console.error("Error generating code fixes:", error);
      vscode.window.showErrorMessage(
        `Failed to generate code fixes: ${
          (error as any).message || "Unknown error"
        }`
      );
      return [];
    }
  }
}
