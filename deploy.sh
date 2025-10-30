#!/bin/bash

# 🚀 VoiceAI Dashboard Deployment Script
# Автоматическое развертывание на VPS с dashboard.aloda.agency

set -e  # Остановка при ошибке

# Цвета для логов
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции логирования
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Проверка запуска от root или с sudo
check_permissions() {
    if [[ $EUID -ne 0 ]]; then
        log_error "Скрипт должен запускаться от пользователя root или с sudo"
        log_info "Запустите: sudo $0"
        exit 1
    fi
}

# Проверка системы
check_system() {
    log_info "Проверка системы..."
    
    # Проверка Ubuntu/Debian
    if ! command -v apt &> /dev/null; then
        log_error "Скрипт предназначен для Ubuntu/Debian систем"
        exit 1
    fi
    
    log_success "Система совместима"
}

# Обновление системы
update_system() {
    log_info "Обновление системы..."
    apt update && apt upgrade -y
    log_success "Система обновлена"
}

# Установка Docker
install_docker() {
    if command -v docker &> /dev/null; then
        log_success "Docker уже установлен"
        return
    fi
    
    log_info "Установка Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    
    # Установка Docker Compose
    log_info "Установка Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    log_success "Docker установлен"
}

# Установка nginx
install_nginx() {
    if command -v nginx &> /dev/null; then
        log_success "nginx уже установлен"
        return
    fi
    
    log_info "Установка nginx..."
    apt install nginx -y
    systemctl enable nginx
    systemctl start nginx
    log_success "nginx установлен и запущен"
}

# Создание структуры проекта
create_project_structure() {
    log_info "Создание структуры проекта..."
    
    PROJECT_DIR="/opt/voiceai-dashboard"
    
    # Создание директорий
    mkdir -p $PROJECT_DIR/{app,postgres-data,nginx,logs,backups}
    
    # Создание пользователя для приложения (если не существует)
    if ! id "voiceai" &>/dev/null; then
        useradd -r -s /bin/false voiceai
    fi
    
    # Установка прав доступа
    chown -R voiceai:voiceai $PROJECT_DIR
    chmod 755 $PROJECT_DIR
    
    log_success "Структура проекта создана в $PROJECT_DIR"
}

