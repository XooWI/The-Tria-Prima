package utils

import "fmt"

// BotError представляет ошибку бота с контекстом
type BotError struct {
    Operation string
    Err       error
}

func (e *BotError) Error() string {
    return fmt.Sprintf("%s: %v", e.Operation, e.Err)
}

func NewBotError(operation string, err error) error {
    return &BotError{
        Operation: operation,
        Err:       err,
    }
}