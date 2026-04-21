from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from ..core.config import Config
from ..core.note import AuditIssue, Note
from ..core.vault import VaultManager, VaultNotFoundError
from ..utils.md_parser import build_frontmatter_block, parse_frontmatter
from ..utils.similarity import calculate_jaccard_similarity
from ..utils.validators import validate_note_structure

_SEP = "━" * 51


@dataclass
class AuditReport:
    folder: str
    total_files: int
    format_issues: list[AuditIssue] = field(default_factory=list)
    placement_issues: list[AuditIssue] = field(default_factory=list)
    duplicates: list[AuditIssue] = field(default_factory=list)
    broken_links: list[AuditIssue] = field(default_factory=list)
    invalid_tags: list[AuditIssue] = field(default_factory=list)

    @property
    def all_issues(self) -> list[AuditIssue]:
        return (
            self.format_issues
            + self.placement_issues
            + self.duplicates
            + self.broken_links
            + self.invalid_tags
        )

    @property
    def auto_fixable(self) -> list[AuditIssue]:
        return [i for i in self.all_issues if i.auto_fix]


def check_format(note: Note, config: Config) -> list[AuditIssue]:
    issues = []
    if not note.has_frontmatter():
        issues.append(AuditIssue(
            issue_type="missing_frontmatter",
            severity="high",
            file_path=note.filename,
            description="Отсутствует frontmatter",
            auto_fix=True,
            fix_action="add_default_frontmatter",
        ))
    if len(note.content.strip()) < config.audit.min_note_length:
        issues.append(AuditIssue(
            issue_type="too_short",
            severity="medium",
            file_path=note.filename,
            description=f"Слишком короткая заметка ({len(note.content.strip())} символов)",
            suggestion=f"Расширить контент или переместить в {config.folders.inbox}/",
        ))
    stem = note.path.stem
    if stem in config.audit.default_untitled_names:
        issues.append(AuditIssue(
            issue_type="untitled",
            severity="medium",
            file_path=note.filename,
            description="Название по умолчанию",
            auto_fix=True,
            fix_action="generate_title_from_content",
        ))
    return issues


def check_placement(note: Note, vault: VaultManager) -> list[AuditIssue]:
    issues = []
    cfg = vault.config

    # Infer category from tags
    tag_categories: list[str] = []
    for tag in note.tags:
        top = tag.lstrip("#").split("/")[0]
        tag_categories.append(top)

    # Infer category from folder
    try:
        rel = note.path.relative_to(vault.root)
        folder_top = rel.parts[0] if rel.parts else ""
    except ValueError:
        folder_top = ""

    # Map known folder prefixes
    _folder_map = {
        cfg.folders.inbox: "входящие",
        cfg.folders.daily: "личное",
        cfg.folders.areas: "areas",
        cfg.folders.projects: "проекты",
        cfg.folders.archive: "архив",
    }
    folder_category = _folder_map.get(folder_top, folder_top)

    if tag_categories and folder_category and folder_category not in tag_categories:
        suggested = _guess_folder(tag_categories[0], cfg)
        if suggested and suggested != folder_top:
            issues.append(AuditIssue(
                issue_type="folder_mismatch",
                severity="high",
                file_path=str(note.path.relative_to(vault.root)),
                description=(
                    f"Папка '{folder_top}' не соответствует тегам {tag_categories[:2]}"
                ),
                suggestion=f"Переместить в {suggested}/",
                extra={"current": folder_top, "suggested": suggested},
            ))
    return issues


def _guess_folder(tag_top: str, cfg) -> str:
    mapping = {
        "личное": cfg.folders.daily,
        "входящие": cfg.folders.inbox,
        "архив": cfg.folders.archive,
        "карьера": cfg.folders.areas,
        "it": cfg.folders.areas,
        "инфраструктура": cfg.folders.areas,
        "творчество": cfg.folders.areas,
    }
    return mapping.get(tag_top.lower(), "")


