package utils

import (
	"os"

	maxbot "github.com/max-messenger/max-bot-api-client-go"
)

func GetAPI() (*maxbot.Api, error) {
	return maxbot.New(os.Getenv("MAX_BOT_TOKEN"))
}

