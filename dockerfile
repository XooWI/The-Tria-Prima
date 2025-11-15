# Используем мультиплатформенный базовый образ
FROM --platform=$BUILDPLATFORM golang:1.25.4 AS builder

# Устанавливаем аргументы для целевой платформы
ARG TARGETOS
ARG TARGETARCH

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .

# Сборка с учетом целевой платформы
RUN CGO_ENABLED=0 GOOS=$TARGETOS GOARCH=$TARGETARCH go build -a -installsuffix cgo -o max-bot ./cmd/app

# Мультиплатформенный базовый образ
FROM alpine:latest

# Устанавливаем необходимые пакеты
RUN apk --no-cache add \
    ca-certificates \
    python3 \
    && rm -rf /var/cache/apk/*

# Создаем пользователя
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

WORKDIR /app

# Копируем бинарник и нейросеть
COPY --from=builder --chown=appuser:appgroup /app/max-bot .
COPY --from=builder --chown=appuser:appgroup /app/neuro ./neuro

ENV NEURO_PATH=/app/neuro

USER appuser
EXPOSE 8080
CMD ["./max-bot"]
