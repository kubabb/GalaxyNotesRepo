"""
WATCHMAN (Supervisor)
Strażnik procesu. Jeśli skrypt napotka błąd (np. uszkodzony plik .md),
decyduje: „pomiń ten plik i idź dalej”, zamiast przerywać pracę całego zespołu.
"""
import traceback
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_FILE = LOG_DIR / "watchman.log"


def _ensure_log_dir():
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def log_error(context: str, exception: Exception, filepath: Path = None):
    """Loguje błąd do pliku z datą i szczegółami."""
    _ensure_log_dir()
    timestamp = datetime.now().isoformat()
    entry = f"[{timestamp}] KONTEXT: {context}\n"
    if filepath:
        entry += f"  PLIK: {filepath}\n"
    entry += f"  BŁĄD: {exception}\n"
    entry += f"  TRACE:\n{traceback.format_exc()}\n"
    entry += "-" * 60 + "\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry)
    print(f"[WATCHMAN] Złapałem błąd w '{context}'. Szczegóły w {LOG_FILE}")


def run(agent_name: str, task_func, *args, **kwargs):
    """
    Wykonuje funkcję agenta w bloku try/except.
    W przypadku błędu loguje go i zwraca None zamiast przerywać pipeline.
    """
    try:
        print(f"[WATCHMAN] Uruchamiam {agent_name}...")
        result = task_func(*args, **kwargs)
        print(f"[WATCHMAN] {agent_name} zakończony sukcesem.")
        return result
    except Exception as e:
        log_error(agent_name, e, kwargs.get("filepath") or kwargs.get("file_path"))
        return None


def run_iterable(agent_name: str, task_func, items: list):
    """
    Przetwarza listę elementów przez task_func,
    pomijając te, które rzucają wyjątek.
    Zwraca listę wyników (z None dla błędnych elementów).
    """
    results = []
    for item in items:
        try:
            result = task_func(item)
            results.append(result)
        except Exception as e:
            log_error(agent_name, e, filepath=Path(str(item)) if isinstance(item, (str, Path)) else None)
            results.append(None)
    return results


if __name__ == "__main__":
    # Demo
    def failing_task(x):
        if x == 2:
            raise ValueError("Uszkodzony plik!")
        return x * 2

    outputs = run_iterable("DemoAgent", failing_task, [1, 2, 3])
    print("Wyniki:", outputs)
