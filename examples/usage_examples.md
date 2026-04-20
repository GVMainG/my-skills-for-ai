# Примеры использования notes-manager

## Сценарий 1: Первый запуск

```bash
pip install -e /path/to/notes-manager
notes-manager init
# → Укажите путь к Obsidian vault: /home/user/obsidian
# ✅ Vault сохранён
```

---

## Сценарий 2: Ежедневное использование

```bash
# Утром — дневниковая запись
notes-manager daily-journal

# Анализ тегов только что написанной заметки
notes-manager analyze-tags ~/obsidian/00-inbox/new-idea.md --dry-run

# Если рекомендации понравились
notes-manager analyze-tags ~/obsidian/00-inbox/new-idea.md --auto-apply

# Поиск по теме
notes-manager search "async await многопоточность C#"
```

---

## Сценарий 3: Еженедельный audit

```bash
# Полный audit vault
notes-manager audit ~/obsidian/ --all

# Только битые ссылки и невалидные теги
notes-manager audit ~/obsidian/ --check-links --check-tags

# С автоисправлением
notes-manager audit ~/obsidian/ --all --auto-fix
```

---

## Сценарий 4: Генерация профиля

```bash
# Первичная генерация
notes-manager generate-profile

# Обновление через месяц
notes-manager generate-profile --update

# Только технические навыки
notes-manager generate-profile --sections technical_skills --output ~/skills.md
```

---

## Тестовый vault

В папке `test_vault/` находятся примеры заметок для тестирования команд.

```bash
notes-manager audit examples/test_vault/ --all
notes-manager search "python" --scope examples/test_vault/
```
