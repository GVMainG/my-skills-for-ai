from __future__ import annotations

import sys

import click

from .core.config import ConfigurationError, load_config, save_config
from .core.vault import VaultNotFoundError
from .utils.validators import validate_vault_path


def _get_config():
    try:
        return load_config()
    except ConfigurationError as e:
        click.echo(f"❌ Ошибка конфигурации: {e}", err=True)
        sys.exit(1)


def _ensure_vault(config):
    """Prompt for vault path if not set."""
    if config.vault_path is None or not config.vault_path.exists():
        click.echo("⚠️ Путь к vault не задан или не существует.")
        path = click.prompt("Укажите путь к Obsidian vault")
        ok, msg = validate_vault_path(path)
        if not ok:
            click.echo(f"❌ {msg}")
            sys.exit(1)
        config.set_vault_path(path)
        save_config(config)
        click.echo(f"✅ Vault сохранён: {path}")
    return config


@click.group()
def cli():
    """notes-manager — управление Obsidian vault через CLI."""
    pass


@cli.command("init")
def cmd_init():
    """Инициализация конфигурации (первый запуск)."""
    config = _get_config()
    _ensure_vault(config)
    click.echo("✅ Инициализация завершена.")


@cli.command("analyze-tags")
@click.argument("filepath")
@click.option("--auto-apply", is_flag=True, help="Автоматически применить рекомендации")
@click.option("--dry-run", is_flag=True, help="Показать изменения без применения")
def cmd_analyze_tags(filepath: str, auto_apply: bool, dry_run: bool):
    """Анализировать и рекомендовать теги для заметки."""
    config = _ensure_vault(_get_config())
    from .commands.analyze_tags import analyze_tags
    analyze_tags(filepath, config, auto_apply=auto_apply, dry_run=dry_run)


@cli.command("audit")
@click.argument("folder_path")
@click.option("--check-format", "chk_format", is_flag=True, default=False)
@click.option("--check-placement", "chk_placement", is_flag=True, default=False)
@click.option("--find-duplicates", "chk_dupes", is_flag=True, default=False)
@click.option("--check-links", "chk_links", is_flag=True, default=False)
@click.option("--check-tags", "chk_tags", is_flag=True, default=False)
@click.option("--auto-fix", is_flag=True, help="Автоисправление тривиальных проблем")
@click.option("--all", "run_all", is_flag=True, default=True, help="Все проверки (по умолчанию)")
def cmd_audit(
    folder_path: str,
    chk_format: bool,
    chk_placement: bool,
    chk_dupes: bool,
    chk_links: bool,
    chk_tags: bool,
    auto_fix: bool,
    run_all: bool,
):
    """Audit заметок в папке на предмет проблем."""
    config = _ensure_vault(_get_config())
    # If any specific flag set, disable run_all for that category
    specific = any([chk_format, chk_placement, chk_dupes, chk_links, chk_tags])
    if not specific:
        chk_format = chk_placement = chk_dupes = chk_links = chk_tags = True

    from .commands.audit import run_audit
    run_audit(
        folder_path,
        config,
        check_format_flag=chk_format,
        check_placement_flag=chk_placement,
        find_duplicates_flag=chk_dupes,
        check_links_flag=chk_links,
        check_tags_flag=chk_tags,
        auto_fix=auto_fix,
    )


@cli.command("search")
@click.argument("query")
@click.option("--max-results", type=int, default=None)
@click.option("--include-backlinks", is_flag=True, default=True)
@click.option("--scope", default=None, help="Ограничить поиск папкой")
@click.option("--tags", "tag_filter", default=None, help="Фильтр по тегам (через запятую)")
def cmd_search(
    query: str,
    max_results: int | None,
    include_backlinks: bool,
    scope: str | None,
    tag_filter: str | None,
):
    """Интеллектуальный поиск по заметкам."""
    config = _ensure_vault(_get_config())
    tags = [t.strip() for t in tag_filter.split(",")] if tag_filter else None
    from .commands.search import run_search
    run_search(
        query,
        config,
        max_results=max_results,
        include_backlinks=include_backlinks,
        scope=scope,
        tag_filter=tags,
    )


@cli.command("daily-journal")
@click.option("--questions", type=int, default=5)
@click.option("--find-connections", "find_conn", is_flag=True, default=True)
@click.option("--no-create", is_flag=True, default=False)
def cmd_daily_journal(questions: int, find_conn: bool, no_create: bool):
    """Помощник для ведения дневниковой записи."""
    config = _ensure_vault(_get_config())
    from .commands.daily_journal import run_daily_journal
    run_daily_journal(
        config,
        questions_count=questions,
        find_connections=find_conn,
        no_create=no_create,
    )


@cli.command("generate-profile")
@click.option("--update", is_flag=True, default=False)
@click.option("--output", "output_path", default=None)
@click.option("--sections", default=None, help="Секции через запятую")
def cmd_generate_profile(update: bool, output_path: str | None, sections: str | None):
    """Генерация психологического профиля пользователя."""
    config = _ensure_vault(_get_config())
    section_list = [s.strip() for s in sections.split(",")] if sections else None
    from .commands.generate_profile import generate_profile
    generate_profile(config, update=update, output_path=output_path, sections=section_list)


if __name__ == "__main__":
    cli()
