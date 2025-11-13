FROM golang:1.25.4 AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o max-bot ./cmd/app

FROM alpine:latest
RUN apk --no-cache add ca-certificates
RUN apk add --no-cache python3

RUN addgroup -S appgroup && adduser -S appuser -G appgroup
RUN mkdir -p /app && chown appuser:appgroup /app

WORKDIR /app
COPY --from=builder /app/max-bot .
COPY --from=builder /app/neuro ./neuro

# Устанавливаем переменную окружения
ENV NEURO_PATH=/app/neuro

RUN chown -R appuser:appgroup /app
USER appuser
EXPOSE 8080
CMD ["./max-bot"]