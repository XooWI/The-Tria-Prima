package main

import (
	"context"
	"fmt"
	"log"
	"time"

	"github.com/XooWI/BenefitBot/internal/utils"
)

func main(){
	api, err := utils.GetAPI()
	if err != nil {
		log.Fatal(err)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	info, err := api.Bots.GetBot(ctx)
	fmt.Printf("Get me: %#v %#v", info, err)
}
