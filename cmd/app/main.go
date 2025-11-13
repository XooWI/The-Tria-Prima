package main

import (
	"log"

	"github.com/XooWI/BenefitBot/internal/utils"
)

func main() {
    // Инициализация бота
    api, err := utils.GetAPI()
    if err != nil {
        log.Fatal("Ошибка инициализации API:", err)
    }

    // Настройка контекстов и graceful shutdown
    ctx, cancel := utils.SetupGracefulShutdown()
    defer cancel()

    // Получение информации о боте
    botInfo, err := utils.GetBotInfo(api, ctx)
    if err != nil {
        log.Printf("Предупреждение: не удалось получить информацию о боте: %v", err)
    } else {
        log.Printf("Бот %s запущен и готов к работе!", botInfo.Name)
    }

    // Запуск обработки сообщений
    if err := utils.StartMessageProcessing(api, ctx); err != nil {
        log.Fatal("Ошибка обработки сообщений:", err)
    }
}