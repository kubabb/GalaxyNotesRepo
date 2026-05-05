"""
STORYTELLER (Metadata Agent) – EVOLUTION v2.0
Deep Scan AI z retry logic, batch processing i fallbackiem lokalnym.
Wykorzystuje OpenRouter API (Google Gemma 4) z backoff.
"""
import os
import re
import json
import time
import concurrent.futures
from pathlib import Path
from dotenv import load_dotenv

try:
    import requests
except ImportError:
    requests = None

try:
    import ml_engine
except ImportError:
    ml_engine = None

# Ładuj .env z config/
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
ENV_PATH = PROJECT_ROOT / "config" / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH, override=True)

DEFAULT_BRAIN_PATH = Path(r"C:\Users\kubar\OneDrive\Dokumenty\BRAIN")
OUTPUT_DIR = PROJECT_ROOT / "data" / "output"
OUTPUT_FILE = OUTPUT_DIR / "metadata.json"
PROGRESS_FILE = OUTPUT_DIR / "progress.json"
GALAXY_MAP_DIR = PROJECT_ROOT / ".galaxy_map"

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemma-4-26b-a4b-it:free")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

FRONTMATTER_RE = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)

# Retry config
MAX_RETRIES = 3
BACKOFF_DELAYS = [2, 4, 8]  # seconds
MAX_CONCURRENT = 3
API_ENABLED = False  # WATCHMAN: API rate limited – LOCAL MODE enforced

# Multi-format scan config
ALLOWED_EXTS = {".md", ".txt", ".pdf", ".docx", ".html", ".py", ".js", ".json"}
SKIP_DIRS = {".git", "__pycache__", "node_modules", "data", ".galaxy_map"}


