# 🚀 Полное руководство по развертыванию VoiceAI Dashboard на VPS

## 📋 Обзор развертывания

Система будет развернута на поддомене `dashboard.aloda.agency` с использованием Docker и nginx reverse proxy.

**Архитектура:**
- Основной сайт: `aloda.agency` (порт 80)
- Dashboard: `dashboard.aloda.agency` (внутренний порт 8000)
- PostgreSQL: контейнер базы данных
- nginx: reverse proxy для маршрутизации

---

## 🎯 1. Подготовка VPS сервера

### 1.1 Подключение к серверу
```bash
ssh root@your-server-ip
# или
ssh user@your-server-ip
```

### 1.2 Обновление системы
```bash
apt update && apt upgrade -y
```

### 1.3 Установка Docker и Docker Compose
```bash
# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Добавление пользователя в группу docker (если не root)
usermod -aG docker $USER

# Установка Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Проверка установки
docker --version
docker-compose --version
```

---

## 🏗️ 2. Структура проекта на сервере

### 2.1 Создание директорий
```bash
# Переход в домашнюю директорию или /opt
cd /opt

# Создание структуры проекта
mkdir -p voiceai-dashboard
cd voiceai-dashboard

# Создание поддиректорий
mkdir -p {app,postgres-data,nginx,logs}
```

### 2.2 Итоговая структура
```
/opt/voiceai-dashboard/
├── app/                    # Код приложения
├── postgres-data/          # Данные PostgreSQL
├── nginx/                  # Конфигурация nginx
├── logs/                   # Логи
├── docker-compose.yml      # Docker Compose конфигурация
└── .env                    # Переменные окружения
```

---

## 🐳 3. Docker конфигурация

### 3.1 Создание Dockerfile для приложения
```bash
cat > app/Dockerfile << 'EOF'
FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

# Копирование requirements.txt и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY . .

# Создание пользователя для безопасности
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Открытие порта
EXPOSE 8000

# Команда запуска
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF
```

### 3.2 Создание requirements.txt для продакшена
```bash
cat > app/requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
python-multipart==0.0.6
jinja2==3.1.2
python-dotenv==1.0.0
loguru==0.7.2
google-api-python-client==2.108.0
google-auth-httplib2==0.1.1
google-auth-oauthlib==1.1.0
openai==1.3.7
pandas==2.1.3
asyncio==3.4.3
pathlib==1.0.1
aiofiles==23.2.1
EOF
```

### 3.3 Создание docker-compose.yml
```bash
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  # PostgreSQL база данных
  postgres:
    image: postgres:15
    container_name: voiceai_postgres
    environment:
      POSTGRES_DB: voiceai_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - ./postgres-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped
    networks:
      - voiceai-network

  # VoiceAI Dashboard приложение
  voiceai-app:
    build:
      context: ./app
      dockerfile: Dockerfile
    container_name: voiceai_dashboard
    environment:
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/voiceai_db
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - GOOGLE_SERVICE_ACCOUNT_FILE=${GOOGLE_SERVICE_ACCOUNT_FILE}
      - GOOGLE_DRIVE_FOLDER_ID=${GOOGLE_DRIVE_FOLDER_ID}
      - GOOGLE_SPREADSHEET_ID=${GOOGLE_SPREADSHEET_ID}
      - LOG_LEVEL=INFO
      - POLL_INTERVAL_SECONDS=60
      - SAVE_TO_DATABASE=true
      - SAVE_TO_SHEETS=false
    volumes:
      - ./logs:/app/logs
      - ./app/temp_audio:/app/temp_audio
    ports:
      - "8000:8000"
    depends_on:
      - postgres
    restart: unless-stopped
    networks:
      - voiceai-network

networks:
  voiceai-network:
    driver: bridge

volumes:
  postgres-data:
EOF
```

---

## 🌐 4. Конфигурация nginx

### 4.1 Обновление nginx конфигурации для поддомена
```bash
# Создание конфигурации для поддомена
cat > /etc/nginx/sites-available/dashboard.aloda.agency << 'EOF'
server {
    listen 80;
    server_name dashboard.aloda.agency;

    # Логи
    access_log /var/log/nginx/dashboard.aloda.agency.access.log;
    error_log /var/log/nginx/dashboard.aloda.agency.error.log;

    # Проксирование к VoiceAI Dashboard
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket поддержка (если нужна)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Таймауты
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Статические файлы (если есть)
    location /static/ {
        alias /opt/voiceai-dashboard/app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Безопасность
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
EOF

# Активация конфигурации
ln -s /etc/nginx/sites-available/dashboard.aloda.agency /etc/nginx/sites-enabled/
```

