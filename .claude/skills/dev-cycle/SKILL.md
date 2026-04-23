---
name: dev-cycle
description: >
  Full software development lifecycle skill — from idea to working application.
  Invoke this skill whenever the user wants to create a new application, start a new project,
  or develop software from scratch. Triggers on phrases like: "создать приложение", "разработать приложение",
  "новый проект", "хочу сделать сайт/сервис/систему", "есть идея для приложения", "build app",
  "create application", "new project", "start development", "develop from scratch", "I have an idea for an app".
  This skill guides Claude through a structured pipeline:
  idea & feasibility discussion → requirements gathering → ТЗ approval → task block planning → iterative development with per-block review → testing.
  Always use this skill when there's a multi-phase development workflow ahead, even if the user doesn't explicitly
  say "full cycle" or "dev cycle".
---

# Full Development Lifecycle

This skill manages the complete development process of an application, with explicit user approval gates between each phase. **Never skip a gate or proceed to the next phase without explicit approval.**

## Supported Stack

- **Backend:** C# (.NET) or Python
- **Frontend:** React
- **Database:** SQL (PostgreSQL, MS SQL, SQLite — clarify during requirements)
- **Infrastructure:** Docker, docker-compose
- **Testing:** Unit tests (xUnit/NUnit for C# projects), manual for others

---

## Project File Structure

Create this structure in the current working directory:

```
<app-name>/
├── docs/
│   ├── requirements.md       # Gathered requirements
│   ├── technical-spec.md     # Agreed ТЗ
│   └── tasks.md              # Task blocks (filled after ТЗ approval)
└── src/                      # Source code (filled during development)
```

Create the `docs/` folder and empty placeholder files at the start of Phase 1.

---

## Phase 0: Idea & Feasibility

**Goal:** Understand the idea at a high level and honestly assess whether it's worth pursuing — before investing time in detailed requirements. This phase is a conversation, not a form.

### Step 0.1 — Listen to the idea

Ask the user to describe what they want to build in their own words, without constraints:

> "Расскажите в общих чертах — что вы хотите создать? Не нужно быть точным, просто опишите идею как вы её видите."

Let the user speak freely. Don't interrupt with clarifying questions yet — just understand the overall picture.

### Step 0.2 — Discuss feasibility

After the user describes the idea, reflect it back briefly and raise any relevant concerns. Be honest but constructive — your goal is to help the user make an informed decision, not to discourage them.

Consider and raise (where relevant):

**Complexity & time:**
- Is the scope realistic for one developer + AI assistant? Or is it a multi-team, multi-year effort?
- Are there parts that are significantly more complex than they might appear (e.g., real-time sync, ML/AI features, complex financial logic, regulatory compliance)?
- Rough time estimate: days / weeks / months?

**Technical challenges:**
- Does the idea require technologies outside the supported stack (Docker, C#, Python, SQL, React)? If so, flag it — it doesn't block anything, but the user should know.
- Are there hard technical problems involved (e.g., high-load architecture, low-latency requirements, complex algorithms)?

**External dependencies:**
- Does the idea rely on paid third-party APIs or services?
- Are there licensing, legal, or compliance constraints (GDPR, payment processing, medical data)?
- Does it require specific domain expertise (medical, financial, legal)?

**Cost:**
- Infrastructure (hosting, cloud, DB): estimate low/medium/high
- Third-party services or APIs: any notable costs?

Be specific — instead of "this will be complex", say "real-time collaboration like Google Docs requires complex conflict resolution logic and WebSocket infrastructure, which would add significant time."

### Step 0.3 — Feasibility gate

After the discussion, summarize the assessment:

> "**Резюме по идее:**
> - Что планируется: [brief description]
> - Сложность: [low/medium/high] — [why]
> - Примерные сроки: [estimate]
> - Возможные сложности: [list]
> - Внешние зависимости/затраты: [list or "нет"]
>
> В целом идея [реализуема / реализуема с оговорками / труднореализуема] потому что [reason].
>
> Продолжаем и переходим к детальному сбору требований?"

**Wait for the user's decision:**
- **"Да"** → proceed to Phase 1
- **"Нет"** or "хочу пересмотреть" → discuss alternatives, scope down, or pivot the idea
- If the user wants to change the idea — go back to Step 0.1

Don't proceed to requirements until the user explicitly agrees to move forward.

---

## Phase 1: Requirements Gathering

**Goal:** Fully understand what the user wants to build before writing anything.

### Step 1.1 — Ask for the app name

Ask the user: what is the name of the application?

### Step 1.2 — Ask for the response mode

Ask the user how they prefer to answer requirements questions:

> "Как вы предпочитаете отвечать на вопросы о требованиях?
> 1. **По одному** — я задаю один вопрос, вы отвечаете, затем следующий
> 2. **Списком** — я даю все вопросы сразу, вы отвечаете в одном сообщении"

### Step 1.3 — Gather requirements

Cover all of the following areas. Use the mode the user selected (one-by-one or as a full list).

**Questions to cover:**

1. Какую проблему решает приложение? Кто им будет пользоваться?
2. Каковы основные функции/модули? Что обязательно должно быть в первой версии?
3. Нужна ли аутентификация/авторизация? Если да — роли пользователей?
4. Какая база данных предпочтительна? (PostgreSQL / MS SQL / SQLite / другое)
5. Нужен ли REST API? GraphQL? Или только frontend без отдельного API?
6. Нужна ли интеграция с внешними сервисами (почта, платежи, уведомления и т.д.)?
7. Есть ли требования к UI/UX? Дизайн-макеты? Или типовой интерфейс?
8. Нужен ли Docker / docker-compose для запуска?
9. Есть ли нефункциональные требования: производительность, безопасность, доступность?
10. Что является критерием "готово" для первой рабочей версии?

Ask follow-up questions if any answer is unclear or ambiguous. Don't move on until you have a solid understanding of what's being built.

### Step 1.4 — Save requirements

Write everything gathered to `docs/requirements.md` using the template in `references/requirements-template.md`.

Tell the user: "Требования собраны и сохранены в `docs/requirements.md`. Перехожу к составлению ТЗ."

---

## Phase 2: Technical Specification (ТЗ)

**Goal:** Turn requirements into a structured, agreed specification.

### Step 2.1 — Write the ТЗ

Based on the requirements, write `docs/technical-spec.md`. Use the template in `references/tz-template.md`.

The ТЗ must include:
- Overview and goals
- User roles (if any)
- Functional requirements — detailed, enumerated
- Technical stack decision (explain choices based on requirements)
- Architecture overview (components, how they interact)
- Data model (main entities and relationships)
- API outline (main endpoints, if applicable)
- Out of scope (what explicitly is NOT in this version)
- Glossary (if needed)

### Step 2.2 — Approval gate

Present the ТЗ to the user:

> "ТЗ готово и сохранено в `docs/technical-spec.md`. Пожалуйста, ознакомьтесь и скажите:
> - **Да** — всё верно, идём дальше
> - **Нет** + что именно нужно изменить"

**Wait for approval. Do not proceed until user says yes.**

If the user requests changes — update the ТЗ and show the diff of what changed. Ask for approval again.

---

## Phase 3: Task Planning

**Goal:** Break the ТЗ into concrete development tasks, grouped into logical blocks.

### Step 3.1 — Create task blocks

Decompose the approved ТЗ into tasks. Group related tasks into blocks (typically 3–7 tasks per block). Blocks should be independently deliverable and testable.

Good block examples:
- Block 1: Project setup (Docker, DB, skeleton app)
- Block 2: Authentication & user management
- Block 3: Core feature A
- Block 4: Core feature B + API integration
- Block 5: Frontend for features A and B
- Block 6: Final polish, error handling, testing

Each task should be specific and small enough to implement and verify in one step.

### Step 3.2 — Save task plan

Write the task plan to `docs/tasks.md` using the template in `references/tasks-template.md`.

### Step 3.3 — Approval gate

Present the task plan:

> "План задач готов и сохранён в `docs/tasks.md`. Пожалуйста, ознакомьтесь:
> - **Да** — план верный, начинаем разработку
> - **Нет** + что изменить"

**Wait for approval. Do not proceed until user says yes.**

If the user requests changes — update `docs/tasks.md` and ask again.

---

## Phase 4: Development Loop

**Goal:** Implement the project block by block, with user review after each block.

For each block in `docs/tasks.md`:

### Step 4.1 — Announce the block

Tell the user which block you're starting:

> "Начинаю разработку **Блок N: [название]**
> Задачи этого блока:
> - [ ] Задача 1
> - [ ] Задача 2
> ..."

### Step 4.2 — Implement tasks

Implement all tasks in the block. For each task:
- Write the code
- Update `docs/tasks.md` marking the task as done: `[x]`
- Briefly note what was done (one line per task)

Follow these conventions:
- **C# projects:** Follow standard .NET conventions, use dependency injection, async/await
- **Python projects:** Use type hints, follow PEP 8
- **React:** Functional components, hooks, keep components small
- **SQL:** Write migrations, not raw DDL — so schema is reproducible
- **Docker:** Always include a `docker-compose.yml` for local dev setup

### Step 4.3 — Review gate

After completing all tasks in the block, present a summary:

> "**Блок N завершён.** Вот что было реализовано:
> - [краткое описание каждой задачи]
>
> Для проверки: [как запустить и что протестировать руками]
>
> Всё верно?
> - **Да** — переходим к следующему блоку
> - **Нет** + что нужно исправить"

**Wait for approval before starting the next block.**

If the user finds issues — fix them, show what changed, ask again.

### Step 4.4 — Testing (C# projects only)

If the project is C#, after the user approves the block:
- Write unit tests for the business logic implemented in this block
- Aim for coverage of happy path + main edge cases
- Use xUnit or NUnit (whichever was established in the project setup)
- Run the tests and confirm they pass before moving on

For non-C# projects, remind the user to test manually using the instructions from Step 4.3.

### Step 4.5 — Repeat

Repeat Steps 4.1–4.4 for each block until all blocks are complete.

---

## Phase 5: Project Completion

When all blocks are done:

1. Update `docs/tasks.md` — all tasks should be marked `[x]`
2. Verify `docker-compose up` works (if Docker was in scope)
3. Write a brief `README.md` in the project root with: what the app does, how to run it, and the tech stack

Present a final summary:

> "🎉 Проект **[название]** завершён!
>
> **Что реализовано:**
> [список всех блоков]
>
> **Как запустить:**
> [инструкция]
>
> **Документация:** `docs/` — требования, ТЗ, задачи"

---

## Approval Gate Rules

These rules apply at every gate in this workflow:

- **"Да"** (or "yes", "ок", "всё верно", "принято", "согласован", thumbs up, "+") → proceed
- **"Нет"** + comment → address all feedback, show changes, ask again
- Ambiguous response → ask for clarification
- **Never assume approval.** If the user says nothing or goes quiet, don't proceed.

---

## Key Principles

- **State lives in files.** Always keep `docs/requirements.md`, `docs/technical-spec.md`, and `docs/tasks.md` up to date. If the conversation is interrupted, you can pick it up from these files.
- **One phase at a time.** Don't mix phases. Requirements phase is only requirements. Don't start writing code ideas during ТЗ phase.
- **Be specific when asking.** Vague requirements lead to rework. Push back gently if an answer is too vague ("Что именно должно происходить когда...?").
- **Show, don't just tell.** When presenting the ТЗ or task plan, show the actual document, not a summary of it.
- **Communicate progress.** During development, briefly note what you're doing for each task so the user can follow along.