# Конфигурация nginx
configure_nginx() {
    log_info "Настройка nginx для dashboard.aloda.agency..."
    
    # Создание конфигурации
    cat > /etc/nginx/sites-available/dashboard.aloda.agency << 'EOF'
server {
    listen 80;
    server_name dashboard.aloda.agency;

    # Логи
    access_log /var/log/nginx/dashboard.aloda.agency.access.log;
    error_log /var/log/nginx/dashboard.aloda.agency.error.log;

    # Основное проксирование
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket поддержка
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Таймауты
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Статические файлы
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
    ln -sf /etc/nginx/sites-available/dashboard.aloda.agency /etc/nginx/sites-enabled/
    
    # Проверка конфигурации
    if nginx -t; then
        systemctl reload nginx
        log_success "nginx настроен для dashboard.aloda.agency"
    else
        log_error "Ошибка в конфигурации nginx"
        exit 1
    fi
}

# Установка SSL сертификата
install_ssl() {
    log_info "Установка Certbot для SSL..."
    apt install certbot python3-certbot-nginx -y
    
    log_warning "Для получения SSL сертификата выполните:"
    log_warning "certbot --nginx -d dashboard.aloda.agency"
    log_warning "И настройте автообновление: crontab -e"
    log_warning "Добавьте: 0 12 * * * /usr/bin/certbot renew --quiet"
}

# Создание скриптов управления
create_management_scripts() {
    log_info "Создание скриптов управления..."
    
    # Скрипт обновления
    cat > /opt/voiceai-dashboard/update.sh << 'EOF'
#!/bin/bash
set -e

echo "🔄 Обновление VoiceAI Dashboard..."

cd /opt/voiceai-dashboard

# Остановка контейнеров
docker-compose down

# Обновление кода (если используется Git)
if [ -d "app/.git" ]; then
    cd app
    git pull origin main
    cd ..
fi

# Пересборка и запуск
docker-compose build
docker-compose up -d

echo "✅ Обновление завершено!"
EOF

    # Скрипт бэкапа
    cat > /opt/voiceai-dashboard/backup.sh << 'EOF'
#!/bin/bash
set -e

BACKUP_DIR="/opt/voiceai-dashboard/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

echo "📦 Создание бэкапа базы данных..."

# Бэкап PostgreSQL
docker-compose exec -T postgres pg_dump -U postgres voiceai_db > $BACKUP_DIR/voiceai_db_$DATE.sql

# Сжатие
gzip $BACKUP_DIR/voiceai_db_$DATE.sql

# Удаление старых бэкапов (>30 дней)
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "✅ Бэкап создан: voiceai_db_$DATE.sql.gz"
EOF

    # Скрипт мониторинга
    cat > /opt/voiceai-dashboard/status.sh << 'EOF'
#!/bin/bash

echo "📊 Статус VoiceAI Dashboard"
echo "=========================="

# Статус контейнеров
echo "🐳 Docker контейнеры:"
docker-compose ps

echo ""
echo "📈 Использование ресурсов:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

echo ""
echo "🌐 Статус nginx:"
systemctl status nginx --no-pager -l

echo ""
echo "🔗 Проверка доступности:"
curl -I http://localhost:8000 2>/dev/null | head -1 || echo "❌ Приложение недоступно"
curl -I http://dashboard.aloda.agency 2>/dev/null | head -1 || echo "❌ Домен недоступен"
EOF

    # Установка прав на выполнение
    chmod +x /opt/voiceai-dashboard/{update.sh,backup.sh,status.sh}
    
    log_success "Скрипты управления созданы"
}

# Создание systemd сервиса
create_systemd_service() {
    log_info "Создание systemd сервиса..."
    
    cat > /etc/systemd/system/voiceai-dashboard.service << 'EOF'
[Unit]
Description=VoiceAI Dashboard
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/voiceai-dashboard
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable voiceai-dashboard.service
    
    log_success "Systemd сервис создан и включен"
}

# Настройка файрвола
configure_firewall() {
    log_info "Настройка файрвола..."
    
    if command -v ufw &> /dev/null; then
        # Разрешение SSH, HTTP, HTTPS
        ufw --force enable
        ufw allow ssh
        ufw allow 80/tcp
        ufw allow 443/tcp
        
        log_success "Файрвол настроен"
    else
        log_warning "ufw не найден, настройте файрвол вручную"
    fi
}

# Основная функция развертывания
main() {
    echo "🚀 Запуск автоматического развертывания VoiceAI Dashboard"
    echo "========================================================"
    
    check_permissions
    check_system
    update_system
    install_docker
    install_nginx
    create_project_structure
    configure_nginx
    install_ssl
    create_management_scripts
    create_systemd_service
    configure_firewall
    
    echo ""
    log_success "🎉 Базовое развертывание завершено!"
    echo ""
    echo "📋 Следующие шаги:"
    echo "1. Скопируйте код приложения в /opt/voiceai-dashboard/app/"
    echo "2. Создайте файл .env в /opt/voiceai-dashboard/"
    echo "3. Загрузите Google Service Account файл"
    echo "4. Запустите: cd /opt/voiceai-dashboard && docker-compose up -d"
    echo "5. Получите SSL сертификат: certbot --nginx -d dashboard.aloda.agency"
    echo ""
    echo "🔧 Полезные команды:"
    echo "  Статус:     /opt/voiceai-dashboard/status.sh"
    echo "  Обновление: /opt/voiceai-dashboard/update.sh"
    echo "  Бэкап:      /opt/voiceai-dashboard/backup.sh"
    echo ""
    echo "📝 Подробная инструкция в DEPLOYMENT_GUIDE.md"
}

# Запуск главной функции
main "$@"