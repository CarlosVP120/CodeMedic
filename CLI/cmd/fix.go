/*
Copyright © 2025 NAME HERE <EMAIL ADDRESS>
*/
package cmd

import (
	"fmt"
	"github.com/briandowns/spinner"
	"github.com/manifoldco/promptui"
	"github.com/spf13/cobra"
	"log"
	"medic-cli/utilities"
	"time"
)

var fixIssueNumber int

// fixCmd represents the fix command
var fixCmd = &cobra.Command{
	Use:   "fix",
	Short: "Select and fix a GitHub issue using the Code Medic AI agent",
	Long: `The 'fix' command allows you to choose an issue from your configured GitHub repository 
and automatically send it to an AI agent for analysis and resolution.

You can either:
  - Select an issue interactively using arrow keys, or
  - Provide an issue number directly via the --issue flag.

The AI agent will process the issue and attempt to generate a fix based on the problem described.

Examples:
  medic-cli fix                  # Use interactive selection
  medic-cli fix --issue 42       # Directly fix issue #42`,
	Run: func(cmd *cobra.Command, args []string) {
		githubToken, githubRepository, _ := utilities.GetViperConfig()

		creds := utilities.GitHubCredentials{
			Token:          githubToken,
			RepositoryName: githubRepository,
		}

		if fixIssueNumber > 0 {
			issue, err := utilities.GetGithubIssue(githubToken, githubRepository, fixIssueNumber)
			if err != nil {
				log.Fatalf("❌ Error while getting issue #%d: %v", fixIssueNumber, err)
			}
			fmt.Printf("📌 Selected issue:\n%+v\n", issue)
			request := utilities.FixCodeRequest{
				GithubCredentials: creds,
				GithubIssueData:   issue,
			}

			agentResponse, err := callFixIssue(request)
			if err != nil {
				log.Fatalf("❌ Error while fixing issue #%d: %v", issue.Number, err)
			}
			printAgentResponse(agentResponse)
			return
		}

		// Interactive mode
		githubIssues, err := utilities.GetGitHubIssues(githubToken, githubRepository)
		if err != nil {
			log.Fatalf("❌ Failed to get GitHub issues: %v", err)
		}
		if len(githubIssues) == 0 {
			fmt.Println("📭 No GitHub issues found.")
			return
		}

		var issueTitles []string
		for _, issue := range githubIssues {
			issueTitles = append(issueTitles, fmt.Sprintf("#%d: %s", issue.Number, issue.Title))
		}

		prompt := promptui.Select{
			Label: "Select issue to fix",
			Items: issueTitles,
		}

		index, result, err := prompt.Run()
		if err != nil {
			log.Fatalf("❌ Prompt failed: %v", err)
		}

		selectedIssue := githubIssues[index]
		fmt.Printf("✅ You selected: %s\n", result)

		request := utilities.FixCodeRequest{
			GithubCredentials: creds,
			GithubIssueData:   selectedIssue,
		}

		s := spinner.New(spinner.CharSets[14], 100*time.Millisecond) // ⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏
		s.Prefix = "🧠 Thinking... "
		s.Start()

		agentResponse, err := callFixIssue(request)
		s.Stop()

		if err != nil {
			log.Fatalf("❌ Error while fixing issue #%d: %v\nRun with DEBUG=1 for more information.", selectedIssue.Number, err)
		}
		fmt.Println("\n✅ Successfully received AI response!")
		printAgentResponse(agentResponse)
	},
}

func init() {
	rootCmd.AddCommand(fixCmd)
	fixCmd.Flags().IntVarP(&fixIssueNumber, "issue", "i", 0, "Specify an issue number to fix directly")

	// Here you will define your flags and configuration settings.

	// Cobra supports Persistent Flags which will work for this command
	// and all subcommands, e.g.:
	// fixCmd.PersistentFlags().String("foo", "", "A help for foo")

	// Cobra supports local flags which will only run when this command
	// is called directly, e.g.:
	// fixCmd.Flags().BoolP("toggle", "t", false, "Help message for toggle")
}

func callFixIssue(req utilities.FixCodeRequest) (utilities.AgentResponse, error) {
	return utilities.FixIssue(req)
}
func printAgentResponse(resp utilities.AgentResponse) {
	fmt.Println("🧠 AI Response Summary:")
	fmt.Printf("📋 Summary: %s\n", resp.Summary)

	fmt.Println("\n💬 Messages:")
	if len(resp.Messages) == 0 {
		fmt.Println("  (No messages)")
	} else {
		for i, msg := range resp.Messages {
			fmt.Printf("  %d. %s\n", i+1, msg)
		}
	}

	fmt.Println("\n🛠️ Tool Calls:")
	if len(resp.ToolPath) == 0 {
		fmt.Println("  (No tools used)")
	} else {
		for i, tool := range resp.ToolPath {
			fmt.Printf("  %d. %s\n", i+1, tool)
		}
	}
}
