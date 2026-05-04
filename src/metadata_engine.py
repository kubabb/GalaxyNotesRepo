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
API_ENABLED = OPENROUTER_API_KEY and "tutaj" not in OPENROUTER_API_KEY.lower() and len(OPENROUTER_API_KEY) > 20


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
        return "Krytyczny"
    if "plan" in low or "adr" in low or "feature" in low:
        return "Projekt aktywny"
    if "index" in low or "log" in low:
        return "Archiwum"
    if text_len > 5000:
        return "Projekt aktywny"
    if text_len < 500:
        return "Standard"
    return "Standard"


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
    """Generuje dokładnie 10 wyrazów jako brief – lokalnie."""
    clean = clean_markdown(text)
    if not clean:
        words = ["Plik", name.replace("_", " "), "bez", "zawartosci", "tekstowej", "w", "vault", "BRAIN", "GalaxyNotes", "."]
    else:
        words = clean.split()
    brief_words = words[:10]
    while len(brief_words) < 10:
        brief_words.append("[...]")
    return " ".join(brief_words)


def count_wikilinks(text: str) -> int:
    return len(re.findall(r"\[\[[^\]]+\]\]", text))


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

    return {
        "file": str(md_file.relative_to(vault_path)).replace("\\", "/"),
        "tooltip": tooltip,
        "star_class": star_class,
        "energy_level": energy_level,
        "brief": brief,
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


def process_single_file(md_file: Path, vault_path: Path, processed: set) -> tuple:
    """Przetwarza jeden plik (AI + fallback). Zwraca (key, result, success)."""
    key = md_file.stem
    if key in processed:
        return key, None, True

    try:
        raw = md_file.read_text(encoding="utf-8")
    except Exception as e:
        print(f"[STORYTELLER] Pominięto {md_file}: {e}")
        return key, None, False

    # Próbuj AI najpierw
    ai_result = None
    if API_ENABLED:
        ai_result = analyze_with_ai(md_file, raw)

    if ai_result:
        result = {
            "file": str(md_file.relative_to(vault_path)).replace("\\", "/"),
            "tooltip": extract_first_sentence(clean_markdown(raw)) or f"Notatka {key}.",
            "star_class": ai_result.get("star_class", "Standard"),
            "energy_level": ai_result.get("energy_level", "Srednia"),
            "brief": ai_result.get("brief", "Brak opisu"),
            "suggested_links": ai_result.get("suggested_links", []),
            "stats": {
                "char_count": len(clean_markdown(raw)),
                "wikilink_count": count_wikilinks(raw)
            },
            "source": "ai"
        }
    else:
        # Fallback lokalny
        result = analyze_local(md_file, vault_path)

    return key, result, result is not None


def process_vault(vault_path: Path = DEFAULT_BRAIN_PATH):
    """Przetwarza cały vault z batch processing i checkpointami."""
    if not vault_path.exists():
        raise FileNotFoundError(f"Vault nie istnieje: {vault_path}")

    print(f"[STORYTELLER] [EVOLUTION v2.0] Skanuję {vault_path}...")
    print(f"[STORYTELLER] API: {'WLACZONE' if API_ENABLED else 'WYLACZONE (LOCAL MODE)'}")

    md_files = list(vault_path.rglob("*.md"))
    md_files = [f for f in md_files if ".git" not in str(f)]

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

    pending = [f for f in md_files if f.stem not in processed]
    print(f"[STORYTELLER] Znaleziono {len(md_files)} notatek. Do przetworzenia: {len(pending)}. Batch size: {MAX_CONCURRENT}")

    api_failures = 0
    api_failure_threshold = 5  # Po 5 błędach API wyłączamy

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT) as executor:
        future_to_file = {
            executor.submit(process_single_file, md_file, vault_path, processed): md_file
            for md_file in pending
        }

        for future in concurrent.futures.as_completed(future_to_file):
            md_file = future_to_file[future]
            try:
                key, result, success = future.result()
                if success and result:
                    metadata[key] = result
                    processed.add(key)
                    if result.get("source") == "ai":
                        api_failures = max(0, api_failures - 1)
                    if len(processed) % 5 == 0:
                        save_checkpoint(processed, len(md_files))
                        print(f"[STORYTELLER] [{len(processed)}/{len(md_files)}] Checkpoint saved.")
                else:
                    if not success:
                        api_failures += 1
                        if api_failures >= api_failure_threshold:
                            print(f"[STORYTELLER] API failures: {api_failures}. Switching to LOCAL MODE for remaining files.")
                            API_ENABLED = False
            except Exception as e:
                print(f"[STORYTELLER] Błąd przetwarzania {md_file.name}: {e}")

    # Zapisz finalne wyniki
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    save_checkpoint(processed, len(md_files))
    ai_count = sum(1 for v in metadata.values() if v.get("source") == "ai")
    local_count = len(metadata) - ai_count

    print(f"[STORYTELLER] ZAKONCZONO: {len(metadata)} wpisów (AI: {ai_count}, Local: {local_count})")
    print(f"[STORYTELLER] Plik: {OUTPUT_FILE}")
    return OUTPUT_FILE


if __name__ == "__main__":
    process_vault()
