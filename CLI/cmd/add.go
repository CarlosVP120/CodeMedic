/*
Copyright © 2025 NAME HERE <EMAIL ADDRESS>
*/
package cmd

import (
	"fmt"
	"github.com/spf13/cobra"
	"strconv"
)

// addCmd represents the add command
var addCmd = &cobra.Command{
	Use:   "add",
	Short: "A brief description of your command",
	Long: `A longer description that spans multiple lines and likely contains examples
and usage of using your command. For example:

Cobra is a CLI library for Go that empowers applications.
This application is a tool to generate the needed files
to quickly create a Cobra application.`,
	Run: func(cmd *cobra.Command, args []string) {
		sum := 0
		for _, args := range args {
			num, err := strconv.Atoi(args)
			if err != nil {
				fmt.Println(err)
			}
			sum += num
		}
		fmt.Println("The result of the addition is: ", sum)
	},
}

func init() {
	rootCmd.AddCommand(addCmd)

}
