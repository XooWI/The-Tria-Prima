package utils

import (
	"os"
	"net/http"
	"log"
)

func StartHTTPServer() {
    http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
        w.WriteHeader(http.StatusOK)
        w.Write([]byte("OK"))
    })
    
    port := os.Getenv("PORT")
    if port == "" {
        port = "8080"
    }
    
    log.Printf("HTTP сервер запущен на порту %s", port)
    if err := http.ListenAndServe(":"+port, nil); err != nil {
        log.Printf("Ошибка HTTP сервера: %v", err)
    }
}