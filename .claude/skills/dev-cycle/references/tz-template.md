# Техническое Задание: {{app-name}}

**Версия:** 1.0  
**Дата:** {{date}}  
**Статус:** На согласовании

---

## 1. Обзор и цели

{{What problem this solves, what the app does, business goal}}

## 2. Роли пользователей

| Роль | Описание | Права доступа |
|------|----------|---------------|
| {{role}} | {{description}} | {{permissions}} |

*(если аутентификация не нужна — написать "Нет ролей, публичное приложение")*

## 3. Функциональные требования

### 3.1 {{Module/Feature Name}}

- **FR-01:** {{requirement}}
- **FR-02:** {{requirement}}

### 3.2 {{Module/Feature Name}}

- **FR-10:** {{requirement}}

*(продолжить для каждого модуля)*

## 4. Технический стек

| Компонент | Технология | Обоснование |
|-----------|------------|-------------|
| Backend | {{C# .NET / Python}} | {{why}} |
| Frontend | React | {{why}} |
| База данных | {{PostgreSQL / MS SQL / SQLite}} | {{why}} |
| Инфраструктура | Docker, docker-compose | Воспроизводимое окружение |

## 5. Архитектура

{{High-level description of how components interact. Include a text diagram if helpful:}}

```
[React Frontend] ──HTTP──> [API Backend] ──SQL──> [Database]
                                │
                           [Docker Network]
```

{{Describe key architectural decisions: monolith vs microservices, sync vs async, etc.}}

## 6. Модель данных

### Сущности

**{{EntityName}}**
| Поле | Тип | Описание |
|------|-----|----------|
| id | int/uuid | Первичный ключ |
| {{field}} | {{type}} | {{description}} |

*(продолжить для каждой сущности)*

### Связи

{{Describe relationships: one-to-many, many-to-many, etc.}}

## 7. API (если применимо)

### Основные эндпоинты

| Метод | URL | Описание | Auth |
|-------|-----|----------|------|
| GET | /api/{{resource}} | {{description}} | {{yes/no}} |
| POST | /api/{{resource}} | {{description}} | {{yes/no}} |

## 7.1 Ошибки и валидация (если применимо)

{{validation rules, error formats, important error cases}}

## 7.2 Миграции/изменения схемы (если применимо)

{{migration approach, versioning, rollback considerations}}

## 8. Вне скоупа v1

Следующие функции **не входят** в первую версию:

- {{feature}}
- {{feature}}

## 9. Глоссарий

| Термин | Определение |
|--------|-------------|
| {{term}} | {{definition}} |
