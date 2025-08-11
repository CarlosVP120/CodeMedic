/*
Copyright © 2025 NAME HERE <EMAIL ADDRESS>
*/
package cmd

import (
	"fmt"
	"github.com/spf13/viper"
	"log"

	"github.com/spf13/cobra"
)

// showCmd represents the show command
var showCmd = &cobra.Command{
	Use:   "show",
	Short: "Display your current GitHub CLI configuration",
	Long: `The 'show' command displays the current GitHub token and repository 
configured in your local environment.

This is useful to verify which credentials and repository the CLI will use 
when executing other commands like 'list' or 'fix'.

Examples:
  medic-cli show
  medic-cli show config`,
	Run: func(cmd *cobra.Command, args []string) {
		viper.SetConfigName("config")
		viper.SetConfigType("yaml")
		viper.AddConfigPath(".")

		if err := viper.ReadInConfig(); err != nil {
			log.Fatalf("❌ Could not read config file: %v", err)
		}

		token := viper.GetString("github_token")
		repo := viper.GetString("github_repository")

		fmt.Println("🔧 Current Configuration:")
		fmt.Println("----------------------------")
		fmt.Printf("🔑 GitHub Token: %s\n", maskToken(token))
		fmt.Printf("📦 Repository:   %s\n", repo)
	},
}

func init() {
	rootCmd.AddCommand(showCmd)

	// Here you will define your flags and configuration settings.

	// Cobra supports Persistent Flags which will work for this command
	// and all subcommands, e.g.:
	// showCmd.PersistentFlags().String("foo", "", "A help for foo")

	// Cobra supports local flags which will only run when this command
	// is called directly, e.g.:
	// showCmd.Flags().BoolP("toggle", "t", false, "Help message for toggle")
}
func maskToken(token string) string {
	if len(token) > 10 {
		return token[:4] + "..." + token[len(token)-4:]
	}
	return "(not set)"
}
