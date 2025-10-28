# VoiceAI Call Analysis Dashboard

Современный React frontend для системы анализа звонков VoiceAI с интерактивным dashboard для отображения производительности менеджеров и метрик звонков.

## Особенности

- **Современный UI/UX**: Чистый дизайн с Tailwind CSS и интерактивными компонентами
- **Производительность менеджеров**: Таблица с 30+ менеджерами, сортировкой и фильтрацией
- **Метрики в реальном времени**: 8 карточек с KPI показателями и прогресс-барами  
- **Интерактивные графики**: Визуализация топ-производительности менеджеров
- **Адаптивный дизайн**: Оптимизация для desktop и tablet устройств
- **TypeScript**: Полная типизация для надежности кода
- **Доступность**: ARIA-атрибуты и keyboard navigation

## Технологический стек

- **Frontend Framework**: React 18 с TypeScript
- **Сборщик**: Vite (быстрая разработка)
- **Стилизация**: Tailwind CSS для utility-first подхода
- **Иконки**: Lucide React (современные SVG иконки)
- **Утилиты**: clsx для условной стилизации

## Структура проекта

```
frontend/
├── public/
├── src/
│   ├── components/
│   │   ├── layout/          # Основные layout компоненты
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── MainContent.tsx
│   │   ├── ui/              # Переиспользуемые UI компоненты
│   │   │   ├── MetricCard.tsx
│   │   │   ├── ManagerTable.tsx
│   │   │   ├── PerformanceChart.tsx
│   │   │   └── ProgressBar.tsx
│   │   └── index.ts         # Экспорты компонентов
│   ├── services/
│   │   └── api.ts           # API сервис с mock данными
│   ├── types/
│   │   └── index.ts         # TypeScript типы и интерфейсы
│   ├── utils/
│   │   └── index.ts         # Утилиты и хелперы
│   ├── App.tsx              # Основной App компонент
│   ├── main.tsx             # Entry point
│   └── index.css            # Глобальные стили
├── package.json
├── tailwind.config.js       # Tailwind конфигурация
├── tsconfig.json            # TypeScript конфигурация
└── vite.config.ts           # Vite конфигурация
```

## Компоненты Dashboard

### Layout Components

1. **Dashboard**: Основной контейнер с управлением состоянием
2. **Header**: Навигация с метриками статуса и профилем пользователя
3. **Sidebar**: Таблица менеджеров с поиском и сортировкой
4. **MainContent**: Область с карточками метрик и графиками

### UI Components

1. **MetricCard**: Карточка с процентными показателями и прогрессом
2. **ManagerTable**: Полная таблица менеджеров с сортировкой
3. **PerformanceChart**: Горизонтальные прогресс-бары для топ менеджеров
4. **ProgressBar**: Переиспользуемый прогресс-бар с цветовой индикацией

## API Интеграция

Реализован service layer с mock данными:

- `getManagersStats()` - получение списка менеджеров
- `getPerformanceMetrics()` - KPI метрики для карточек
- `getCallMetrics()` - общая статистика звонков
- `getProcessingStatus()` - статус обработки звонков
- `healthCheck()` - проверка состояния системы

## Дизайн система

```json
{
  "colors": {
    "primary": "#2563eb",    // Основной синий
    "success": "#10b981",    // Зеленый для успеха
    "warning": "#f59e0b",    // Желтый для предупреждений
    "danger": "#ef4444",     // Красный для ошибок
    "bg-primary": "#ffffff", // Белый фон
    "bg-secondary": "#f8fafc" // Серый фон
  },
  "typography": "Inter font family",
  "spacing": "8px grid system",
  "shadows": "Subtle elevation shadows",
  "radius": "8-12px border radius"
}
```

## Установка и запуск

1. **Установка зависимостей**:
```bash
cd frontend
npm install
```

2. **Запуск в development режиме**:
```bash
npm run dev
```

3. **Сборка для production**:
```bash
npm run build
```

4. **Проверка сборки**:
```bash
npm run preview
```

## Скрипты

- `npm run dev` - запуск development сервера
- `npm run build` - production сборка
- `npm run lint` - проверка ESLint
- `npm run preview` - предпросмотр production сборки

## Особенности реализации

### Адаптивность
- Desktop-first подход с адаптацией под планшеты
- Collapsed sidebar на мобильных устройствах
- Responsive grid для метрик карточек

### Производительность
- Lazy loading компонентов
- React.memo для оптимизации рендера
- Виртуализация для больших списков

### Доступность
- ARIA labels для screen readers
- Keyboard navigation поддержка
- Цветовые индикаторы с текстовыми альтернативами
- Focus management

### TypeScript
- Строгая типизация всех props и данных
- Интерфейсы для API responses
- Type guards для runtime проверок

## Интеграция с Backend

API endpoints готовы к подключению к Python backend:

```typescript
// Базовый URL настраивается в api.ts
const baseUrl = 'http://localhost:8000/api';

// Endpoints:
// GET /api/managers/stats
// GET /api/performance-metrics  
// GET /api/call-metrics
// GET /api/processing-status
// GET /api/health-check
```

## Следующие шаги

1. **Backend интеграция**: Подключение к реальному Python API
2. **WebSocket**: Реальное время обновлений
3. **Фильтрация**: Расширенные фильтры по датам, команде
4. **Экспорт**: Экспорт отчетов в PDF/Excel
5. **Темная тема**: Dark mode поддержка
6. **Уведомления**: Toast notifications система

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

---

Разработано с использованием современных web технологий для максимальной производительности и удобства использования.