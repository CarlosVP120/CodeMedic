package utilities

import (
	"context"
	"fmt"
	"github.com/google/go-github/v72/github"
	"golang.org/x/oauth2"
	"log"
	"strings"
)

func GetGithubIssue(githubToken string, githubRepository string, issueNumber int) (GithubIssueData, error) {
	ctx := context.Background()

	ts := oauth2.StaticTokenSource(&oauth2.Token{AccessToken: githubToken})
	tc := oauth2.NewClient(ctx, ts)
	client := github.NewClient(tc)

	parts := strings.SplitN(githubRepository, "/", 2)
	if len(parts) != 2 {
		return GithubIssueData{}, fmt.Errorf("invalid repository format (expected 'owner/repo')")
	}
	owner, repo := parts[0], parts[1]

	ghIssue, _, err := client.Issues.Get(ctx, owner, repo, issueNumber)
	if err != nil {
		return GithubIssueData{}, fmt.Errorf("failed to fetch issue #%d: %w", issueNumber, err)
	}

	return GithubIssueData{
		Number:    ghIssue.GetNumber(),
		Title:     ghIssue.GetTitle(),
		Body:      ghIssue.GetBody(),
		State:     ghIssue.GetState(),
		CreatedAt: ghIssue.GetCreatedAt().Time,
		UpdatedAt: ghIssue.GetUpdatedAt().Time,
	}, nil
}

func GetGitHubIssues(githubToken string, githubRepository string) ([]GithubIssueData, error) {
	parts := strings.SplitN(githubRepository, "/", 2)
	if len(parts) != 2 {
		log.Fatalf("Invalid github repository name: %s", githubRepository)
	}
	owner := parts[0]
	repo := parts[1]

	ctx := context.Background()

	ts := oauth2.StaticTokenSource(&oauth2.Token{AccessToken: githubToken})
	tc := oauth2.NewClient(ctx, ts)

	client := github.NewClient(tc)

	opts := &github.IssueListByRepoOptions{
		State: "open",
		ListOptions: github.ListOptions{
			Page:    1,
			PerPage: 30,
		},
	}

	var retrievedIssues []GithubIssueData

	for {
		issues, resp, err := client.Issues.ListByRepo(ctx, owner, repo, opts)
		if err != nil {
			return nil, fmt.Errorf("failed to fetch issues: %w", err)
		}

		for _, issue := range issues {
			if issue.IsPullRequest() {
				continue
			}

			retrievedIssues = append(retrievedIssues, GithubIssueData{
				Number:    issue.GetNumber(),
				Title:     issue.GetTitle(),
				Body:      issue.GetBody(),
				State:     issue.GetState(),
				CreatedAt: issue.GetCreatedAt().Time,
				UpdatedAt: issue.GetUpdatedAt().Time,
			})
		}

		if resp.NextPage == 0 {
			break
		}
		opts.ListOptions.Page = resp.NextPage
	}

	return retrievedIssues, nil
}
