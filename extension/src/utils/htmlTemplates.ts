import { GitHubIssue } from '../models/issue';

function convertMarkdownToHtml(text: string): string {
  if (!text) return '';
  
  return text
    // Convert **bold** to <strong>bold</strong>
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    // Convert *italic* to <em>italic</em>
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    // Convert [link text](url) to <a href="url">link text</a>
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>')
    // Convert line breaks
    .replace(/\n/g, '<br>')
    // Escape remaining HTML tags except the ones we created
    .replace(/<(?!\/?(strong|em|a|br)\b)[^>]*>/g, (match) => {
      return match.replace(/</g, '&lt;').replace(/>/g, '&gt;');
    });
}

export function getIssueHtml(issue: GitHubIssue, logoUrl: string): string {
  return `
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src vscode-webview: https: data:;">
      <title>Issue #${issue.number}</title>
      <style>
        :root {
          --primary-color: #2563eb;
          --primary-light: #3b82f6;
          --primary-dark: #1d4ed8;
          --success-color: #10b981;
          --success-hover: #059669;
          --text-primary: #1f2937;
          --text-secondary: #6b7280;
          --text-muted: #9ca3af;
          --bg-primary: #ffffff;
          --bg-secondary: #f9fafb;
          --bg-accent: #f3f4f6;
          --border-color: #e5e7eb;
          --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
          --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
          --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
          --radius-sm: 4px;
          --radius-md: 6px;
          --radius-lg: 8px;
          --radius-full: 9999px;
          --transition: all 0.2s ease;
        }
        
        * {
          box-sizing: border-box;
          margin: 0;
          padding: 0;
        }
        
        body {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
          line-height: 1.5;
          color: var(--text-primary);
          background-color: var(--bg-secondary);
          padding: 0;
          margin: 0;
          -webkit-font-smoothing: antialiased;
          -moz-osx-font-smoothing: grayscale;
        }
        
        .container {
          max-width: 950px;
          margin: 0 auto;
          padding: 2rem;
          background-color: var(--bg-primary);
          box-shadow: var(--shadow-md);
          border-radius: var(--radius-lg);
          margin-top: 2rem;
          margin-bottom: 2rem;
          transition: var(--transition);
        }
        
        .container:hover {
          box-shadow: var(--shadow-lg);
        }
        
        .navbar {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0.75rem 1.5rem;
          background: #15426d;
          color: white;
          box-shadow: var(--shadow-md);
          position: sticky;
          top: 0;
          z-index: 100;
        }
        
        .logo-container {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }
        
        .app-name {
          font-size: 1.25rem;
          font-weight: 600;
          letter-spacing: 0.5px;
        }
        
        .header {
          border-bottom: 1px solid var(--border-color);
          padding-bottom: 1.25rem;
          margin-bottom: 1.5rem;
        }
        
        .issue-title {
          font-size: 1.5rem;
          font-weight: 600;
          color: var(--text-primary);
          margin-bottom: 0.75rem;
          line-height: 1.3;
        }
        
        .issue-number {
          color: var(--text-secondary);
          font-weight: 500;
          margin-right: 0.5rem;
        }
        
        .meta {
          display: flex;
          gap: 1.25rem;
          flex-wrap: wrap;
          align-items: center;
          color: var(--text-secondary);
          font-size: 0.875rem;
          margin-bottom: 1rem;
        }
        
        .meta-item {
          display: flex;
          align-items: center;
          gap: 0.375rem;
        }
        
        .status-badge {
          display: inline-flex;
          align-items: center;
          padding: 0.25rem 0.75rem;
          border-radius: var(--radius-full);
          font-size: 0.75rem;
          font-weight: 500;
          background-color: #dcfce7;
          color: #166534;
          box-shadow: var(--shadow-sm);
        }
        
        .status-badge.closed {
          background-color: #fee2e2;
          color: #991b1b;
        }
        
        .labels {
          display: flex;
          flex-wrap: wrap;
          gap: 0.5rem;
          margin-top: 0.75rem;
        }
        
        .label {
          display: inline-flex;
          align-items: center;
          padding: 0.25rem 0.75rem;
          border-radius: var(--radius-full);
          font-size: 0.75rem;
          font-weight: 500;
          background-color: var(--bg-accent);
          color: var(--text-secondary);
        }
        
        .body-section {
          margin-top: 2rem;
        }
        
        .body-content {
          background-color: var(--bg-accent);
          padding: 1.25rem;
          border-radius: var(--radius-md);
          font-size: 0.9375rem;
          white-space: pre-wrap;
        }
        
        .code-block {
          background-color: #1e1e1e;
          color: #e6e6e6;
          font-family: 'Fira Mono', 'Consolas', 'Menlo', monospace;
          font-size: 0.875rem;
          padding: 1.25rem;
          border-radius: var(--radius-md);
          margin-top: 1.5rem;
          margin-bottom: 1.5rem;
          overflow-x: auto;
          white-space: pre;
        }
        
        .actions {
          display: flex;
          flex-wrap: wrap;
          gap: 1rem;
          margin-top: 2rem;
          border-top: 1px solid var(--border-color);
          padding-top: 1.5rem;
        }
        
        .button {
          display: inline-flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.625rem 1.25rem;
          border-radius: var(--radius-md);
          font-size: 0.875rem;
          font-weight: 500;
          cursor: pointer;
          transition: var(--transition);
          border: none;
          outline: none;
        }
        
        .fix-button-structured {
          background-color: var(--success-color);
          color: white;
        }
        
        .fix-button-structured:hover {
          background-color: var(--success-hover);
        }
        
        .fix-button-icon {
          width: 1rem;
          height: 1rem;
        }
        
        .agent-response-section {
          margin-top: 2rem;
          border-top: 1px solid var(--border-color);
          padding-top: 1.5rem;
          display: none;
        }
        
        .agent-response-section.visible {
          display: block;
        }
        
        .agent-response-title {
          font-size: 1.25rem;
          font-weight: 600;
          color: var(--text-primary);
          margin-bottom: 1rem;
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }
        
        .agent-response-content {
          background-color: #f8fafc;
          border: 1px solid #e2e8f0;
          border-radius: var(--radius-md);
          padding: 1.25rem;
          font-size: 0.9375rem;
          line-height: 1.6;
        }
        
        .agent-response-content strong {
          font-weight: 600;
          color: var(--text-primary);
        }
        
        .agent-response-content b {
          font-weight: 600;
          color: var(--text-primary);
        }
        
        .agent-response-content em {
          font-style: italic;
          color: var(--text-secondary);
        }
        
        .agent-response-content a {
          color: var(--primary-color);
          text-decoration: none;
          border-bottom: 1px solid transparent;
          transition: var(--transition);
        }
        
        .agent-response-content a:hover {
          color: var(--primary-dark);
          border-bottom-color: var(--primary-color);
        }
        
        .agent-log {
          margin-top: 1.5rem;
        }
        
        .agent-log-title {
          font-size: 1.125rem;
          font-weight: 600;
          color: var(--text-primary);
          margin-bottom: 0.75rem;
        }
        
        .agent-log-content {
          background-color: #1e1e1e;
          color: #e6e6e6;
          font-family: 'Fira Mono', 'Consolas', 'Menlo', monospace;
          font-size: 0.875rem;
          padding: 1.25rem;
          border-radius: var(--radius-md);
          max-height: 400px;
          overflow-y: auto;
          white-space: pre-wrap;
        }
        
        .loading {
          display: none;
          align-items: center;
          justify-content: center;
          margin: 2rem 0;
        }
        
        .loading.visible {
          display: flex;
        }
        
        .loading-spinner {
          border: 4px solid rgba(0, 0, 0, 0.1);
          border-radius: 50%;
          border-top: 4px solid var(--primary-color);
          width: 24px;
          height: 24px;
          animation: spin 1s linear infinite;
          margin-right: 1rem;
        }
        
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      </style>
    </head>
    <body>
      <div class="navbar">
        <div class="logo-container">
          <img src="${logoUrl}" alt="CodeMedic Logo" style="height: 24px; width: 24px;" />
          <span class="app-name">CodeMedic</span>
        </div>
      </div>
      
      <div class="container">
        <div class="header">
          <h1 class="issue-title">
            <span class="issue-number">#${issue.number}</span>
            ${issue.title}
          </h1>
          
          <div class="meta">
            <div class="meta-item">
              <span class="status-badge ${issue.state === 'closed' ? 'closed' : ''}">
                ${issue.state}
              </span>
            </div>
            
            <div class="meta-item">
              Opened by <b>${issue.user?.login || "Unknown"}</b> on ${new Date(issue.created_at).toLocaleString()}
            </div>
          </div>
          
          <div class="labels">
            ${(issue.labels || [])
              .map((l) => `<span class="label">${l.name}</span>`)
              .join("")}
          </div>
        </div>
        
        <div class="body-section">
          <div class="body-content">${
            issue.body
              ? issue.body.replace(/</g, "&lt;").replace(/\n/g, "<br>")
              : "<i>No description provided.</i>"
          }</div>
        </div>
        
        <div class="actions">
          <button class="button fix-button-structured" id="fix-button-structured">
            <svg class="fix-button-icon" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
            </svg>
            Fix this issue with CodeMedic
          </button>
        </div>
        
        <div id="loading" class="loading">
          <div class="loading-spinner"></div>
          <span>Processing issue with CodeMedic agent...</span>
        </div>
        
        <div id="agent-response" class="agent-response-section">
          <h2 class="agent-response-title">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M9 11.24V7.5C9 6.12 10.12 5 11.5 5S14 6.12 14 7.5v3.74c1.21-.81 2-2.18 2-3.74C16 5.01 13.99 3 11.5 3S7 5.01 7 7.5c0 1.56.79 2.93 2 3.74zm9.84 4.63l-4.54-2.26c-.17-.07-.35-.11-.54-.11H13v-6c0-.83-.67-1.5-1.5-1.5S10 6.67 10 7.5v10.74c-3.6-.76-3.54-.75-3.67-.75-.31 0-.59.13-.79.33l-.79.8 4.94 4.94c.27.27.65.44 1.06.44h6.79c.75 0 1.33-.55 1.44-1.28l.75-5.27c.01-.07.02-.14.02-.2 0-.62-.38-1.16-.91-1.38z" fill="currentColor"/>
            </svg>
            Agent Solution
          </h2>
          <div id="agent-response-content" class="agent-response-content">
            The agent's response will appear here after processing the issue.
          </div>
          
          <div id="agent-log" class="agent-log" style="display: none;">
            <h3 class="agent-log-title">Agent Log Output</h3>
            <div id="agent-log-content" class="agent-log-content"></div>
          </div>
        </div>
      </div>
      
      <script>
        // Get VS Code API
        const vscode = acquireVsCodeApi();
        
        // Configure fix button
        function setupFixButton() {
          const fixButton = document.getElementById('fix-button-structured');
          
          if (!fixButton) {
            console.error('Fix button not found');
            return;
          }
          
          // Add click listener
          fixButton.addEventListener('click', function() {
            // Show loading state
            const loading = document.getElementById('loading');
            if (loading) {
              loading.classList.add('visible');
            }
            
            // Send message to extension
            vscode.postMessage({
              command: 'fixIssueStructured'
            });
          });
        }
        
        // Handle messages from extension
        window.addEventListener('message', function(event) {
          const message = event.data;
          
          if (message.command === 'agentResponse') {
            // Hide loading
            const loading = document.getElementById('loading');
            if (loading) {
              loading.classList.remove('visible');
            }
            
            // Show response
            const responseSection = document.getElementById('agent-response');
            const responseContent = document.getElementById('agent-response-content');
            
            if (responseSection && responseContent) {
              responseContent.innerHTML = message.response.details || 'No response details available';
              responseSection.classList.add('visible');
            }
          }
        });
        
        // Initialize when DOM is ready
        if (document.readyState === 'loading') {
          document.addEventListener('DOMContentLoaded', setupFixButton);
        } else {
          setupFixButton();
        }
      </script>
    </body>
    </html>
  `;
}

