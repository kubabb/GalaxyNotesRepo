"""
GIT-PUSHER
Zarządca kontroli wersji Git.
Tworzy repozytorium na GitHubie i wypycha tam projekt.
Przed pushem sprawdza konfigurację z SECURITY-OFFICER.
"""
import os
import sys
import subprocess
import requests
from pathlib import Path

# Import lokalny – watchman obsłuży brak modułu
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

try:
    import env_guard as so
except Exception as e:
    print(f"[GIT-PUSHER] Nie udało się załadować env_guard: {e}")
    sys.exit(1)

GITHUB_API = "https://api.github.com"


def _run_git(args: list, cwd: Path = None):
    """Wykonuje komendę git i zwraca stdout."""
    cmd = ["git"] + args
    result = subprocess.run(cmd, cwd=cwd or PROJECT_ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Git failed: {' '.join(cmd)}\n{result.stderr}")
    return result.stdout.strip()


def ensure_git_repo():
    """Inicjalizuje lokalne repo git jeśli nie istnieje."""
    git_dir = PROJECT_ROOT / ".git"
    if not git_dir.exists():
        print("[GIT-PUSHER] Inicjalizuję lokalne repo git...")
        _run_git(["init"])
        _run_git(["branch", "-M", "main"])


def create_github_repo(repo_name: str = None, private: bool = True):
    """Tworzy repozytorium na GitHubie przez API."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("[GIT-PUSHER] BŁĄD: Brak GITHUB_TOKEN w środowisku.")
        sys.exit(1)

    if repo_name is None:
        repo_name = PROJECT_ROOT.name

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }
    payload = {
        "name": repo_name,
        "private": private,
        "auto_init": False,
    }

    print(f"[GIT-PUSHER] Tworzę repo '{repo_name}' na GitHubie...")
    resp = requests.post(f"{GITHUB_API}/user/repos", headers=headers, json=payload)

    if resp.status_code == 201:
        data = resp.json()
        clone_url = data["clone_url"]
        print(f"[GIT-PUSHER] Repo utworzone: {data['html_url']}")
        return clone_url
    elif resp.status_code == 422:
        # Repo już istnieje
        print("[GIT-PUSHER] Repo prawdopodobnie już istnieje – używam istniejącego.")
        username = _get_github_username(token)
        return f"https://github.com/{username}/{repo_name}.git"
    else:
        raise RuntimeError(f"GitHub API error {resp.status_code}: {resp.text}")


def _get_github_username(token: str) -> str:
    """Pobiera nazwę użytkownika GitHub z API."""
    headers = {"Authorization": f"token {token}"}
    resp = requests.get(f"{GITHUB_API}/user", headers=headers)
    resp.raise_for_status()
    return resp.json()["login"]


def add_remote(repo_url: str):
    """Dodaje remote 'origin' lub aktualizuje go."""
    try:
        remotes = _run_git(["remote"])
        if "origin" in remotes:
            _run_git(["remote", "set-url", "origin", repo_url])
            print("[GIT-PUSHER] Zaktualizowano remote origin.")
        else:
            _run_git(["remote", "add", "origin", repo_url])
            print("[GIT-PUSHER] Dodano remote origin.")
    except Exception as e:
        print(f"[GIT-PUSHER] Błąd przy ustawianiu remote: {e}")
        raise


def commit_and_push(message: str = "update: automatyczny push przez GalaxyNotesProject"):
    """Dodaje, commituje i pushuje zmiany."""
    # Sprawdź czy są zmiany
    status = _run_git(["status", "--porcelain"])
    if not status:
        print("[GIT-PUSHER] Brak zmian do spushowania.")
        return

    _run_git(["add", "."])
    try:
        _run_git(["commit", "-m", message])
    except RuntimeError:
        # Jeśli nic do commitowania (np. tylko untracked ignored)
        pass

    _run_git(["push", "-u", "origin", "main"])
    print("[GIT-PUSHER] Push zakończony sukcesem.")


def full_push(repo_name: str = None, private: bool = True):
    """
    Pełny pipeline puszu:
    1. SECURITY-OFFICER sprawdza .env i .gitignore.
    2. Tworzy repo na GitHubie (jeśli trzeba).
    3. Inicjalizuje git lokalnie.
    4. Dodaje remote, commituje i pushuje.
    """
    so.validate_before_push()
    ensure_git_repo()
    repo_url = create_github_repo(repo_name=repo_name, private=private)
    add_remote(repo_url)
    commit_and_push()


if __name__ == "__main__":
    full_push()
