import * as vscode from 'vscode';
import { GitHubIssue, GitHubCredentials } from '../models/issue';
import { GITHUB_TOKEN, DEFAULT_REPOSITORY } from '../utils/constants';
import { Octokit } from '@octokit/rest';

export class GitHubService {
    private context: vscode.ExtensionContext;
    private octokit: Octokit | undefined;
    private repository: string = "Elcasvi/Code-Fixer-LLM-Agent";

    constructor(context: vscode.ExtensionContext) {
        this.context = context;
        this.initializeOctokit();
        console.log('GitHubService initialized with:', {
            hasOctokit: !!this.octokit,
            repository: this.repository
        });
    }

    private initializeOctokit() {
        const token = this.context.globalState.get<string>('githubToken');
        if (token) {
            this.octokit = new Octokit({ auth: token });
        }
    }

    async authenticate(): Promise<void> {
        try {
            console.log('Starting authentication...');
            
            // Prompt for token
            const token = await vscode.window.showInputBox({
                prompt: 'Enter your GitHub Personal Access Token',
                password: true,
                ignoreFocusOut: true
            });

            if (!token) {
                throw new Error('No token provided');
            }

            this.octokit = new Octokit({ auth: token });
            
            await this.context.globalState.update('githubToken', token);
            
            console.log('Authentication successful:', {
                repository: this.repository,
                hasOctokit: !!this.octokit
            });
            
            vscode.window.showInformationMessage(`Successfully authenticated with GitHub repository: ${this.repository}`);
        } catch (error) {
            console.error('Authentication failed:', error);
            vscode.window.showErrorMessage(`Failed to authenticate with GitHub: ${error}`);
            throw error;
        }
    }

    isAuthenticated(): boolean {
        const isAuth = !!this.octokit && !!this.repository;
        console.log('Checking authentication:', {
            hasOctokit: !!this.octokit,
            hasRepository: !!this.repository,
            isAuthenticated: isAuth
        });
        return isAuth;
    }

    async getRepoInfo(): Promise<{ owner: string; repo: string } | null> {
        console.log('Getting repository info...');
        const [owner, repo] = this.repository.split('/');
        if (!owner || !repo) {
            console.log('Invalid repository format:', this.repository);
            vscode.window.showErrorMessage('Invalid repository format. Expected: owner/repo');
            return null;
        }

        console.log('Repository info:', { owner, repo });
        return { owner, repo };
    }

    async getCredentials(): Promise<GitHubCredentials> {
        try {
            if (!this.octokit) {
                console.log('Credentials not configured:', {
                    hasOctokit: !!this.octokit
                });
                throw new Error('GitHub credentials not configured');
            }

            const token = this.context.globalState.get<string>('githubToken');
            if (!token) {
                throw new Error('GitHub token not found');
            }

            const repoInfo = await this.getRepoInfo();
            if (!repoInfo) {
                throw new Error('Repository information not found');
            }

            return {
                token: token,
                repository_name: `${repoInfo.owner}/${repoInfo.repo}`
            };
        } catch (error) {
            console.error('Error getting credentials:', error);
            throw error;
        }
    }

    async getIssues(): Promise<GitHubIssue[]> {
        try {
            console.log('Getting issues...');
            if (!this.octokit) {
                console.log('No Octokit instance available');
                vscode.window.showErrorMessage('GitHub token not configured. Please authenticate first.');
                return [];
            }

            const repoInfo = await this.getRepoInfo();
            if (!repoInfo) {
                console.log('No repository info available');
                return [];
            }

            console.log('Making API request to get issues with:', {
                owner: repoInfo.owner,
                repo: repoInfo.repo
            });

            const { data } = await this.octokit.issues.listForRepo({
                owner: repoInfo.owner,
                repo: repoInfo.repo,
                state: 'all'
            });

            // Filter out pull requests
            const issues = data.filter(issue => !('pull_request' in issue));

            console.log('Received response:', {
                issueCount: issues.length
            });

            return issues.map(issue => ({
                number: issue.number,
                title: issue.title,
                body: issue.body || "",
                state: issue.state,
                created_at: issue.created_at,
                updated_at: issue.updated_at,
                user: issue.user ? { login: issue.user.login } : null,
                labels: issue.labels.map(label => ({
                    name: typeof label === 'string' ? label : (label.name || '')
                }))
            }));
        } catch (error: any) {
            console.error('Error fetching issues:', error);
            if (error.response) {
                console.error('Response status:', error.response.status);
                console.error('Response data:', error.response.data);
            }
            vscode.window.showErrorMessage(`Failed to fetch issues: ${error.message}`);
            return [];
        }
    }
} 