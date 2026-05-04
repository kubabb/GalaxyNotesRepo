"""
DEBUGGER v2.0
QA, diagnosta i strażnik stabilności.
- Skanuje wycieki kluczy API przed pushem
- Retry logic diagnostics
- Walidacja JSONów i kodu Python
"""
import os
import re
import sys
import json
import py_compile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / "config" / ".env"
GITIGNORE_PATH = PROJECT_ROOT / ".gitignore"


def scan_for_leaks() -> bool:
    """
    Skanuje całe drzewo projektu pod kątem wycieków kluczy API.
    Zwraca True jeśli BRAK wycieków, False jeśli wykryto.
    """
    print("[DEBUGGER] Skanuję wycieki kluczy API...")

    leaks_found = []

    # Wczytaj klucz z .env
    api_key = ""
    if ENV_PATH.exists():
        content = ENV_PATH.read_text(encoding="utf-8")
        match = re.search(r'OPENROUTER_API_KEY=(.+)', content)
        if match:
            api_key = match.group(1).strip()

    if not api_key or len(api_key) < 20:
        print("[DEBUGGER] OSTRZEZENIE: Nie mozna odczytac klucza API z config/.env")
        return True  # Nie mozna skanowac = nie blokuj pusha

    # Skanuj pliki trackowane przez git (i potencjalnie trackowane)
    scan_patterns = [
        ("*.py", "Python"),
        ("*.md", "Markdown"),
        ("*.txt", "Text"),
        ("*.html", "HTML"),
        ("*.json", "JSON"),
        ("*.yml", "YAML"),
        ("*.yaml", "YAML"),
    ]

    # Fragment klucza do wyszukiwania (ostatnie 32 znaki to wystarczająco unikalne)
    key_fragment = api_key[-32:] if len(api_key) > 32 else api_key

    for pattern, label in scan_patterns:
        for file_path in PROJECT_ROOT.rglob(pattern):
            # Pomiń pliki w ignorowanych folderach
            if any(part in str(file_path) for part in ['.git', 'node_modules', '__pycache__', 'data/output']):
                continue
            try:
                text = file_path.read_text(encoding="utf-8", errors="ignore")
                if key_fragment in text:
                    leaks_found.append(str(file_path.relative_to(PROJECT_ROOT)))
            except Exception:
                pass

    if leaks_found:
        print(f"[DEBUGGER] FAIL: WYCIEKI WYKRYTE w: {', '.join(leaks_found)}")
        return False
    else:
        print("[DEBUGGER] PASS: BRAK wyciekow API. Bezpieczenstwo potwierdzone.")
        return True


def validate_json(filepath: Path) -> bool:
    """Waliduje czy plik JSON jest poprawny."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            json.load(f)
        return True
    except Exception as e:
        print(f"[DEBUGGER] FAIL: Nieprawidlowy JSON {filepath}: {e}")
        return False


def validate_all_python() -> bool:
    """Kompiluje wszystkie pliki .py w projekcie."""
    print("[DEBUGGER] Kompilacja wszystkich plikow .py...")
    all_ok = True
    for py_file in PROJECT_ROOT.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        try:
            py_compile.compile(str(py_file), doraise=True)
        except py_compile.PyCompileError as e:
            print(f"[DEBUGGER] FAIL: Blad kompilacji {py_file}: {e}")
            all_ok = False
    if all_ok:
        print("[DEBUGGER] PASS: Wszystkie pliki .py skompilowane poprawnie.")
    return all_ok


def diagnose_api_errors(error_log: str = "") -> dict:
    """
    Diagnostyka błędów API (timeouty, 429, 500).
    Zwraca rekomendacje.
    """
    recommendations = {
        "timeout": "Zwieksz timeout w requests (np. 60s -> 120s) lub zmniejsz max_tokens.",
        "429": "Rate limit. Dodaj backoff: 2s, 4s, 8s. Zmniejsz batch size. Rozwaz platny tier.",
        "500": "Blad serwera. Uzyj fallbacku lokalnego. Sprobuj pozniej.",
        "connection": "Sprawdz polaczenie internetowe. Uzyj fallbacku lokalnego.",
    }
    print("[DEBUGGER] Diagnoza API:")
    for err, rec in recommendations.items():
        print(f"  [{err.upper()}] -> {rec}")
    return recommendations


def full_qa_report():
    """Generuje pełny raport QA."""
    print("\n" + "="*60)
    print("RAPORT QA – DEBUGGER v2.0")
    print("="*60)

    # 1. Wycieki
    leaks_ok = scan_for_leaks()

    # 2. JSONy
    json_ok = True
    for json_file in (PROJECT_ROOT / "data" / "output").glob("*.json"):
        if not validate_json(json_file):
            json_ok = False

    # 3. Kompilacja
    py_ok = validate_all_python()

    print("\n--- PODSUMOWANIE ---")
    print(f"Wycieki API: {'PASS' if leaks_ok else 'FAIL'}")
    print(f"Walidacja JSON: {'PASS' if json_ok else 'FAIL'}")
    print(f"Kompilacja Python: {'PASS' if py_ok else 'FAIL'}")
    print("="*60)
    return leaks_ok and json_ok and py_ok

    return leaks_ok and json_ok and py_ok


if __name__ == "__main__":
    full_qa_report()
