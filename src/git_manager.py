"""
GIT-PUSHER v2.0
Agresywny zarządca kontroli wersji Git.
Wypycha zmiany per-file lub w batchu, z walidacją bezpieczeństwa.
"""
import os
import sys
import subprocess
import logging
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# --- Logi ---
logging.basicConfig(
    level=logging.INFO,
    format="[GIT-PUSHER] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("git_pusher")

# --- Env ---
ENV_PATH = PROJECT_ROOT / "config" / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH, override=True)

# --- Importy lokalne (watchman-style) ---
try:
    import env_guard
except Exception as e:
    logger.error(f"Nie udało się załadować env_guard: {e}")
    env_guard = None

try:
    import debugger
except Exception as e:
    logger.error(f"Nie udało się załadować debugger: {e}")
    debugger = None

# --- Stan wewnętrzny ---
_consecutive_failures: int = 0


def _run_git(args: list, cwd: Path = None, check: bool = True, silent: bool = True):
    """Wykonuje komendę git. Jeśli silent=True – wycisza stdout."""
    cmd = ["git"] + args
    kwargs = {
        "cwd": cwd or PROJECT_ROOT,
        "text": True,
    }
    if silent:
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = subprocess.PIPE

    result = subprocess.run(cmd, **kwargs)
    if check and result.returncode != 0:
        err = result.stderr.strip() if result.stderr else "(no stderr)"
        raise RuntimeError(f"Git failed: {' '.join(cmd)}\n{err}")
    return result


def _get_remote_url() -> str | None:
    """Buduje URL remote z GITHUB_TOKEN i GITHUB_REPO z .env.
    Jeśli brak tokena – zwraca None (używamy istniejącego remote)."""
    token = os.getenv("GITHUB_TOKEN", "").strip()
    repo = os.getenv("GITHUB_REPO", "").strip()
    if not token or not repo:
        return None

    if repo.startswith("http"):
        if "@" in repo:
            return repo
        return repo.replace("https://", f"https://{token}@")
    return f"https://{token}@github.com/{repo}.git"


def ensure_git_repo():
    """Inicjalizuje lokalne repo git jeśli nie istnieje."""
    git_dir = PROJECT_ROOT / ".git"
    if not git_dir.exists():
        logger.info("Inicjalizuję lokalne repo git...")
        _run_git(["init"], silent=True)
        _run_git(["branch", "-M", "main"], silent=True)


def ensure_remote():
    """Sprawdza czy remote 'origin' istnieje.
    Jeśli nie – próbuje dodać z GITHUB_TOKEN. Jeśli brak tokena – loguje info i puszuje bez remote (lokalnie)."""
    try:
        result = _run_git(["remote"], silent=True)
        remotes = result.stdout.strip().splitlines() if result.stdout else []
        url = _get_remote_url()
        if "origin" not in remotes:
            if url:
                logger.info("Dodaję remote origin z tokenem...")
                _run_git(["remote", "add", "origin", url], silent=True)
            else:
                logger.warning("Brak GITHUB_TOKEN – używam istniejącego remote lub push lokalny")
        else:
            # Jeśli mamy token – aktualizujemy URL; jeśli nie – zostawiamy jak jest
            if url:
                _run_git(["remote", "set-url", "origin", url], silent=True)
    except RuntimeError:
        raise


def push_per_file(filename: str) -> bool:
    """
    Wykonuje: git add . → git commit → git push.
    Commit: "Galaxy Pilot: Mapping star [filename]"
    Jeśli brak GITHUB_TOKEN – pushuje przez istniejący remote (SSH/HTTPS credentials).
    Jeśli push zawodzi – loguje błąd i kontynuuje (nie przerywa pipeline).
    Zwraca True/False.
    """
    global _consecutive_failures
    try:
        ensure_git_repo()
        ensure_remote()

        _run_git(["add", "."], silent=True)
        _run_git(["commit", "-m", f"Galaxy Pilot: Mapping star {filename}"], silent=True)
        _run_git(["push", "-u", "origin", "main"], silent=True)

        logger.info(f"SUKCES: push_per_file({filename})")
        _consecutive_failures = 0
        return True
    except RuntimeError as e:
        logger.error(f"BŁĄD push_per_file({filename}): {e}")
        _consecutive_failures += 1
        return False


def batch_push(count: int) -> bool:
    """
    Commit z komunikatem "Galaxy Pilot: Batch mapping [count] stars" → push.
    Używane gdy push_per_file zawodzi więcej niż 3 razy z rzędu.
    Zwraca True/False.
    """
    global _consecutive_failures
    try:
        ensure_git_repo()
        ensure_remote()

        _run_git(["add", "."], silent=True)
        _run_git(["commit", "-m", f"Galaxy Pilot: Batch mapping {count} stars"], silent=True)
        _run_git(["push", "-u", "origin", "main"], silent=True)

        logger.info(f"SUKCES: batch_push({count})")
        _consecutive_failures = 0
        return True
    except RuntimeError as e:
        logger.error(f"BŁĄD batch_push({count}): {e}")
        return False


def validate_and_push():
    """
    Wywołuje env_guard.validate_before_push() oraz debugger.scan_for_leaks().
    Jeśli oba PASS – wykonuje push.
    """
    # 1. env_guard
    if env_guard is not None:
        try:
            env_guard.validate_before_push()
            logger.info("PASS: env_guard.validate_before_push()")
        except SystemExit as e:
            logger.error(f"FAIL: env_guard.validate_before_push() (exit {e.code})")
            return
        except Exception as e:
            logger.error(f"FAIL: env_guard.validate_before_push(): {e}")
            return
    else:
        logger.warning("SKIP: env_guard niedostępny")

    # 2. debugger
    if debugger is not None:
        try:
            result = debugger.scan_for_leaks()
            if result is False:
                logger.error("FAIL: debugger.scan_for_leaks() zwrócił False")
                return
            logger.info("PASS: debugger.scan_for_leaks()")
        except Exception as e:
            logger.error(f"FAIL: debugger.scan_for_leaks(): {e}")
            return
    else:
        logger.warning("SKIP: debugger niedostępny")

    # 3. Push
    try:
        ensure_git_repo()
        ensure_remote()
        _run_git(["add", "."], silent=True)
        _run_git(["commit", "-m", "Galaxy Pilot: Validated push"], silent=True)
        _run_git(["push", "-u", "origin", "main"], silent=True)
        logger.info("SUKCES: validate_and_push()")
    except RuntimeError as e:
        logger.error(f"BŁĄD validate_and_push(): {e}")


def aggressive_push(filename: str) -> bool:
    """
    Wrapper: push per file z automatycznym fallbackiem do batch_push
    po >3 nieudanych próbach z rzędu.
    """
    success = push_per_file(filename)
    if not success and _consecutive_failures > 3:
        logger.warning(
            f"{_consecutive_failures} nieudanych prób z rzędu – uruchamiam batch_push..."
        )
        batch_push(_consecutive_failures)
    return success


if __name__ == "__main__":
    # Demo – można podać nazwę pliku jako argument
    target = sys.argv[1] if len(sys.argv) > 1 else "demo_star.md"
    aggressive_push(target)
