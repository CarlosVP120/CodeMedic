/*
Copyright © 2025 NAME HERE <EMAIL ADDRESS>
*/
package cmd

import (
	"os"

	"github.com/spf13/cobra"
)

// rootCmd represents the base command when called without any subcommands
var rootCmd = &cobra.Command{
	Use:   "medic-cli",
	Short: "AI-powered GitHub issue fixer from the command line",
	Long: `Medic CLI is a developer productivity tool that uses AI to analyze and fix issues from a GitHub repository.

Features:
  - Authenticate with your GitHub token
  - Retrieve and list open issues
  - Send issues to an AI agent for automatic resolution
  - Automatically create branches, apply fixes, and open pull requests

Examples:
  medic-cli auth --token <your_token>
  medic-cli list-issues
  medic-cli fix --issue 42
  medic-cli fix-all

This tool streamlines the debugging and patching process by integrating GitHub and AI directly into your terminal workflow.`,
	// Uncomment the following line if your bare application
	// has an action associated with it:
	// Run: func(cmd *cobra.Command, args []string) { },
}

// Execute adds all child commands to the root command and sets flags appropriately.
// This is called by main.main(). It only needs to happen once to the rootCmd.
func Execute() {
	err := rootCmd.Execute()
	if err != nil {
		os.Exit(1)
	}
}

func init() {
	// Here you will define your flags and configuration settings.
	// Cobra supports persistent flags, which, if defined here,
	// will be global for your application.

	// rootCmd.PersistentFlags().StringVar(&cfgFile, "config", "", "config file (default is $HOME/.codemediccli.yaml)")

	// Cobra also supports local flags, which will only run
	// when this action is called directly.
	rootCmd.Flags().BoolP("toggle", "t", false, "Help message for toggle")
}
