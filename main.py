"""
Galaxy Notes Project – Nocny Pipeline Agentów v3.0 (Parallel)
Koordynuje wszystkich agentów równolegle tam gdzie to możliwe:
  SECURITY-OFFICER -> [ASTRONOMER || STORYTELLER || LIBRARIAN] -> DEBUGGER -> GIT-PUSHER
aby przetworzyć vault BRAIN w interaktywną mapę wiedzy.

Uruchomienie:
    python main.py
    python main.py --brain "C:/path/to/vault"   # override default vault
    python main.py --push                         # dodatkowo git-push
    python main.py --import "C:/path/to/notes"    # importuj notatki do data/inbox/
"""
import argparse
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Ścieżki
PROJECT_ROOT = Path(__file__).resolve().parent
AGENTS_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(AGENTS_DIR))

import env_guard
import pipeline_guard
import galaxy_mapper
import metadata_engine
import debugger
import librarian
import git_manager
import importer


def main():
    parser = argparse.ArgumentParser(description="GalaxyNotesProject Pipeline v3.0 Parallel")
    parser.add_argument("--push", action="store_true", help="Wypchnij wyniki na GitHub po zakończeniu")
    parser.add_argument("--brain", type=str, default=r"C:\Users\kubar\OneDrive\Dokumenty\BRAIN",
                        help="Ścieżka do vaultu Obsidian")
    parser.add_argument("--import", dest="import_folder", type=str, default=None,
                        help="Importuj notatki z podanego folderu do data/inbox/ przed pipeline")
    args = parser.parse_args()

    brain_path = Path(args.brain)

    # 1. SECURITY-OFFICER – sprawdzenie przy starcie (musi być pierwszy)
    print("\n=== FAZA 1: SECURITY-OFFICER (boot check) ===")
    try:
        env_guard.boot_check()
    except SystemExit as e:
        print(f"[MAIN] Start zablokowany przez SECURITY-OFFICER (kod: {e.code})")
        sys.exit(e.code)

    # 1b. IMPORTER – opcjonalny import notatek przed pipeline
    if args.import_folder:
        import_folder = Path(args.import_folder)
        if import_folder.exists():
            print("\n=== FAZA 1b: IMPORTER ===")
            result = pipeline_guard.run("IMPORTER", importer.import_folder, import_folder)
            if result and result.get("imported", 0) > 0:
                brain_path = PROJECT_ROOT / "data" / "inbox"
            else:
                print("[MAIN] Import nie powiódł się lub brak plików. Używam domyślnego vault.")
        else:
            print(f"[MAIN] Folder do importu nie istnieje: {import_folder}")

    # 2. RÓWNOLEGŁE AGENTY: ASTRONOMER + STORYTELLER + LIBRARIAN
    print("\n=== FAZA 2-4: RÓWNOLEGŁE AGENTY (ASTRONOMER || STORYTELLER || LIBRARIAN) ===")
    results = {}
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(pipeline_guard.run, "ASTRONOMER", galaxy_mapper.refine_galaxy, brain_path): "galaxy_file",
            executor.submit(pipeline_guard.run, "STORYTELLER", metadata_engine.process_vault, brain_path): "meta_file",
            executor.submit(pipeline_guard.run, "LIBRARIAN", librarian.sync_galaxy_map): "lib_result",
        }
        for future in as_completed(futures):
            key = futures[future]
            try:
                results[key] = future.result()
            except Exception as e:
                print(f"[MAIN] Błąd w {key}: {e}")
                results[key] = None

    galaxy_file = results.get("galaxy_file")
    meta_file = results.get("meta_file")
    lib_result = results.get("lib_result")

    # LIBRARIAN – aktualizacja Project_Log (może być równolegle, ale po sync)
    if lib_result:
        pipeline_guard.run("LIBRARIAN", librarian.update_project_log)

    # 5. DEBUGGER – QA i walidacja (po zakończeniu wszystkich piszących)
    print("\n=== FAZA 5: DEBUGGER (QA & Validator) ===")
    qa_ok = pipeline_guard.run("DEBUGGER", debugger.full_qa_report)
    if qa_ok is not True:
        print("[MAIN] OSTRZEŻENIE: DEBUGGER zgłosił problemy. Sprawdź logi.")

    # 6. Podsumowanie
    print("\n=== PIPELINE ZAKOŃCZONY ===")
    if galaxy_file:
        print(f"  Galaxy data : {galaxy_file}")
    if meta_file:
        print(f"  Metadata    : {meta_file}")
    if lib_result:
        print(f"  Galaxy map  : {lib_result}")

    if args.push:
        print("\n=== FAZA 6: GIT-PUSHER ===")
        try:
            git_manager.validate_and_push()
        except Exception as e:
            print(f"[MAIN] Błąd podczas pushu: {e}")
            sys.exit(1)

    print("\n[MAIN] Nocna zmiana zakończona. Galaktyka gotowa.")


if __name__ == "__main__":
    main()
