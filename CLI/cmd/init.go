/*
Copyright © 2025 NAME HERE <EMAIL ADDRESS>
*/
package cmd

import (
	"bufio"
	"fmt"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
	"log"
	"os"
	"strings"
)

// initCmd represents the init command
var initCmd = &cobra.Command{
	Use:   "init",
	Short: "Initialize your GitHub configuration for medic-cli",
	Long: `The 'init' command sets up your GitHub credentials and target repository 
for use with the CodeFixer CLI.

You will be prompted to enter your GitHub personal access token and the repository 
you want to work with (in the format 'owner/repo'). This configuration will be saved 
locally in a config file for future use.

Examples:
  medic-cli init
  medic-cli init my-project`,
	Run: func(cmd *cobra.Command, args []string) {
		reader := bufio.NewReader(os.Stdin)
		fmt.Print("Enter your github token:")
		token, _ := reader.ReadString('\n')

		fmt.Print("Enter your github repository (e.g. username/repo):")
		repo, _ := reader.ReadString('\n')

		token = strings.TrimSpace(token)
		repo = strings.TrimSpace(repo)
		viper.Set("github_token", token)
		viper.Set("github_repository", repo)

		viper.SetConfigName("config")
		viper.SetConfigType("yaml")
		viper.AddConfigPath(".")

		err := viper.WriteConfigAs("config.yaml")
		if err != nil {
			log.Fatalf("Error writing config.yaml: %v", err)
		}
		print("Configuration file written to config.yaml")
	},
}

func init() {
	rootCmd.AddCommand(initCmd)

	// Here you will define your flags and configuration settings.

	// Cobra supports Persistent Flags which will work for this command
	// and all subcommands, e.g.:
	// initCmd.PersistentFlags().String("foo", "", "A help for foo")

	// Cobra supports local flags which will only run when this command
	// is called directly, e.g.:
	// initCmd.Flags().BoolP("toggle", "t", false, "Help message for toggle")
}
