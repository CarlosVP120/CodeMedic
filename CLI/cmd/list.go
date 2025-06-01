/*
Copyright © 2025 NAME HERE <EMAIL ADDRESS>
*/
package cmd

import (
	"fmt"
	"github.com/spf13/cobra"
	"log"
	"medic-cli/utilities"
)

var listIssueNumber int

// listCmd represents the list command
var listCmd = &cobra.Command{
	Use:   "list",
	Short: "List open GitHub issues from the configured repository",
	Long: `The 'list' command fetches and displays open issues from the repository 
you have configured using the 'init' or 'config' command.

This allows you to quickly review outstanding issues before deciding to fix one 
using the 'fix' command.

Examples:
  medic-cli list
  medic-cli list --label bug
  medic-cli list --issue 42`,
	Run: func(cmd *cobra.Command, args []string) {
		githubToken, githubRepository, _ := utilities.GetViperConfig()
		if listIssueNumber > 0 {
			selectedIssueNumber := listIssueNumber
			issue, err := utilities.GetGithubIssue(githubToken, githubRepository, selectedIssueNumber)
			if err != nil {
				log.Fatalf("Error while getting issue %v: %v", selectedIssueNumber, err)
			}
			fmt.Printf("Selected issue:\n%+v", issue)
		} else {
			githubToken, githubRepository, _ := utilities.GetViperConfig()
			githubIssues, _ := utilities.GetGitHubIssues(githubToken, githubRepository)
			if len(githubIssues) == 0 {
				fmt.Println("No GitHub issues found.")
				return
			}
			for _, issue := range githubIssues {
				fmt.Printf("#%d: %s\n", issue.Number, issue.Title)
			}
		}
	},
}

func init() {
	rootCmd.AddCommand(listCmd)
	listCmd.Flags().IntVarP(&listIssueNumber, "issue", "i", 0, "GithubIssueData number")
}
