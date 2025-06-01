package utilities

import "time"

type GitHubCredentials struct {
	Token          string `json:"token"`
	RepositoryName string `json:"repository_name"`
}

type GithubIssueData struct {
	Number    int       `json:"number"`
	Title     string    `json:"title"`
	Body      string    `json:"body"`
	State     string    `json:"state"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

type FixCodeRequest struct {
	GithubCredentials GitHubCredentials `json:"github_credentials"`
	GithubIssueData   GithubIssueData   `json:"issue_data"`
}

type AgentResponse struct {
	Status string `json:"status"`
	Data   struct {
		Messages []string `json:"messages"`
		Summary  string   `json:"summary"`
	} `json:"data"`
}