def clean_markdown(text: str) -> str:
    """Usuwa frontmatter, nagłówki markdown i linki."""
    text = FRONTMATTER_RE.sub("", text)
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\[\[[^\]|]+\|([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"[*_]{1,2}", "", text)
    text = re.sub(r"^\s*[-*+]\s*", "", text, flags=re.MULTILINE)
    text = " ".join(text.split())
    return text.strip()


def extract_first_sentence(text: str) -> str:
    """Wyciąga pierwsze sensowne zdanie z tekstu."""
    match = re.search(r"([^.!?]+[.!?])", text)
    if match:
        sentence = match.group(1).strip()
        if len(sentence) > 10:
            return sentence
    fallback = text[:120]
    if len(text) > 120:
        fallback += "..."
    return fallback


# ═══════════════════════════════════════════════════════════════
# LOKALNA ANALIZA (FALLBACK)
# ═══════════════════════════════════════════════════════════════

def star_class_from_name(name: str, text_len: int) -> str:
    low = name.lower()
    if "bug" in low or "error" in low:
        return "Krytyczna anomalia"
    if "plan" in low or "adr" in low or "feature" in low:
        return "Aktywny sektor"
    if "index" in low or "log" in low:
        return "Archiwum danych"
    if text_len > 5000:
        return "Aktywny sektor"
    if text_len < 500:
        return "Standardowy sektor"
    return "Standardowy sektor"


def energy_level_from_size(text_len: int, link_count: int) -> str:
    score = text_len / 1000 + link_count * 2
    if score > 15:
        return "Krytyczna"
    if score > 8:
        return "Wysoka"
    if score > 3:
        return "Srednia"
    return "Niska"


def brief_from_text_local(text: str, name: str) -> str:
    """Generuje brief w stylu raportu z misji – max 15 wyrazów, bez JSON i klamerek."""
    clean = clean_markdown(text)
    sector = name.replace("_", " ").replace("-", " ").strip()
    sector_words = sector.split()
    if len(sector_words) > 3:
        sector = " ".join(sector_words[:3])

    if not clean:
        brief = f"Anomalia wykryta w module {sector}. Stan: Krytyczny. Zalecana interwencja."
    else:
        text_len = len(clean)
        if text_len > 5000:
            stan = "Aktywny"
        elif text_len < 500:
            stan = "Stabilny"
        else:
            stan = "Stabilny"
        brief = f"Wykryto dane strukturalne. Sektor: {sector}. Stan: {stan}."

    words = brief.split()
    if len(words) > 15:
        words = words[:15]
        brief = " ".join(words)
        if not brief.endswith("."):
            brief += "."
    return brief


def count_wikilinks(text: str) -> int:
    return len(re.findall(r"\[\[[^\]]+\]\]", text))


def extract_text_from_file(file_path: Path) -> tuple:
    """Ekstrahuje tekst z różnych formatów. Zwraca (text, is_imported_md, original_path)."""
    suffix = file_path.suffix.lower()

    if suffix == ".md":
        if file_path.name.endswith(".imported.md"):
            try:
                raw = file_path.read_text(encoding="utf-8")
                original = str(file_path).replace("\\", "/")
                fm_match = FRONTMATTER_RE.search(raw)
                if fm_match:
                    fm = raw[:fm_match.end()]
                    content = raw[fm_match.end():]
                    m = re.search(r'original_file:\s*["\']?([^"\n]+)', fm)
                    if m:
                        original = m.group(1).strip().strip('"').strip("'")
                else:
                    content = raw
                return content, True, original
            except Exception:
                return "", True, str(file_path).replace("\\", "/")
        else:
            try:
                return file_path.read_text(encoding="utf-8"), False, None
            except Exception:
                return "", False, None

    if suffix in {".txt", ".py", ".js", ".json", ".html"}:
        try:
            return file_path.read_text(encoding="utf-8"), False, None
        except Exception:
            return "", False, None

    if suffix == ".pdf":
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(str(file_path))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            return text, False, None
        except Exception as e:
            print(f"[STORYTELLER] PDF extract failed {file_path}: {e}")
            return "", False, None

    if suffix == ".docx":
        try:
            from docx import Document
            doc = Document(str(file_path))
            text = "\n".join(p.text for p in doc.paragraphs)
            return text, False, None
        except Exception as e:
            print(f"[STORYTELLER] DOCX extract failed {file_path}: {e}")
            return "", False, None

    return "", False, None


def analyze_local(md_file: Path, vault_path: Path) -> dict:
    """Przetwarza plik .md całkowicie lokalnie (fallback)."""
    try:
        raw = md_file.read_text(encoding="utf-8")
    except Exception as e:
        print(f"[STORYTELLER] Pominięto {md_file}: {e}")
        return None

    clean = clean_markdown(raw)
    text_len = len(clean)
    link_count = count_wikilinks(raw)
    name = md_file.stem

    tooltip = extract_first_sentence(clean) if clean else f"Notatka {name}."
    star_class = star_class_from_name(name, text_len)
    energy_level = energy_level_from_size(text_len, link_count)
    brief = brief_from_text_local(raw, name)

    links = re.findall(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", raw)
    links = [l.strip() for l in links if l.strip() != name]
    links = list(dict.fromkeys(links))[:5]

    # Czysta treść .md (bez frontmatter, max 3000 znaków dla HUD)
    content_clean = clean[:3000] if clean else ""

    return {
        "file": str(md_file.relative_to(vault_path)).replace("\\", "/"),
        "tooltip": tooltip,
        "star_class": star_class,
        "energy_level": energy_level,
        "brief": brief,
        "content": content_clean,
        "suggested_links": links,
        "stats": {"char_count": text_len, "wikilink_count": link_count},
        "source": "local"
    }


# ═══════════════════════════════════════════════════════════════
# AI ANALIZA (LOCAL ML via ml_engine)
# ═══════════════════════════════════════════════════════════════

def analyze_with_ai(md_file: Path, raw_text: str, all_texts: list, all_filenames: list) -> dict:
    """Używa lokalnego ML (TF-IDF + k-means) zamiast OpenRouter API."""
    if not ml_engine:
        return {}
    try:
        results = ml_engine.analyze_texts([raw_text] + all_texts, [md_file.stem] + all_filenames)
        return results[0]  # pierwszy wynik to nasz plik
    except Exception as e:
        print(f"[STORYTELLER] ML engine error: {e}")
        return {}


# ═══════════════════════════════════════════════════════════════
# BATCH PROCESSING z CHECKPOINTAMI
# ═══════════════════════════════════════════════════════════════

def load_checkpoint() -> set:
    """Wczytuje checkpoint z poprzedniego uruchomienia."""
    if PROGRESS_FILE.exists():
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return set(data.get("processed", []))
        except Exception:
            pass
    return set()


def save_checkpoint(processed: set, total: int):
    """Zapisuje checkpoint dla wznowienia."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump({"processed": list(processed), "total": total}, f, ensure_ascii=False, indent=2)


def process_single_file(file_path: Path, vault_path: Path, processed: set) -> tuple:
    """Przetwarza jeden plik dowolnego formatu (AI + fallback). Zwraca (key, result, success)."""
    key = file_path.stem
    if key in processed:
        return key, None, True

    text, is_imported, original_path = extract_text_from_file(file_path)
    if text is None:
        text = ""
    if not text and not is_imported:
        return key, None, False

    # Dla imported.md użyj oryginalnego stem jako klucz
    if is_imported and original_path:
        key = Path(original_path).stem

    is_native_md = file_path.suffix.lower() == ".md" and not is_imported

    if is_native_md:
        raw = text
        clean_text = clean_markdown(raw)
        link_count = count_wikilinks(raw)
    else:
        raw = text
        clean_text = raw[:5000]
        link_count = 0

    text_len = len(clean_text)

    # Próbuj AI najpierw
    ai_result = None
    if API_ENABLED:
        ai_result = analyze_with_ai(file_path, raw)

    if ai_result:
        result = {
            "file": str(file_path.relative_to(vault_path)).replace("\\", "/"),
            "tooltip": extract_first_sentence(clean_text) or f"Notatka {key}.",
            "star_class": ai_result.get("star_class", "Standardowy sektor"),
            "energy_level": ai_result.get("energy_level", "Srednia"),
            "brief": ai_result.get("brief", "Brak opisu"),
            "content": clean_text[:3000],
            "suggested_links": ai_result.get("suggested_links", []),
            "stats": {
                "char_count": text_len,
                "wikilink_count": link_count
            },
            "source": "ai" if is_native_md else "ai-upload"
        }
    else:
        if is_native_md:
            result = analyze_local(file_path, vault_path)
        else:
            result = {
                "file": str(file_path.relative_to(vault_path)).replace("\\", "/"),
                "tooltip": extract_first_sentence(clean_text) or f"Notatka {key}.",
                "star_class": star_class_from_name(key, text_len),
                "energy_level": energy_level_from_size(text_len, link_count),
                "brief": brief_from_text_local(raw, key),
                "content": clean_text[:3000],
                "suggested_links": [],
                "stats": {"char_count": text_len, "wikilink_count": link_count},
                "source": "local-upload"
            }

    return key, result, result is not None


def process_vault(vault_path: Path = DEFAULT_BRAIN_PATH):
    """Przetwarza cały vault z batch processing i checkpointami."""
    global API_ENABLED
    if not vault_path.exists():
        raise FileNotFoundError(f"Vault nie istnieje: {vault_path}")

    print(f"[STORYTELLER] [EVOLUTION v2.0] Skanuję {vault_path}...")
    print(f"[STORYTELLER] API: {'WLACZONE' if API_ENABLED else 'WYLACZONE (LOCAL MODE)'}")

    # Multi-format scan
    all_files = []
    for f in vault_path.rglob("*"):
        if any(part in SKIP_DIRS for part in f.parts):
            continue
        if f.is_file() and f.suffix.lower() in ALLOWED_EXTS:
            all_files.append(f)

    processed = load_checkpoint()
    metadata = {}

    # Wczytaj istniejące metadata jeśli są
    if OUTPUT_FILE.exists():
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            print(f"[STORYTELLER] Wczytano {len(metadata)} istniejących wpisów.")
        except Exception:
            pass

    pending = [f for f in all_files if f.stem not in processed]
    print(f"[STORYTELLER] Znaleziono {len(all_files)} plików. Do przetworzenia: {len(pending)}. Batch size: {MAX_CONCURRENT}")

    # Batch ML processing
    if ml_engine and len(pending) > 0:
        print(f"[STORYTELLER] Running local ML on {len(pending)} files...")
        all_texts = []
        all_files = []
        for f in pending:
            text, _, _ = extract_text_from_file(f)
            all_texts.append(text[:5000])  # truncate dla szybkości
            all_files.append(f.stem)
        
        try:
            ml_results = ml_engine.analyze_texts(all_texts, all_files)
            
            for i, f in enumerate(pending):
                key = f.stem
                result = {
                    "file": str(f.relative_to(vault_path)).replace("\\", "/"),
                    "tooltip": ml_results[i].get("brief", f"Notatka {key}."),
                    "star_class": ml_results[i].get("star_class", "Standardowy sektor"),
                    "energy_level": ml_results[i].get("energy_level", "Srednia"),
                    "brief": ml_results[i].get("brief", "Brak opisu"),
                    "content": all_texts[i][:3000],
                    "suggested_links": ml_results[i].get("suggested_links", []),
                    "stats": {"char_count": len(all_texts[i]), "wikilink_count": 0},
                    "source": "ml-local"
                }
                metadata[key] = result
                processed.add(key)
            
            # Usuń przetworzone z pending
            pending = [f for f in pending if f.stem not in processed]
            print(f"[STORYTELLER] ML batch done. Remaining for local: {len(pending)}")
        except Exception as e:
            print(f"[STORYTELLER] ML batch failed: {e}. Falling back to local processing.")
    
    # Local fallback for remaining files
    if pending:
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT) as executor:
            future_to_file = {
                executor.submit(process_single_file, file_path, vault_path, processed): file_path
                for file_path in pending
            }

            for future in concurrent.futures.as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    key, result, success = future.result()
                    if success and result:
                        metadata[key] = result
                        processed.add(key)
                        if len(processed) % 5 == 0:
                            save_checkpoint(processed, len(all_files))
                            print(f"[STORYTELLER] [{len(processed)}/{len(all_files)}] Checkpoint saved.")
                except Exception as e:
                    print(f"[STORYTELLER] Błąd przetwarzania {file_path.name}: {e}")

    # Zapisz finalne wyniki
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    save_checkpoint(processed, len(all_files))
    ai_count = sum(1 for v in metadata.values() if v.get("source") in ("ai", "ai-upload"))
    ml_count = sum(1 for v in metadata.values() if v.get("source") == "ml-local")
    upload_count = sum(1 for v in metadata.values() if v.get("source") in ("local-upload", "ai-upload"))
    local_count = len(metadata) - ai_count - ml_count - upload_count

    print(f"[STORYTELLER] ZAKONCZONO: {len(metadata)} wpisów (AI: {ai_count}, ML: {ml_count}, Local: {local_count}, Upload: {upload_count})")
    print(f"[STORYTELLER] Plik: {OUTPUT_FILE}")
    return OUTPUT_FILE


if __name__ == "__main__":
    process_vault()
