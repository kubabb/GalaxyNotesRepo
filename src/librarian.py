"""
LIBRARIAN v2.0 (Knowledge Keeper)
Agent Bibliotekarz. Zarządza strukturą lustrzaną `.galaxy_map/`.
Dla każdego pliku projektu tworzy odpowiednik `.md` z analizą kontekstową i linkami.
"""
import os
import re
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GALAXY_MAP_DIR = PROJECT_ROOT / ".galaxy_map"

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".galaxy_map", "data", ".opencode"}
SKIP_EXTS = {".pyc", ".log", ".env", ".png", ".jpg", ".jpeg", ".gif", ".ico"}

TAGS_BY_EXT = {
    ".py": ["#python", "#backend", "#agent"],
    ".md": ["#markdown", "#docs", "#design"],
    ".html": ["#frontend", "#cockpit", "#3d"],
    ".json": ["#data", "#config"],
    ".ps1": ["#powershell", "#setup"],
    ".txt": ["#docs", "#text"],
}


def should_skip(path: Path) -> bool:
    parts = set(path.parts)
    if SKIP_DIRS & parts:
        return True
    if path.suffix.lower() in SKIP_EXTS:
        return True
    if path.name.startswith(".") and path.is_file():
        return True
    return False


def extract_imports(text: str, ext: str) -> list:
    """Wyciąga nazwy importów/plików do linków Wiki."""
    links = []
    if ext == ".py":
        # import x, from x import y
        for m in re.finditer(r"^\s*(?:import|from)\s+([a-zA-Z_][a-zA-Z0-9_]*)", text, re.MULTILINE):
            links.append(m.group(1))
    elif ext == ".html":
        for m in re.finditer(r'src=["\']([^"\']+)["\']', text):
            links.append(Path(m.group(1)).stem)
        for m in re.finditer(r'href=["\']([^"\']+)["\']', text):
            links.append(Path(m.group(1)).stem)
    return list(dict.fromkeys(links))[:8]


def generate_mirror_md(source_file: Path) -> str:
    rel = source_file.relative_to(PROJECT_ROOT)
    ext = source_file.suffix.lower()
    name = source_file.stem
    date_str = datetime.now().isoformat(timespec="seconds")
    tags = TAGS_BY_EXT.get(ext, ["#file"])

    try:
        raw = source_file.read_text(encoding="utf-8", errors="ignore")[:3000]
    except Exception:
        raw = ""

    lines_count = raw.count("\n") + 1 if raw else 0
    imports = extract_imports(raw, ext)
    links_md = " ".join(f"[[{l}]]" for l in imports) if imports else ""

    # Brief analysis based on content
    brief = f"Plik źródłowy `{name}{ext}` w projekcie GalaxyNotesProject."
    if ext == ".py":
        if "def " in raw:
            funcs = re.findall(r"^\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", raw, re.MULTILINE)
            brief = f"Moduł Python zawierający {len(funcs)} funkcji. Główne: {', '.join(funcs[:3])}."
        elif "class " in raw:
            classes = re.findall(r"^\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[\(:]", raw, re.MULTILINE)
            brief = f"Moduł Python z klasą {classes[0] if classes else '---'}."
    elif ext == ".html":
        brief = f"Strona HTML/frontend projektu Galaxy-Pilot."
    elif ext == ".md":
        brief = f"Dokumentacja projektu GalaxyNotesProject."

    frontmatter = f"""---
title: "{name}"
date: {date_str}
type: SourceFile
source: GalaxyNotes
tags: {' '.join(tags)}
---

"""

    body = f"""## Analiza: `{rel.as_posix()}`

{brief}

- **Rozszerzenie:** {ext}
- **Lokalizacja:** `{rel.as_posix()}`
- **Liczba linii:** ~{lines_count}

### Powiązane
{links_md}

### Fragment
```
{raw[:500]}{'...' if len(raw) > 500 else ''}
```

---
*Wygenerowane przez Librarian* | [[01_Projects/GalaxyNotes/PLAN|PLAN]] | [[01_Projects/GalaxyNotes/Project_Log|Project Log]]
"""
    return frontmatter + body


def sync_galaxy_map():
    """Synchronizuje strukturę lustrzaną .galaxy_map/ z aktualnym kodem projektu."""
    print("[LIBRARIAN] Skanuję projekt pod kątem zmian...")
    GALAXY_MAP_DIR.mkdir(parents=True, exist_ok=True)

    source_files = []
    for root, dirs, files in os.walk(PROJECT_ROOT):
        # Pomijaj foldery z SKIP_DIRS
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            fp = Path(root) / f
            if should_skip(fp):
                continue
            source_files.append(fp)

    created = 0
    updated = 0

    for src in source_files:
        rel = src.relative_to(PROJECT_ROOT)
        mirror_path = GALAXY_MAP_DIR / (rel.as_posix() + ".md")
        mirror_path.parent.mkdir(parents=True, exist_ok=True)

        needs_update = True
        if mirror_path.exists():
            # Proste sprawdzenie: jeśli mirror jest nowszy niż źródło, pomiń
            if mirror_path.stat().st_mtime >= src.stat().st_mtime:
                needs_update = False

        if needs_update:
            content = generate_mirror_md(src)
            mirror_path.write_text(content, encoding="utf-8")
            if mirror_path.exists() and mirror_path.stat().st_mtime < src.stat().st_mtime:
                updated += 1
            else:
                created += 1

    print(f"[LIBRARIAN] Synchronizacja zakończona: {created} nowych, {updated} zaktualizowanych.")
    return GALAXY_MAP_DIR


def update_project_log():
    """Aktualizuje Project_Log.md w .galaxy_map (lokalna kopia)."""
    log_path = GALAXY_MAP_DIR / "Project_Log.md"
    date_str = datetime.now().strftime("%Y-%m-%d")
    entry = f"- **{date_str}** — Synchronizacja struktury lustrzanej i pipeline agents.\n"

    if log_path.exists():
        content = log_path.read_text(encoding="utf-8")
    else:
        content = "# Project Log – GalaxyNotesProject\n\n"

    # Dodaj wpis na górze (po nagłówku)
    lines = content.splitlines()
    new_lines = []
    inserted = False
    for line in lines:
        new_lines.append(line)
        if not inserted and line.startswith("# "):
            new_lines.append("")
            new_lines.append(entry.rstrip())
            inserted = True
    if not inserted:
        new_lines.append(entry.rstrip())

    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    print(f"[LIBRARIAN] Zaktualizowano Project_Log.")


if __name__ == "__main__":
    sync_galaxy_map()
    update_project_log()
