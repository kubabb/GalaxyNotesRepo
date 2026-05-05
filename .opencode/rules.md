# OpenCode Rules – GalaxyNotesProject

## Zasada #1: Agenci to osobne jednostki pracy

**NIE wykonuję zadań agentów samodzielnie.** Każdy agent to osobny proces Python, który uruchamiam przez `main.py`. Moja rola to koordynacja, a nie wykonywanie ich pracy.

## Zasada #2: Zawsze równolegle

Uruchamiam wszystkich agentów jednocześnie przez `ThreadPoolExecutor` w `main.py`:

```python
with ThreadPoolExecutor(max_workers=3) as executor:
    futures = {
        executor.submit(pipeline_guard.run, "ASTRONOMER", galaxy_mapper.refine_galaxy, brain_path): "galaxy_file",
        executor.submit(pipeline_guard.run, "STORYTELLER", metadata_engine.process_vault, brain_path): "meta_file",
        executor.submit(pipeline_guard.run, "LIBRARIAN", librarian.sync_galaxy_map): "lib_result",
    }
```

Agenci nie gryzą się bo piszą do różnych plików:
- ASTRONOMER → `galaxy_data.json`
- STORYTELLER → `metadata.json`
- LIBRARIAN → `.galaxy_map/*.md`

## Zasada #3: Nie commituję ręcznie

**GIT-PUSHER to osobny agent** (`src/git_manager.py`). Uruchamiam go tylko przez:
```powershell
python main.py --push
```

NIE robię `git push` bezpośrednio. GIT-PUSHER robi dodatkowe sprawdzenia (debugger przed pushem).

## Zasada #4: Librarian zawsze prowadzi dokumentację

Po KAŻDEJ zmianie kodu uruchamiam `python main.py`, żeby LIBRARIAN zsynchronizował `.galaxy_map/` i zaktualizował `Project_Log.md`.

## Zasada #5: Watchman łapie błędy

Jeśli agent rzuci wyjątek, WATCHMAN (`src/pipeline_guard.py`) go łapie, loguje do `logs/watchman.log` i pipeline kontynuuje. Nie przerywam pracy innych agentów.

## Zasada #6: Security Officer pierwszy

Zawsze `env_guard.boot_check()` przed uruchomieniem jakiegokolwiek agenta. Nigdy nie pomijam.

## Podsumowanie workflow

1. **Zmieniam kod** (tactical.html, galaxy_mapper.py, etc.)
2. **Uruchamiam `python main.py`** – wszyscy agenci równolegle
3. **Sprawdzam `logs/watchman.log`** jeśli coś poszło nie tak
4. **Uruchamiam `python main.py --push`** – GIT-PUSHER wysyła na remote
5. **Librarian prowadzi dokumentację** automatycznie
