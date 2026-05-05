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
# AI ANALIZA (OPENROUTER z RETRY)
# ═══════════════════════════════════════════════════════════════

def call_openrouter(prompt: str, max_retries: int = MAX_RETRIES) -> str:
    """Wywołuje OpenRouter API z retry logic i backoff."""
    if not requests:
        return ""
    if not API_ENABLED:
        return ""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/galaxynotesproject",
        "X-Title": "GalaxyNotesProject"
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": "Jesteś analitykiem semantycznym w stylu Sci-Fi. Odpowiadasz zwięźle i konkretnie w JSON."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 300
    }

    for attempt in range(max_retries):
        try:
            resp = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
            data = resp.json()
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            elif "error" in data:
                err = data["error"]
                code = err.get("code", 0)
                print(f"[STORYTELLER] API error (attempt {attempt+1}/{max_retries}): {err.get('message', 'unknown')}")
                if code == 429 and attempt < max_retries - 1:
                    delay = BACKOFF_DELAYS[min(attempt, len(BACKOFF_DELAYS) - 1)]
                    print(f"[STORYTELLER] Rate limit. Backoff {delay}s...")
                    time.sleep(delay)
                elif code >= 500 and attempt < max_retries - 1:
                    time.sleep(BACKOFF_DELAYS[min(attempt, len(BACKOFF_DELAYS) - 1)])
                else:
                    return ""
            else:
                return ""
        except requests.exceptions.Timeout:
            print(f"[STORYTELLER] Timeout (attempt {attempt+1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(BACKOFF_DELAYS[min(attempt, len(BACKOFF_DELAYS) - 1)])
        except Exception as e:
            print(f"[STORYTELLER] Exception (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
    return ""


def analyze_with_ai(md_file: Path, raw_text: str) -> dict:
    """Używa LLM do wygenerowania metadanych Sci-Fi i sugerowanych linków."""
    preview = raw_text[:2000]
    prompt = f"""Przeanalizuj plik i zwróć WYŁĄCZNIE obiekt JSON (bez markdown, bez komentarzy).

Nazwa: {md_file.name}
Zawartość:
---
{preview}
---

Zwróć JSON z polami:
- "star_class": jedna z ["Projekt aktywny", "Archiwum", "Standard", "Krytyczny", "Eksperymentalny"]
- "energy_level": "Niska" | "Srednia" | "Wysoka" | "Krytyczna"
- "brief": dokładnie 10 wyrazów opisujących plik w stylu "skanu pokładowego"
- "suggested_links": lista max 5 nazw plików (bez ścieżek), które mogą być powiązane tematycznie

Przykład:
{{"star_class":"Projekt aktywny","energy_level":"Wysoka","brief":"Główny koordynator nocnego pipeline'u agentów AI.","suggested_links":["env_guard","galaxy_mapper"]}}"""

    raw = call_openrouter(prompt)
    if not raw:
        return {}

    try:
        cleaned = re.sub(r"```json\s*", "", raw)
        cleaned = re.sub(r"```\s*", "", cleaned)
        data = json.loads(cleaned)
        if all(k in data for k in ["star_class", "energy_level", "brief"]):
            return data
    except json.JSONDecodeError:
        pass
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

    api_failures = 0
    api_failure_threshold = 5  # Po 5 błędach API wyłączamy

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
                    if result.get("source") in ("ai", "ai-upload"):
                        api_failures = max(0, api_failures - 1)
                    if len(processed) % 5 == 0:
                        save_checkpoint(processed, len(all_files))
                        print(f"[STORYTELLER] [{len(processed)}/{len(all_files)}] Checkpoint saved.")
                else:
                    if not success:
                        api_failures += 1
                        if api_failures >= api_failure_threshold:
                            print(f"[STORYTELLER] API failures: {api_failures}. Switching to LOCAL MODE for remaining files.")
                            API_ENABLED = False
            except Exception as e:
                print(f"[STORYTELLER] Błąd przetwarzania {file_path.name}: {e}")

    # Zapisz finalne wyniki
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    save_checkpoint(processed, len(all_files))
    ai_count = sum(1 for v in metadata.values() if v.get("source") in ("ai", "ai-upload"))
    upload_count = sum(1 for v in metadata.values() if v.get("source") in ("local-upload", "ai-upload"))
    local_count = len(metadata) - ai_count - upload_count

    print(f"[STORYTELLER] ZAKONCZONO: {len(metadata)} wpisów (AI: {ai_count}, Local: {local_count}, Upload: {upload_count})")
    print(f"[STORYTELLER] Plik: {OUTPUT_FILE}")
    return OUTPUT_FILE


if __name__ == "__main__":
    process_vault()
