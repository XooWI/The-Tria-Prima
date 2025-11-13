package utils

import (
    "context"
    "fmt"
    "log"
    
    maxbot "github.com/max-messenger/max-bot-api-client-go"
    "github.com/max-messenger/max-bot-api-client-go/schemes"
)

// GetBotInfo получает информацию о боте
func GetBotInfo(api *maxbot.Api, ctx context.Context) (*schemes.BotInfo, error) {
    info, err := api.Bots.GetBot(ctx)
    if err != nil {
        return nil, fmt.Errorf("ошибка получения информации о боте: %w", err)
    }
    
    fmt.Printf("Информация о боте: %#v\n", info)
    return info, nil
}

// StartMessageProcessing запускает обработку входящих сообщений
func StartMessageProcessing(api *maxbot.Api, ctx context.Context) error {
    log.Println("Запуск обработки сообщений...")
    
    updates := api.GetUpdates(ctx)
    if updates == nil {
        return fmt.Errorf("не удалось получить канал обновлений")
    }
    
    for update := range updates {
        if err := HandleUpdate(api, update); err != nil {
            log.Printf("Ошибка обработки обновления: %v", err)
            // Продолжаем обработку следующих сообщений несмотря на ошибку
        }
    }
    
    log.Println("Обработка сообщений завершена")
    return nil
}