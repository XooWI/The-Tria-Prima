package utils

import (
	"fmt"
	"log"

	maxbot "github.com/max-messenger/max-bot-api-client-go"
	"github.com/max-messenger/max-bot-api-client-go/schemes"
)

// HandleUpdate обрабатывает входящее обновление
func HandleUpdate(api *maxbot.Api, update interface{}) error {
	switch upd := update.(type) {
	case *schemes.MessageCreatedUpdate:
		// ЗАПУСКАЕМ в горутине каждое сообщение!
		go func() {
			if err := HandleMessage(api, upd); err != nil {
				log.Printf("Ошибка обработки сообщения: %v", err)
			}
		}()
	default:
		log.Printf("Получен неизвестный тип обновления: %T", update)
	}
	return nil
}

// HandleMessage обрабатывает входящее сообщение
func HandleMessage(api *maxbot.Api, update *schemes.MessageCreatedUpdate) error {
	log.Printf("Получено сообщение от %d: %s",
		update.Message.Sender.UserId, update.Message.Body.Text)

	// Создаем контекст для отправки сообщения
	msgCtx, cancel := CreateMessageContext()
	defer cancel()

	// Генерируем ответ
	response, err := GenerateResponse(update.Message.Body.Text)
	if err != nil {
		return fmt.Errorf("ошибка генерации ответа: %w", err)
	}

	// Отправляем ответ
	_, err = api.Messages.Send(
		msgCtx,
		maxbot.NewMessage().
			SetChat(update.Message.Recipient.ChatId).
			SetText(response),
	)

	if err != nil {
		return fmt.Errorf("ошибка отправки сообщения: %w", err)
	}

	log.Printf("Ответ отправлен пользователю %d", update.Message.Sender.UserId)
	return nil
}
