package utilities

import (
	"fmt"
	"github.com/spf13/viper"
)

func GetViperConfig() (string, string, error) {
	viper.SetConfigName("config")
	viper.SetConfigType("yaml")
	viper.AddConfigPath(".")
	err := viper.ReadInConfig()
	if err != nil {
		panic(fmt.Errorf("Fatal error config file: %s \n", err))
		return "", "", err
	}
	githubToken := viper.GetString("github_token")
	githubRepository := viper.GetString("github_repository")

	return githubToken, githubRepository, nil
}
