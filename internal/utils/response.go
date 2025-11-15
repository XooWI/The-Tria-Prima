package utils

import (
	"os"
	"os/exec"
	"strings"
	"bytes"
	"log"
	"fmt"
)

// GenerateResponse генерирует ответ на сообщение пользователя
func GenerateResponse(userMessage string) (string, error) {
	if userMessage == "" {
		return "Привет! Я бот для поиска льгот для инвалидов. Напишите мне, какие льготы вас интересуют, например: 'парковка для инвалидов 2 группы' или 'лекарства для инвалидов'.", nil
	}

	// Очищаем сообщение от лишних пробелов
	userMessage = strings.TrimSpace(userMessage)

	// Обработка специальных команд на стороне Go (для скорости)
	switch strings.ToLower(userMessage) {
	case "/start", "start", "начать":
		return GetWelcomeMessage(), nil
	case "/help", "help", "помощь":
		return GetHelpMessage(), nil
	case "/stats", "статистика":
		return GetStatsMessage(), nil
	}

	// Вызов Python-скрипта для обработки сложных запросов
	response, err := callPythonScript(userMessage)
	if err != nil {
		log.Printf("Ошибка при вызове Python-скрипта: %v", err)
		return GetFallbackResponse(userMessage), nil
	}

	return response, nil
}

// callPythonScript вызывает Python-скрипт для поиска льгот
func callPythonScript(query string) (string, error) {
	log.Printf("Вызов Python-скрипта с запросом: '%s'", query)

	// Пытаемся найти папку neuro относительно текущей директории
	scriptPath := "neuro/main.py"

	// Проверяем существование файла
	if _, err := os.Stat(scriptPath); os.IsNotExist(err) {
		// Если файл не найден, пробуем другие возможные пути
		possiblePaths := []string{
			"neuro/main.py",
			"../neuro/main.py",
			"../../neuro/main.py",
			"./neuro/main.py",
		}

		for _, path := range possiblePaths {
			if _, err := os.Stat(path); err == nil {
				scriptPath = path
				break
			}
		}
	}

	log.Printf("Используем путь к скрипту: %s", scriptPath)
	cmd := exec.Command("python3", scriptPath, query)

	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	err := cmd.Run()

	log.Printf("STDOUT: %s", stdout.String())
	log.Printf("STDERR: %s", stderr.String())

	if err != nil {
		return "", fmt.Errorf("ошибка: %w, stderr: %s", err, stderr.String())
	}

	return strings.TrimSpace(stdout.String()), nil
}
