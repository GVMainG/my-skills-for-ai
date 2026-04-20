---
created: 2026-04-15T10:00:00
tags:
  - инфраструктура/homelab
  - it/docker
  - инфраструктура/развертывание
---

# Docker Compose для homelab

Настройка Docker Compose для развертывания сервисов на домашнем сервере.

## Структура проекта

```yaml
version: '3.8'
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
  n8n:
    image: n8nio/n8n
    ports:
      - "5678:5678"
```

## Преимущества Docker в homelab

Docker Compose — идеальное решение для изоляции сервисов. Каждый сервис в отдельном контейнере.

Ссылки:
- [[Linux server setup]]
