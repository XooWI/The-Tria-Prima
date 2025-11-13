FROM golang:1.25.4 AS builder

WORKDIR /app

# Копируем файлы зависимостей
COPY go.mod go.sum ./
RUN go mod download

# Копируем ВСЕ исходные файлы
COPY . .

# Собираем бинарник из правильной директории
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o max-bot ./cmd/app

# Финальный образ
FROM alpine:latest

RUN apk --no-cache add ca-certificates

WORKDIR /root/

# Копируем бинарник из builder
COPY --from=builder /app/max-bot .

# Создаем непривилегированного пользователя
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

# Экспортируем порт
EXPOSE 8080

# Запускаем бота
CMD ["./max-bot"]
