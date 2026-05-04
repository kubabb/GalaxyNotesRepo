"""
Galaxy Notes Project – Nocny Pipeline Agentów
Koordynuje ASTRONOMER, STORYTELLER, WATCHMAN i SECURITY-OFFICER,
aby przetworzyć vault BRAIN w interaktywną mapę wiedzy.

Uruchomienie:
    python main.py
    python main.py --push   # dodatkowo wypchnie na GitHub
"""
import argparse
import sys
from pathlib import Path

# Ścieżki
PROJECT_ROOT = Path(__file__).resolve().parent
AGENTS_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(AGENTS_DIR))

import env_guard
import pipeline_guard
import galaxy_mapper
import metadata_engine
import git_manager


def main():
    parser = argparse.ArgumentParser(description="GalaxyNotesProject Pipeline")
    parser.add_argument("--push", action="store_true", help="Wypchnij wyniki na GitHub po zakończeniu")
    parser.add_argument("--brain", type=str, default=r"C:\Users\kubar\OneDrive\Dokumenty\BRAIN",
                        help="Ścieżka do vaultu Obsidian")
    args = parser.parse_args()

    brain_path = Path(args.brain)

    # 1. SECURITY-OFFICER – sprawdzenie przy starcie
    print("\n=== FAZA 1: SECURITY-OFFICER (boot check) ===")
    try:
        env_guard.boot_check()
    except SystemExit as e:
        print(f"[MAIN] Start zablokowany przez SECURITY-OFFICER (kod: {e.code})")
        sys.exit(e.code)

    # 2. ASTRONOMER – zbuduj graf i współrzędne
    print("\n=== FAZA 2: ASTRONOMER (Data Refiner) ===")
    galaxy_file = pipeline_guard.run("ASTRONOMER", galaxy_mapper.refine_galaxy, brain_path)

    # 3. STORYTELLER – wygeneruj metadane/tooltips
    print("\n=== FAZA 3: STORYTELLER (Metadata Agent) ===")
    meta_file = pipeline_guard.run("STORYTELLER", metadata_engine.process_vault, brain_path)

    # 4. Podsumowanie
    print("\n=== PIPELINE ZAKOŃCZONY ===")
    if galaxy_file:
        print(f"  Galaxy data : {galaxy_file}")
    if meta_file:
        print(f"  Metadata    : {meta_file}")

    if args.push:
        print("\n=== FAZA 4: GIT-PUSHER ===")
        try:
            git_manager.full_push()
        except Exception as e:
            print(f"[MAIN] Błąd podczas pushu: {e}")
            sys.exit(1)

    print("\n[MAIN] Nocna zmiana zakończona. Galaktyka gotowa.")


if __name__ == "__main__":
    main()