### 4.2 Проверка и перезагрузка nginx
```bash
# Проверка конфигурации
nginx -t

# Перезагрузка nginx
systemctl reload nginx
```

---

## 🔧 5. Настройка DNS

### 5.1 Добавление A-записи для поддомена
В панели управления DNS провайдера добавить:
```
Type: A
Name: dashboard
Value: YOUR_SERVER_IP
TTL: 300 (или по умолчанию)
```

### 5.2 Проверка DNS
```bash
# Проверка разрешения DNS
nslookup dashboard.aloda.agency
dig dashboard.aloda.agency
```

---

## 📁 6. Загрузка кода приложения

### 6.1 Загрузка через Git (рекомендуется)
```bash
cd /opt/voiceai-dashboard/app

# Клонирование репозитория
git clone https://github.com/your-username/voiceai-dashboard.git .

# Или загрузка через scp/rsync с локальной машины
```

### 6.2 Загрузка через scp (альтернативный способ)
```bash
# С локальной машины
scp -r /path/to/local/VoiceAi/* user@server-ip:/opt/voiceai-dashboard/app/
```

---

## 🔐 7. Конфигурация переменных окружения

### 7.1 Создание .env файла
```bash
cat > .env << 'EOF'
# PostgreSQL пароль
POSTGRES_PASSWORD=your_strong_postgres_password_here

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Google APIs Configuration
GOOGLE_SERVICE_ACCOUNT_FILE=clean-outcome-472421-k0-f39e1867604f.json

# Google Drive Configuration
GOOGLE_DRIVE_FOLDER_ID=your_drive_folder_id

# Google Sheets Configuration
GOOGLE_SPREADSHEET_ID=your_spreadsheet_id

# Manager sheet names
ELIZAVETA_SHEET_NAME=Входящие Елизавета
VLADIMIR_SHEET_NAME=Входящие Владимир
NADEZHDA_SHEET_NAME=Входящие Надежда
ANALYSIS_SHEET_NAME=Анализ звонков

# Application settings
LOG_LEVEL=INFO
POLL_INTERVAL_SECONDS=60
SAVE_TO_DATABASE=true
SAVE_TO_SHEETS=false
EOF
```

### 7.2 Загрузка Google Service Account файла
```bash
# Загрузить файл clean-outcome-472421-k0-f39e1867604f.json в директорию app/
scp local/path/to/clean-outcome-472421-k0-f39e1867604f.json user@server:/opt/voiceai-dashboard/app/
```

---

## 🚀 8. Запуск приложения

### 8.1 Сборка и запуск контейнеров
```bash
cd /opt/voiceai-dashboard

# Сборка образов
docker-compose build

# Запуск в фоновом режиме
docker-compose up -d
```

### 8.2 Проверка статуса контейнеров
```bash
# Проверка запущенных контейнеров
docker-compose ps

# Просмотр логов
docker-compose logs -f voiceai-app
docker-compose logs -f postgres
```

---

## 🗄️ 9. Миграция данных PostgreSQL

### 9.1 Если есть существующие данные для миграции
```bash
# Копирование SQLite базы на сервер (если нужно)
scp local/path/to/voiceai_calls.db user@server:/tmp/

# Запуск миграции внутри контейнера
docker-compose exec voiceai-app python migrate_to_postgresql.py
```

### 9.2 Создание начальной схемы базы данных
```bash
# Выполнение в контейнере приложения
docker-compose exec voiceai-app python -c "
from src.database_service import DatabaseService
from src.database_models import Base
import os

# Создание всех таблиц
db = DatabaseService()
Base.metadata.create_all(db.engine)
print('✅ Database schema created successfully!')
"
```

---

## 🔒 10. SSL сертификат (HTTPS)

### 10.1 Установка Certbot
```bash
apt install certbot python3-certbot-nginx -y
```

### 10.2 Получение SSL сертификата
```bash
# Получение сертификата для поддомена
certbot --nginx -d dashboard.aloda.agency

# Настройка автоматического обновления
crontab -e
# Добавить строку:
0 12 * * * /usr/bin/certbot renew --quiet
```

---

## 📊 11. Мониторинг и логи

### 11.1 Настройка логирования
```bash
# Создание директории для логов
mkdir -p /opt/voiceai-dashboard/logs

# Настройка ротации логов
cat > /etc/logrotate.d/voiceai-dashboard << 'EOF'
/opt/voiceai-dashboard/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
}
EOF
```

