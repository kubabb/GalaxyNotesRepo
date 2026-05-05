---
title: "git_manager"
date: 2026-05-05T11:02:21
type: SourceFile
source: GalaxyNotes
tags: #python #backend #agent
---

## Analiza: `src/git_manager.py`

Moduł Python zawierający 4 funkcji. Główne: _run_git, _get_remote_url, ensure_git_repo.

- **Rozszerzenie:** .py
- **Lokalizacja:** `src/git_manager.py`
- **Liczba linii:** ~100

### Powiązane
[[os]] [[sys]] [[subprocess]] [[logging]] [[pathlib]] [[dotenv]] [[env_guard]] [[debugger]]

### Fragment
```
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
logger ...
```

---
*Wygenerowane przez Librarian* | [[01_Projects/GalaxyNotes/PLAN|PLAN]] | [[01_Projects/GalaxyNotes/Project_Log|Project Log]]