def find_duplicates(notes: list[Note], threshold: float = 0.8) -> list[AuditIssue]:
    issues = []
    for i, n1 in enumerate(notes):
        for n2 in notes[i + 1:]:
            if len(n1.content) < 50 or len(n2.content) < 50:
                continue
            sim = calculate_jaccard_similarity(n1.content[:2000], n2.content[:2000])
            if sim > threshold:
                issues.append(AuditIssue(
                    issue_type="duplicate",
                    severity="medium",
                    file_path=n1.filename,
                    description=(
                        f"{n1.filename} ↔ {n2.filename} ({sim:.0%} похожи)"
                    ),
                    suggestion="Объединить заметки и удалить дубликат",
                    extra={"other": n2.filename, "similarity": sim},
                ))
    return issues


def check_links(note: Note, vault: VaultManager) -> list[AuditIssue]:
    issues = []
    for link in note.links:
        target = vault.resolve_link(link)
        if target is None:
            from ..utils.md_parser import find_line_number
            line = find_line_number(note.content, link)
            issues.append(AuditIssue(
                issue_type="broken_link",
                severity="high",
                file_path=note.filename,
                description=f"Битая ссылка: [[{link}]]",
                suggestion="Создать заметку или удалить ссылку",
                extra={"link": link, "line": line},
            ))
    return issues


def check_tags(note: Note, vault: VaultManager) -> list[AuditIssue]:
    issues = []
    valid = vault.tags_manager.all_tags
    if not valid:
        return issues
    for tag in note.tags:
        if tag not in valid:
            closest = vault.tags_manager.find_closest_tag(tag)
            issues.append(AuditIssue(
                issue_type="invalid_tag",
                severity="medium",
                file_path=note.filename,
                description=f"Тег не в иерархии: {tag}",
                suggestion=f"Похожий тег: {closest}" if closest else "Добавить в TAGS_HIERARCHICAL.md",
                extra={"tag": tag, "closest": closest},
            ))
    return issues


def _auto_fix_missing_frontmatter(note: Note) -> None:
    fm = {
        "created": note.created.isoformat() if note.created else datetime.now().isoformat(),
        "tags": [],
    }
    block = build_frontmatter_block(fm)
    new_content = block + "\n" + note.content
    note.path.write_text(new_content, encoding="utf-8")


def _auto_fix_title(note: Note) -> None:
    from ..analyzers.keyword_extractor import extract_keywords
    kws = extract_keywords(note.content, 3)
    new_name = "_".join(kws[:3]) if kws else "заметка"
    new_path = note.path.parent / f"{new_name}.md"
    note.path.rename(new_path)


def run_audit(
    folder_path: str,
    config: Config,
    check_format_flag: bool = True,
    check_placement_flag: bool = True,
    find_duplicates_flag: bool = True,
    check_links_flag: bool = True,
    check_tags_flag: bool = True,
    auto_fix: bool = False,
) -> AuditReport:
    path = Path(folder_path)
    if not path.exists():
        print(f"❌ Папка не найдена: {folder_path}")
        sys.exit(1)

    try:
        vault = VaultManager(config)
    except VaultNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)

    notes = [n for n in vault.get_all_notes() if str(n.path).startswith(str(path))]
    report = AuditReport(folder=folder_path, total_files=len(notes))

    print(f"\n🔍 Audit: {folder_path} ({len(notes)} файлов проанализировано)")
    print(_SEP)

    if check_format_flag:
        for note in notes:
            report.format_issues.extend(check_format(note, config))

    if check_placement_flag:
        for note in notes:
            report.placement_issues.extend(check_placement(note, vault))

    if find_duplicates_flag:
        report.duplicates.extend(find_duplicates(notes))

    if check_links_flag:
        for note in notes:
            report.broken_links.extend(check_links(note, vault))

    if check_tags_flag:
        for note in notes:
            report.invalid_tags.extend(check_tags(note, vault))

    _print_report(report)

    if auto_fix and report.auto_fixable:
        print(f"\n🔧 Автоисправление {len(report.auto_fixable)} проблем...")
        _apply_auto_fixes(report.auto_fixable, notes)
    elif report.auto_fixable:
        answer = input(f"\nПрименить автоисправления ({len(report.auto_fixable)})? [Y/n] ").strip().lower()
        if answer in ("y", ""):
            _apply_auto_fixes(report.auto_fixable, notes)

    return report


