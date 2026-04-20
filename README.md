# notes-manager

Python skill для управления Obsidian vault через CLI.

## Возможности

| Команда | Описание |
|---|---|
| `analyze-tags` | Анализ тегов заметки, рекомендации на основе содержимого |
| `audit` | Проверка vault: формат, размещение, дубли, битые ссылки, теги |
| `search` | Интеллектуальный поиск (теги + ключевые слова + бэклинки) |
| `daily-journal` | Помощник дневниковой записи с адаптивными вопросами |
| `generate-profile` | Генерация психологического профиля пользователя (CLAUDE.md) |

## Установка

```bash
# 1. Перейти в директорию
cd notes-manager/

# 2. Установить пакет
pip install -e .

# 3. (Опционально) установить NLP-зависимости для расширенного анализа
pip install -e ".[nlp]"

# 4. Инициализация
notes-manager init
```

## Быстрый старт

```bash
# Настройка vault
notes-manager init

# Анализ тегов заметки
notes-manager analyze-tags /path/to/vault/my-note.md

# Audit всего vault
notes-manager audit /path/to/vault --all

# Поиск
notes-manager search "docker homelab настройка"

# Дневниковая запись
notes-manager daily-journal

# Генерация профиля
notes-manager generate-profile
```

## Конфигурация

Файл: `~/.notes-manager/config.yaml`

```yaml
vault:
  path: "/path/to/your/obsidian/vault"
  tags_file: "99_Служебная/Indexes/TAGS_HIERARCHICAL.md"

limits:
  max_notes_in_context: 25
  search_max_results: 10

audit:
  min_note_length: 100
```

## Примеры использования

### analyze-tags

```bash
# Просмотр рекомендаций без применения
notes-manager analyze-tags note.md --dry-run

# Автоматическое применение
notes-manager analyze-tags note.md --auto-apply
```

**Вывод:**
```
📝 Анализ тегов: note.md

Текущие теги (2):
  #it/csharp
  #личное/дневник

Рекомендации:

❌ Удалить:
  #личное/дневник
  Причина: Содержимое не подтверждает тег

✅ Добавить:
  #it/многопоточность
  Причина: Ключевые слова — "async", "await", "task", "threading"

Итого тегов после применения: 2 (в пределах нормы 1–5)

Применить изменения? [Y/n]
```

---

### audit

```bash
notes-manager audit /vault/20-areas/ --all
notes-manager audit /vault/ --check-links --check-tags
notes-manager audit /vault/ --find-duplicates --auto-fix
```

**Вывод:**
```
🔍 Audit: /vault/20-areas/ (147 файлов проанализировано)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 FORMAT ISSUES (3)

❌ HIGH: Missing frontmatter
  - async-notes.md
  ✅ Авто-исправление доступно

🔗 BROKEN LINKS (2)

❌ HIGH: async-notes.md
  Строка 15: [[SOLID Principles]]
  💡 Создать заметку или удалить ссылку

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ИТОГО:
  Всего проблем: 5
  Автоисправляемых: 3
  Требуют ручной проверки: 2
```

---

### search

```bash
notes-manager search "async await C#"
notes-manager search "docker homelab" --scope 20-areas/
notes-manager search "дневник" --tags "#личное/дневник"
```

**Вывод:**
```
🔍 Search: "async await C#"

Найдено 5 результатов (просмотрено 147 заметок):

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. C# Advanced Async (релевантность: 1.00) ⭐⭐⭐
   Путь: 20-areas/development/csharp-async.md
   Теги: #it/csharp, #it/многопоточность
   Изменено: 2026-04-15
   Обзор: Разобрался с ConfigureAwait(false) — нужен для library кода...
   Бэклинки: 5 заметок
```

---

### daily-journal

```bash
notes-manager daily-journal --questions 5
notes-manager daily-journal --no-create  # Только вопросы
```

---

### generate-profile

```bash
# Первичная генерация
notes-manager generate-profile

# Обновление существующего
notes-manager generate-profile --update

# Только технические навыки
notes-manager generate-profile --sections technical_skills,knowledge_map
```

---

## Структура vault (ожидаемая)

```
vault/
├── 00-inbox/          # Входящие
├── 10-daily/          # Дневниковые записи
├── 20-areas/          # Области знаний
├── 30-projects/       # Проекты
├── 40-archive/        # Архив
└── 99_Служебная/
    └── Indexes/
        └── TAGS_HIERARCHICAL.md  # Иерархия тегов
```

## Требования

- Python 3.10+
- pyyaml
- click
- rich

Опциональные (для расширенного NLP):
- scikit-learn
- nltk
- networkx
