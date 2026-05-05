"""
IMPORTER Agent — GalaxyNotesProject

Skanuje dowolny folder, ekstrahuje tekst z plików (markdown i non-markdown),
zapisuje tymczasowe `.md` w `data/inbox/`. Obsługuje `.md`, `.txt`, `.pdf`,
`.docx`, `.html`, `.py`, `.js`, `.json`.

Brak twardych zależności: jeśli PyPDF2 lub python-docx nie są zainstalowane,
pliki PDF/DOCX są pomijane z warningiem (nie crash).

Użycie:
    python src/importer.py --source "C:/path/to/notes"
"""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

# Rozszerzenia obsługiwane przez agenta
SUPPORTED_EXTENSIONS = {".md", ".txt", ".pdf", ".docx", ".html", ".py", ".js", ".json"}
TEXT_EXTENSIONS = {".txt", ".py", ".js", ".json", ".html"}
SKIP_DIRS = {".git", "__pycache__", "node_modules"}
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB


def _read_text_file(file_path: Path) -> str:
    """Odczytuje zawartość pliku tekstowego jako string."""
    return file_path.read_text(encoding="utf-8")


def _read_pdf(file_path: Path) -> str | None:
    """Ekstrahuje tekst z PDF przy użyciu PyPDF2 (opcjonalnie)."""
    try:
        import PyPDF2
    except ImportError:
        print(f"[IMPORTER] WARNING: PyPDF2 nie jest zainstalowane. Pomijam: {file_path}")
        return None

    text_parts = []
    try:
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
    except Exception as e:
        print(f"[IMPORTER] WARNING: Błąd odczytu PDF {file_path}: {e}")
        return None

    return "\n".join(text_parts)


def _read_docx(file_path: Path) -> str | None:
    """Ekstrahuje tekst z DOCX przy użyciu python-docx (opcjonalnie)."""
    try:
        import docx
    except ImportError:
        print(f"[IMPORTER] WARNING: python-docx nie jest zainstalowane. Pomijam: {file_path}")
        return None

    try:
        document = docx.Document(file_path)
        paragraphs = [p.text for p in document.paragraphs if p.text]
        return "\n".join(paragraphs)
    except Exception as e:
        print(f"[IMPORTER] WARNING: Błąd odczytu DOCX {file_path}: {e}")
        return None


def _extract_text(file_path: Path) -> str | None:
    """Ekstrahuje tekst z pliku w zależności od rozszerzenia."""
    ext = file_path.suffix.lower()

    if ext in TEXT_EXTENSIONS:
        return _read_text_file(file_path)
    elif ext == ".pdf":
        return _read_pdf(file_path)
    elif ext == ".docx":
        return _read_docx(file_path)
    else:
        return None


def _make_frontmatter(rel_path: str, fmt: str, char_count: int) -> str:
    """Generuje blok YAML frontmatter dla zaimportowanego pliku."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    return (
        "---\n"
        f'original_file: "{rel_path}"\n'
        f'format: "{fmt}"\n'
        f'imported_at: "{now}"\n'
        f'extracted_chars: {char_count}\n'
        f'ai_ready: true\n'
        "---\n"
    )


def _to_forward_slashes(path: Path) -> str:
    """Zwraca ścieżkę jako string z forward slashami."""
    return path.as_posix()


def import_folder(source_path: str, inbox_path: str = "data/inbox") -> dict:
    """
    Główna funkcja agenta IMPORTER.

    Args:
        source_path: Ścieżka do folderu źródłowego z notatkami.
        inbox_path: Ścieżka docelowa dla zaimportowanych plików (domyślnie "data/inbox").

    Returns:
        Słownik: {"imported": int, "skipped": int, "inbox_path": str}
    """
    source = Path(source_path).resolve()
    inbox = Path(inbox_path).resolve()

    if not source.exists():
        raise FileNotFoundError(f"Ścieżka źródłowa nie istnieje: {source}")
    if not source.is_dir():
        raise NotADirectoryError(f"Ścieżka źródłowa nie jest folderem: {source}")

    # Upewnij się, że inbox istnieje
    inbox.mkdir(parents=True, exist_ok=True)

    imported_count = 0
    skipped_count = 0

    for item in source.rglob("*"):
        # Pomijaj katalogi — iterujemy po plikach
        if not item.is_file():
            continue

        # Pomijaj foldery w ścieżce (relatywne do source)
        try:
            rel_parts = item.relative_to(source).parts
        except ValueError:
            continue

        if any(part in SKIP_DIRS for part in rel_parts[:-1]):
            skipped_count += 1
            continue

        ext = item.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            skipped_count += 1
            continue

        # Sanity check rozmiaru
        try:
            file_size = item.stat().st_size
        except OSError:
            skipped_count += 1
            continue

        if file_size > MAX_FILE_SIZE_BYTES:
            print(f"[IMPORTER] SKIP (>{MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB): {item}")
            skipped_count += 1
            continue

        # Oblicz ścieżkę relatywną w inbox (zachowaj strukturę)
        rel_to_source = item.relative_to(source)
        rel_str = _to_forward_slashes(rel_to_source)

        if ext == ".md":
            # Kopiuj markdown bez zmian, zachowując strukturę
            target_file = inbox / rel_to_source
            target_file.parent.mkdir(parents=True, exist_ok=True)
            try:
                target_file.write_bytes(item.read_bytes())
                imported_count += 1
            except Exception as e:
                print(f"[IMPORTER] ERROR kopiowania {item}: {e}")
                skipped_count += 1
        else:
            # Ekstrahuj tekst i zapisz jako .imported.md
            extracted = _extract_text(item)
            if extracted is None:
                skipped_count += 1
                continue

            # Ścieżka docelowa: zachowaj strukturę, zmień nazwę na <oryginał>.imported.md
            # np. notes/foo.py -> inbox/notes/foo.py.imported.md
            target_file = inbox / (rel_str + ".imported.md")
            target_file.parent.mkdir(parents=True, exist_ok=True)

            frontmatter = _make_frontmatter(
                rel_path=rel_str,
                fmt=ext.lstrip("."),
                char_count=len(extracted),
            )
            content = frontmatter + "\n" + extracted

            try:
                target_file.write_text(content, encoding="utf-8")
                imported_count += 1
            except Exception as e:
                print(f"[IMPORTER] ERROR zapisu {target_file}: {e}")
                skipped_count += 1

    result = {
        "imported": imported_count,
        "skipped": skipped_count,
        "inbox_path": _to_forward_slashes(inbox),
    }

    print(f"[IMPORTER] Zakończono. Imported: {imported_count}, Skipped: {skipped_count}, Inbox: {inbox}")
    return result


def main() -> None:
    """CLI entrypoint dla agenta IMPORTER."""
    parser = argparse.ArgumentParser(
        description="IMPORTER Agent — import notatek do data/inbox/",
    )
    parser.add_argument(
        "--source",
        required=True,
        help="Ścieżka do folderu źródłowego z notatkami (np. C:/Users/foo/Notes)",
    )
    parser.add_argument(
        "--inbox",
        default="data/inbox",
        help="Ścieżka docelowa inbox (domyślnie: data/inbox)",
    )
    args = parser.parse_args()

    try:
        result = import_folder(args.source, inbox_path=args.inbox)
        print(result)
    except Exception as e:
        print(f"[IMPORTER] FATAL: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