def _print_report(report: AuditReport) -> None:
    if report.format_issues:
        print(f"\n📋 FORMAT ISSUES ({len(report.format_issues)})\n")
        _group_print(report.format_issues)

    if report.placement_issues:
        print(f"\n{_SEP}\n📂 PLACEMENT ISSUES ({len(report.placement_issues)})\n")
        for issue in report.placement_issues:
            icon = "❌" if issue.severity == "high" else "⚠️"
            print(f"{icon} {issue.severity.upper()}: {issue.description}")
            if issue.suggestion:
                print(f"  💡 {issue.suggestion}")

    if report.duplicates:
        print(f"\n{_SEP}\n🔗 DUPLICATE NOTES ({len(report.duplicates)})\n")
        for issue in report.duplicates:
            print(f"⚠️ MEDIUM: {issue.description}")
            print(f"  💡 {issue.suggestion}")

    if report.broken_links:
        print(f"\n{_SEP}\n🔗 BROKEN LINKS ({len(report.broken_links)})\n")
        for issue in report.broken_links:
            extra = issue.extra
            print(f"❌ HIGH: {issue.file_path}")
            print(f"  Строка {extra.get('line', '?')}: [[{extra.get('link', '?')}]]")
            print(f"  💡 {issue.suggestion}")

    if report.invalid_tags:
        print(f"\n{_SEP}\n🏷️ INVALID TAGS ({len(report.invalid_tags)})\n")
        for issue in report.invalid_tags:
            print(f"⚠️ MEDIUM: {issue.file_path}")
            print(f"  Тег: {issue.extra.get('tag')}")
            print(f"  💡 {issue.suggestion}")

    total = len(report.all_issues)
    fixable = len(report.auto_fixable)
    print(f"\n{_SEP}")
    print(f"ИТОГО:\n  Всего проблем: {total}\n  Автоисправляемых: {fixable}\n  Требуют ручной проверки: {total - fixable}")


def _group_print(issues: list[AuditIssue]) -> None:
    by_type: dict[str, list[AuditIssue]] = {}
    for issue in issues:
        by_type.setdefault(issue.issue_type, []).append(issue)

    labels = {
        "missing_frontmatter": ("❌", "HIGH", "Missing frontmatter"),
        "too_short": ("⚠️", "MEDIUM", "Too short"),
        "untitled": ("⚠️", "MEDIUM", "Untitled notes"),
    }
    for itype, group in by_type.items():
        icon, sev, label = labels.get(itype, ("ℹ️", "LOW", itype))
        print(f"{icon} {sev}: {label}")
        for issue in group:
            print(f"  - {issue.file_path}")
        if group[0].auto_fix:
            print(f"  ✅ Авто-исправление доступно")
        elif group[0].suggestion:
            print(f"  💡 {group[0].suggestion}")
        print()


def _apply_auto_fixes(issues: list[AuditIssue], notes: list[Note]) -> None:
    note_map = {n.filename: n for n in notes}
    for issue in issues:
        note = note_map.get(issue.file_path)
        if not note:
            continue
        if issue.fix_action == "add_default_frontmatter":
            _auto_fix_missing_frontmatter(note)
            print(f"  ✅ Добавлен frontmatter: {issue.file_path}")
        elif issue.fix_action == "generate_title_from_content":
            _auto_fix_title(note)
            print(f"  ✅ Переименована заметка: {issue.file_path}")
