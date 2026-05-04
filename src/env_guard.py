"""
SECURITY-OFFICER
Odpowiada za bezpieczne przechowywanie kluczy API,
zarządzanie plikami .env oraz .gitignore.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / "config" / ".env"
GITIGNORE_PATH = PROJECT_ROOT / ".gitignore"

REQUIRED_KEYS = ["OPENROUTER_API_KEY"]
REQUIRED_GITIGNORE_PATTERNS = [
    ".env",
    "config/.env",
    "__pycache__/",
    "*.pyc",
    ".opencode/node_modules/",
    "logs/",
]


def load_env():
    """Ładuje zmienne środowiskowe z .env w root projektu."""
    if ENV_PATH.exists():
        load_dotenv(dotenv_path=ENV_PATH, override=True)
    else:
        print("[SECURITY-OFFICER] BŁĄD: Brak pliku config/.env!")
        print(f"[SECURITY-OFFICER] Utwórz go na podstawie {PROJECT_ROOT / '.env.example'} lub uruchom setup.ps1")
        sys.exit(1)


def check_api_keys():
    """Sprawdza obecność wymaganych kluczy API."""
    missing = []
    for key in REQUIRED_KEYS:
        value = os.getenv(key)
        if not value or value.strip() == "" or "tutaj_wstaw" in value.lower():
            missing.append(key)
    if missing:
        print(f"[SECURITY-OFFICER] BŁĄD: Brakujące klucze API: {', '.join(missing)}")
        print("[SECURITY-OFFICER] Uzupełnij je w pliku .env i uruchom ponownie.")
        sys.exit(1)
    print("[SECURITY-OFFICER] Wszystkie klucze API są obecne i poprawne.")


def check_gitignore():
    """Sprawdza, czy .gitignore zawiera wymagane wpisy."""
    if not GITIGNORE_PATH.exists():
        print("[SECURITY-OFFICER] OSTRZEŻENIE: Brak .gitignore. Tworzę domyślny...")
        create_default_gitignore()
        return False

    content = GITIGNORE_PATH.read_text(encoding="utf-8")
    missing_patterns = []
    for pattern in REQUIRED_GITIGNORE_PATTERNS:
        if pattern not in content:
            missing_patterns.append(pattern)

    if missing_patterns:
        print(f"[SECURITY-OFFICER] OSTRZEŻENIE: .gitignore nie zawiera: {missing_patterns}")
        return False

    print("[SECURITY-OFFICER] .gitignore zawiera wszystkie wymagane wpisy.")
    return True


def create_default_gitignore():
    """Tworzy domyślny .gitignore, jeśli nie istnieje."""
    default = """# Python
__pycache__/
*.py[cod]
env/
venv/
.venv/

# Secrets
.env

# Node
.opencode/node_modules/
.opencode/package-lock.json

# Logs
logs/
*.log

# IDE
.vscode/
.idea/
"""
    GITIGNORE_PATH.write_text(default, encoding="utf-8")
    print(f"[SECURITY-OFFICER] Utworzono domyślny .gitignore w {GITIGNORE_PATH}")


def validate_before_push():
    """Walidacja przed pushem na GitHub.
    Jeśli coś nie trybi – blokuje push.
    """
    print("[SECURITY-OFFICER] Sprawdzam bezpieczeństwo przed push...")
    load_env()
    check_api_keys()
    if not check_gitignore():
        print("[SECURITY-OFFICER] BŁĄD: .gitignore nie jest w pełni skonfigurowany. Push BLOKOWANY.")
        sys.exit(1)
    print("[SECURITY-OFFICER] Wszystko OK – push dozwolony.")


def boot_check():
    """Sprawdzenie przy każdym uruchomieniu projektu."""
    load_env()
    check_api_keys()
    check_gitignore()


if __name__ == "__main__":
    boot_check()