### 11.2 Команды для мониторинга
```bash
# Просмотр логов приложения
docker-compose logs -f voiceai-app

# Мониторинг ресурсов
docker stats

# Проверка здоровья контейнеров
docker-compose ps
```

---

## 🔄 12. Автоматические обновления и бэкапы

### 12.1 Скрипт обновления приложения
```bash
cat > /opt/voiceai-dashboard/update.sh << 'EOF'
#!/bin/bash
set -e

echo "🔄 Starting VoiceAI Dashboard update..."

cd /opt/voiceai-dashboard

# Остановка контейнеров
docker-compose down

# Обновление кода (если используется Git)
cd app
git pull origin main

# Пересборка и запуск
cd ..
docker-compose build
docker-compose up -d

echo "✅ Update completed successfully!"
EOF

chmod +x /opt/voiceai-dashboard/update.sh
```

### 12.2 Скрипт бэкапа базы данных
```bash
cat > /opt/voiceai-dashboard/backup.sh << 'EOF'
#!/bin/bash
set -e

BACKUP_DIR="/opt/voiceai-dashboard/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

echo "📦 Starting database backup..."

# Создание бэкапа PostgreSQL
docker-compose exec -T postgres pg_dump -U postgres voiceai_db > $BACKUP_DIR/voiceai_db_$DATE.sql

# Сжатие бэкапа
gzip $BACKUP_DIR/voiceai_db_$DATE.sql

# Удаление старых бэкапов (старше 30 дней)
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "✅ Backup completed: voiceai_db_$DATE.sql.gz"
EOF

chmod +x /opt/voiceai-dashboard/backup.sh

# Добавление в crontab для ежедневного бэкапа
echo "0 2 * * * /opt/voiceai-dashboard/backup.sh" | crontab -
```

---

## 🧪 13. Тестирование развертывания

### 13.1 Проверка доступности
```bash
# Проверка локального доступа
curl -I http://localhost:8000

# Проверка через поддомен
curl -I http://dashboard.aloda.agency
```

### 13.2 Проверка базы данных
```bash
# Подключение к PostgreSQL
docker-compose exec postgres psql -U postgres -d voiceai_db

# Внутри psql:
\dt  # Показать таблицы
SELECT COUNT(*) FROM users;  # Проверить данные
\q   # Выход
```

---

## 🚨 14. Устранение неполадок

### 14.1 Общие проблемы и решения

**Проблема: Контейнер не запускается**
```bash
# Проверка логов
docker-compose logs voiceai-app

# Проверка образа
docker images

# Пересборка образа
docker-compose build --no-cache voiceai-app
```

**Проблема: База данных недоступна**
```bash
# Проверка контейнера PostgreSQL
docker-compose logs postgres

# Проверка сетевого подключения
docker-compose exec voiceai-app ping postgres
```

**Проблема: 502 Bad Gateway**
```bash
# Проверка nginx логов
tail -f /var/log/nginx/error.log

# Проверка статуса приложения
curl -I http://localhost:8000

# Проверка nginx конфигурации
nginx -t
```

### 14.2 Команды для диагностики
```bash
# Проверка портов
netstat -tulpn | grep :8000
netstat -tulpn | grep :80

# Проверка процессов
ps aux | grep nginx
ps aux | grep docker

# Проверка дискового пространства
df -h

# Проверка памяти
free -h
```

---

## 📋 15. Финальный чеклист развертывания

### ✅ Предварительная подготовка:
- [ ] VPS сервер готов и доступен
- [ ] Docker и Docker Compose установлены
- [ ] nginx установлен и настроен
- [ ] DNS запись для поддомена создана

### ✅ Конфигурация:
- [ ] Структура директорий создана
- [ ] docker-compose.yml создан
- [ ] Dockerfile создан
- [ ] nginx конфигурация для поддомена создана
- [ ] .env файл настроен

### ✅ Развертывание:
- [ ] Код приложения загружен
- [ ] Google Service Account файл загружен
- [ ] Контейнеры собраны и запущены
- [ ] База данных инициализирована
- [ ] SSL сертификат получен

### ✅ Тестирование:
- [ ] Приложение доступно на dashboard.aloda.agency
- [ ] База данных работает корректно
- [ ] Логи пишутся правильно
- [ ] Бэкапы настроены

---

## 🎉 Готово!

После выполнения всех шагов ваш VoiceAI Dashboard будет доступен по адресу:
**https://dashboard.aloda.agency**

Система будет работать в Docker контейнерах с автоматическими бэкапами и мониторингом.