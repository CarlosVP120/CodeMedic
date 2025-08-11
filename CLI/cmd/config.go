/*
Copyright © 2025 NAME HERE <EMAIL ADDRESS>
*/
package cmd

import (
	"fmt"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
	"log"
)

var (
	newGithubToken      string
	newGithubRepository string
)

// configCmd represents the config command
var configCmd = &cobra.Command{
	Use:   "config",
	Short: "Update your GitHub token or repository settings",
	Long: `The 'config' command allows you to update the GitHub personal access token 
or repository associated with the CodeFixer CLI.

This is useful if your token has changed or if you want to switch to a different repository 
without re-running the full 'init' process.

You can update either setting individually or both at once using the available flags.

Examples:
  medic-cli config --token ghp_abc123
  medic-cli config --repo elcasvi/my-repo
  medic-cli config --token ghp_abc123 --repo elcasvi/my-repo`,
	Run: func(cmd *cobra.Command, args []string) {
		viper.SetConfigName("config")
		viper.SetConfigType("yaml")
		viper.AddConfigPath(".")

		err := viper.ReadInConfig()
		if err != nil {
			log.Fatalf("❌ Failed to read config: %v", err)
		}

		if newGithubToken != "" {
			viper.Set("github_token", newGithubToken)
			fmt.Println("🔑 GitHub token updated.")
		}

		if newGithubRepository != "" {
			viper.Set("github_repository", newGithubRepository)
			fmt.Println("📦 GitHub repository updated.")
		}

		if newGithubToken == "" && newGithubRepository == "" {
			fmt.Println("⚠️  No changes made. Use --token and/or --repo flags.")
			return
		}

		if err := viper.WriteConfig(); err != nil {
			log.Fatalf("❌ Failed to write config: %v", err)
		}

		fmt.Println("✅ Configuration saved.")
	},
}

func init() {
	rootCmd.AddCommand(configCmd)
	configCmd.Flags().StringVarP(&newGithubToken, "token", "t", "", "Github Token")
	configCmd.Flags().StringVarP(&newGithubRepository, "repository", "r", "", "Github Repository(owner/repo)")

	// Here you will define your flags and configuration settings.

	// Cobra supports Persistent Flags which will work for this command
	// and all subcommands, e.g.:
	// configCmd.PersistentFlags().String("foo", "", "A help for foo")

	// Cobra supports local flags which will only run when this command
	// is called directly, e.g.:
	// configCmd.Flags().BoolP("toggle", "t", false, "Help message for toggle")
}