export function getAgentResponseHtml(title: string, response: any, logoUrl?: string): string {
  // Extract data for dropdowns
  const summary = response.agentSummary || 'No summary available';
  const messages = response.agentMessages || [];
  
  // Filter out step 1 (prompt) and empty messages
  const filteredMessages = messages.filter((msg: string, index: number) => {
    return index > 0 && msg && msg.trim().length > 0;
  });

  return `
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src vscode-webview: https: data:;">
      <title>${title}</title>
      <style>
        :root {
          --primary-color: #2563eb;
          --primary-light: #3b82f6;
          --primary-dark: #1d4ed8;
          --success-color: #10b981;
          --success-hover: #059669;
          --text-primary: #1f2937;
          --text-secondary: #6b7280;
          --text-muted: #9ca3af;
          --bg-primary: #ffffff;
          --bg-secondary: #f9fafb;
          --bg-accent: #f3f4f6;
          --border-color: #e5e7eb;
          --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
          --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
          --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
          --radius-sm: 4px;
          --radius-md: 6px;
          --radius-lg: 8px;
          --radius-full: 9999px;
          --transition: all 0.2s ease;
        }
        
        * {
          box-sizing: border-box;
          margin: 0;
          padding: 0;
        }
        
        body {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
          line-height: 1.5;
          color: var(--text-primary);
          background-color: var(--bg-secondary);
          padding: 0;
          margin: 0;
          -webkit-font-smoothing: antialiased;
          -moz-osx-font-smoothing: grayscale;
        }
        
        .container {
          max-width: 950px;
          margin: 0 auto;
          padding: 2rem;
          background-color: var(--bg-primary);
          box-shadow: var(--shadow-md);
          border-radius: var(--radius-lg);
          margin-top: 2rem;
          margin-bottom: 2rem;
          transition: var(--transition);
        }
        
        .container:hover {
          box-shadow: var(--shadow-lg);
        }
        
        .navbar {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0.75rem 1.5rem;
          background: #15426d;
          color: white;
          box-shadow: var(--shadow-md);
          position: sticky;
          top: 0;
          z-index: 100;
        }
        
        .logo-container {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }
        
        .app-name {
          font-size: 1.25rem;
          font-weight: 600;
          letter-spacing: 0.5px;
        }
        
        .header {
          border-bottom: 1px solid var(--border-color);
          padding-bottom: 1.25rem;
          margin-bottom: 1.5rem;
        }
        
        .title {
          font-size: 1.5rem;
          font-weight: 600;
          color: var(--text-primary);
          margin-bottom: 0.75rem;
          line-height: 1.3;
        }
        
        .meta {
          display: flex;
          gap: 1.25rem;
          flex-wrap: wrap;
          align-items: center;
          color: var(--text-secondary);
          font-size: 0.875rem;
          margin-bottom: 1rem;
        }
        
        .meta-item {
          display: flex;
          align-items: center;
          gap: 0.375rem;
        }
        
        .status-badge {
          display: inline-flex;
          align-items: center;
          padding: 0.25rem 0.75rem;
          border-radius: var(--radius-full);
          font-size: 0.75rem;
          font-weight: 500;
          background-color: #dcfce7;
          color: #166534;
          box-shadow: var(--shadow-sm);
        }
        
        .status-badge.error {
          background-color: #fee2e2;
          color: #991b1b;
        }
        
        .status-badge.processing {
          background-color: #fef3c7;
          color: #92400e;
        }

        /* Dropdown Styles */
        .section {
          margin-bottom: 1.5rem;
          border: 1px solid var(--border-color);
          border-radius: var(--radius-md);
          overflow: hidden;
        }
        
        .section-header {
          background-color: var(--bg-accent);
          padding: 1rem 1.25rem;
          cursor: pointer;
          display: flex;
          justify-content: between;
          align-items: center;
          transition: var(--transition);
        }
        
        .section-header:hover {
          background-color: #e5e7eb;
        }
        
        .section-title {
          font-size: 1.1rem;
          font-weight: 600;
          color: var(--text-primary);
          margin: 0;
          flex-grow: 1;
        }
        
        .dropdown-arrow {
          width: 20px;
          height: 20px;
          transition: transform 0.2s ease;
          color: var(--text-secondary);
        }
        
        .dropdown-arrow.expanded {
          transform: rotate(90deg);
        }
        
        .section-content {
          display: none;
          padding: 1.25rem;
          background-color: var(--bg-primary);
          border-top: 1px solid var(--border-color);
          font-size: 0.9375rem;
          line-height: 1.6;
        }
        
        .section-content.expanded {
          display: block;
        }
        
        .summary-content {
          color: var(--text-primary);
          white-space: pre-wrap;
        }
        
        .message-item {
          padding: 0.75rem;
          margin-bottom: 0.75rem;
          background-color: var(--bg-accent);
          border-radius: var(--radius-sm);
          border-left: 3px solid var(--primary-color);
        }
        
        .message-item:last-child {
          margin-bottom: 0;
        }
        
        .message-title {
          font-weight: 600;
          color: var(--primary-color);
          margin-bottom: 0.5rem;
        }
        
        .message-content {
          color: var(--text-primary);
          white-space: pre-wrap;
          word-wrap: break-word;
        }
        
        .no-messages {
          color: var(--text-muted);
          font-style: italic;
          text-align: center;
          padding: 2rem;
        }
      </style>
    </head>
    <body>
      <div class="navbar">
        <div class="logo-container">
          ${logoUrl ? `<img src="${logoUrl}" alt="CodeMedic Logo" style="width: 32px; height: 32px; object-fit: contain;">` : ''}
          <span class="app-name">CodeMedic</span>
        </div>
      </div>
      
      <div class="container">
        <div class="header">
          <h1 class="title">${title}</h1>
          
          <div class="meta">
            <div class="meta-item">
              <span class="status-badge ${response.result}">
                ${response.result}
              </span>
            </div>
            
            <div class="meta-item">
              Processed on ${new Date().toLocaleString()}
            </div>
          </div>
        </div>
        
        <!-- Summary Section -->
        <div class="section">
          <div class="section-header" onclick="toggleSection('summary')">
            <h3 class="section-title">📋 Summary</h3>
            <span class="dropdown-arrow" id="summary-arrow">▶</span>
          </div>
          <div class="section-content" id="summary-content">
            <div class="summary-content">${summary}</div>
          </div>
        </div>
        
        <!-- Agent Messages Section -->
        <div class="section">
          <div class="section-header" onclick="toggleSection('messages')">
            <h3 class="section-title">🤖 Agent Messages (${filteredMessages.length} steps)</h3>
            <span class="dropdown-arrow" id="messages-arrow">▶</span>
          </div>
          <div class="section-content" id="messages-content">
            ${filteredMessages.length > 0 ? 
              filteredMessages.map((message: string, index: number) => `
                <div class="message-item">
                  <div class="message-title">Step ${index + 2}</div>
                  <div class="message-content">${message}</div>
                </div>
              `).join('') : 
              '<div class="no-messages">No detailed steps available</div>'
            }
          </div>
        </div>
      </div>
      
      <script>
        function toggleSection(sectionId) {
          const content = document.getElementById(sectionId + '-content');
          const arrow = document.getElementById(sectionId + '-arrow');
          
          if (content.classList.contains('expanded')) {
            content.classList.remove('expanded');
            arrow.classList.remove('expanded');
          } else {
            content.classList.add('expanded');
            arrow.classList.add('expanded');
          }
        }
      </script>
    </body>
    </html>
  `;
} 