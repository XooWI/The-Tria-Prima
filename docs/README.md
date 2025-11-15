# Benefit Guard - Инструкция по установке и запуску

## Описание
**Benefit Guard** - это чат-бот в отечественном мессенджере *VK MAX*, миссия которого заключается в помощи людям, имеющим инвалидность, по поиску доступных им субсидий.

## Предварительные требования
- Минимум 2 ГБ свободного места
- 1 ГБ оперативной памяти
- Стабильное интернет-соединение

## Установка Docker

### Windows
1. **Скачайте Docker Desktop**:
   - Перейдите на [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/)
   - Нажмите "Download for Windows"
   - Выберите версию для вашей системы (Windows 10/11)

2. **Установите Docker Desktop**:
   - Запустите скачанный файл `Docker Desktop Installer.exe`
   - Следуйте инструкциям мастера установки
   - При запросе включите опцию "Use WSL 2 instead of Hyper-V" (рекомендуется)
   - Перезагрузите компьютер после установки

3. **Запустите Docker Desktop**:
   - Найдите Docker Desktop в меню Пуск и запустите
   - Дождитесь полной загрузки (иконка в трее перестанет быть анимированной)

### Linux (Ubuntu/Debian)
```bash
# Обновите систему
sudo apt update && sudo apt upgrade -y

# Установите Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Добавьте пользователя в группу docker
sudo usermod -aG docker $USER

# Перезапустите сессию (выйдите и зайдите обратно)
sudo systemctl enable docker
sudo systemctl start docker
```

### MacOS
1. **Скачайте Docker Desktop**:
   - Перейдите на [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/)
   - Нажмите "Download for Mac"
   - Выберите версию для Intel или Apple Silicon

2. **Установите Docker Desktop**:
   - Откройте скачанный файл `Docker.dmg`
   - Перетащите Docker иконку в папку Applications
   - Запустите Docker из папки Applications

3. **Завершите установку**:
   - Следуйте инструкциям на экране
   - Введите пароль администратора при запросе

## Запуск Benefit Guard
### Способ 1: Запуск из tar архива (оффлайн установка)

Если у вас есть архив `benefit_guard.tar`:

bash

1. **Загрузите образ из архива**

```sh
docker load -i benefit_guard.tar

```
2. **Создайте файл с переменными окружения**
```
cat > .env << EOF
MAX_TOKEN=your_max_token_here
AI_API_KEY=your_ai_api_key_here
AI_BASE_URL=your_ai_base_url_here
EOF
```
3. **Запустите контейнер**
```

docker run -d \
  --name benefit-guard \
  -p 8080:8080 \
  --env-file .env \
  --restart unless-stopped \
  xoowi/benefit_guard:latest
```
### Быстрый запуск 

1. **Создайте папку для проекта**:
   ```bash
   mkdir benefit-guard
   cd benefit-guard
   ```

2. **Создайте файл с переменными окружения**:
   ```bash
   # Windows (PowerShell)
   echo "MAX_TOKEN=your_max_token_here" > .env

   # Linux/MacOS
   cat > .env << EOF
   MAX_TOKEN=your_max_token_here
   EOF
```

3. **Отредактируйте файл .env** и заполните реальные значения:
   - `MAX_TOKEN` - токен бота из VK MAX

4. **Запустите контейнер**:
   ```bash
   docker run -d \
     --name benefit-guard \
     -p 8080:8080 \
     --env-file .env \
     --restart unless-stopped \
     xoowi/benefit_guard:latest
   ```

### Запуск с помощью Docker Compose

1. **Создайте папку и перейдите в неё**:
   ```bash
   mkdir benefit-guard
   cd benefit-guard
   ```

2. **Создайте docker-compose.yml**:
   ```yaml
   version: '3.8'
   services:
     benefit-guard:
       image: xoowi/benefit_guard:latest
       ports:
         - "8080:8080"
       environment:
         - MAX_TOKEN=${MAX_TOKEN}
       restart: unless-stopped
       healthcheck:
         test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1"]
         interval: 30s
         timeout: 10s
         retries: 3
         start_period: 10s
   ```

3. **Создайте файл .env** (как в предыдущем способе)

4. **Запустите приложение**:
   ```bash
   docker-compose up -d
   ```

## Проверка работы

1. **Проверьте статус контейнера**:
   ```bash
   docker ps
   ```

2. **Проверьте логи**:
   ```bash
   docker logs benefit-guard
   ```

3. **Проверьте healthcheck**:
   ```bash
   curl http://localhost:8080/health
   ```

## Остановка и удаление

### Остановка контейнера:
```bash
docker stop benefit-guard
```

### Удаление контейнера:
```bash
docker rm benefit-guard
```

### Полная остановка (для Docker Compose):
```bash
docker-compose down
```
## Решение проблем

### Если порт 8080 занят:
Замените в командах запуска `-p 8080:8080` на `-p 8081:8080` (или любой другой свободный порт)

### Если Docker не запускается:
- Windows: Проверьте, что включена виртуализация в BIOS
- Linux: Выполните `sudo systemctl status docker`
- MacOS: Перезапустите Docker Desktop

### Проверка версии Docker:
```bash
docker --version
docker-compose --version
```

Для дополнительной помощи обращайтесь в документацию Docker или создайте issue в репозитории проекта.