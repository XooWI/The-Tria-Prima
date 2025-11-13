package utils

import (
	"context"
	"os"
	"os/signal"
	"syscall"
	"time"
)

func SetupGracefulShutdown() (context.Context, context.CancelFunc) {
	ctx, cancel := context.WithCancel(context.Background()) 

	go func() {

		exit := make(chan os.Signal, 1)
		signal.Notify(exit, os.Interrupt, syscall.SIGTERM)

		<-exit
		cancel()
	}()

	return ctx, cancel
}

func CreateMessageContext() (context.Context, context.CancelFunc) {
	return context.WithTimeout(context.Background(), 10*time.Second)
}