/*
Copyright © 2025 NAME HERE <EMAIL ADDRESS>
*/
package cmd

import (
	"context"
	"fmt"
	"github.com/google/go-github/v72/github"
	"github.com/joho/godotenv"
	"github.com/spf13/cobra"
	"golang.org/x/oauth2"
	"log"
	"os"
)

// listCmd represents the list command
var listCmd = &cobra.Command{
	Use:   "list",
	Short: "A brief description of your command",
	Long: `A longer description that spans multiple lines and likely contains examples
and usage of using your command. For example:

Cobra is a CLI library for Go that empowers applications.
This application is a tool to generate the needed files
to quickly create a Cobra application.`,
	Run: func(cmd *cobra.Command, args []string) {
		getGitHubIssues()
	},
}

func init() {
	rootCmd.AddCommand(listCmd)
}

func getGitHubIssues() {
	ctx := context.Background()

	// Optional: Use GITHUB_TOKEN to increase rate limits or access private repos
	err := godotenv.Load()
	if err != nil {
		log.Fatal("❌ Error loading .env file")
	}
	// Use the environment variables
	token := os.Getenv("GITHUB_TOKEN")
	fmt.Println("token", token)
	ts := oauth2.StaticTokenSource(&oauth2.Token{AccessToken: token})
	tc := oauth2.NewClient(ctx, ts)

	client := github.NewClient(tc)

	owner := "Elcasvi"             // replace with your GitHub username or org
	repo := "Code-Fixer-LLM-Agent" // replace with your repository name

	opts := &github.IssueListByRepoOptions{
		State: "open",
		ListOptions: github.ListOptions{
			Page:    1,  // start with the first page
			PerPage: 30, // number of issues per page
		},
	}

	for {
		issues, resp, err := client.Issues.ListByRepo(ctx, owner, repo, opts)
		if err != nil {
			log.Fatalf("Failed to fetch issues: %v", err)
		}

		for _, issue := range issues {
			if issue.IsPullRequest() {
				continue
			}
			fmt.Printf("#%d: %s\n", *issue.Number, *issue.Title)
		}

		// Update the page for the next loop iteration
		if resp.NextPage == 0 {
			break
		}
		opts.ListOptions.Page = resp.NextPage
	}
}
