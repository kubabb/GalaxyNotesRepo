"""
STORYTELLER (Metadata Agent) – LOCAL MODE
Generuje metadane Sci-Fi (Star_Class, Energy_Level, Brief) lokalnie z tekstu.
Bez API – szybko i niezawodnie.
"""
import re
import json
from pathlib import Path

DEFAULT_BRAIN_PATH = Path(r"C:\Users\kubar\OneDrive\Dokumenty\BRAIN")
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "output"
OUTPUT_FILE = OUTPUT_DIR / "metadata.json"
GALAXY_MAP_DIR = Path(__file__).resolve().parent.parent / ".galaxy_map"

FRONTMATTER_RE = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)


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


def star_class_from_name(name: str, text_len: int) -> str:
    """Heurystyka klasy gwiazdy."""
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
    """Heurystyka energii."""
    score = text_len / 1000 + link_count * 2
    if score > 15:
        return "Krytyczna"
    if score > 8:
        return "Wysoka"
    if score > 3:
        return "Srednia"
    return "Niska"


def brief_from_text(text: str, name: str) -> str:
    """Generuje dokładnie 10 wyrazów jako brief."""
    clean = clean_markdown(text)
    if not clean:
        words = ["Plik", name.replace("_", " "), "bez", "zawartosci", "tekstowej", "w", "vault", "BRAIN", "GalaxyNotes", "."]
    else:
        words = clean.split()
    
    # Weź pierwsze 10 słów lub uzupełnij
    brief_words = words[:10]
    while len(brief_words) < 10:
        brief_words.append("[...]")
    
    return " ".join(brief_words)


def count_wikilinks(text: str) -> int:
    """Liczy linki [[WikiLink]]."""
    return len(re.findall(r"\[\[[^\]]+\]\]", text))


def analyze_local(md_file: Path, vault_path: Path) -> dict:
    """Przetwarza jeden plik .md – całkowicie lokalnie."""
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
    brief = brief_from_text(raw, name)

    # Znajdź linki w tekście jako suggested_links
    links = re.findall(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", raw)
    links = [l.strip() for l in links if l.strip() != name]
    links = list(dict.fromkeys(links))[:5]  # Max 5, unikalne

    return {
        "file": str(md_file.relative_to(vault_path)).replace("\\", "/"),
        "tooltip": tooltip,
        "star_class": star_class,
        "energy_level": energy_level,
        "brief": brief,
        "suggested_links": links,
        "stats": {
            "char_count": text_len,
            "wikilink_count": link_count
        }
    }


def process_vault(vault_path: Path = DEFAULT_BRAIN_PATH):
    """Przetwarza cały vault i zapisuje metadata.json."""
    if not vault_path.exists():
        raise FileNotFoundError(f"Vault BRAIN nie istnieje: {vault_path}")

    print(f"[STORYTELLER] [LOCAL MODE] Czytam notatki z {vault_path}...")
    md_files = list(vault_path.rglob("*.md"))
    md_files = [f for f in md_files if ".git" not in str(f)]

    print(f"[STORYTELLER] Znaleziono {len(md_files)} notatek do analizy.")
    metadata = {}

    for idx, md_file in enumerate(md_files, 1):
        result = analyze_local(md_file, vault_path)
        if result:
            key = md_file.stem
            metadata[key] = result
            if idx % 10 == 0:
                print(f"[STORYTELLER] [{idx}/{len(md_files)}] Przetworzono...")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"[STORYTELLER] Zapisano metadata.json ({len(metadata)} wpisów) w {OUTPUT_FILE}")
    return OUTPUT_FILE


if __name__ == "__main__":
    process_vault()
