---
title: "librarian"
date: 2026-05-05T11:02:21
type: SourceFile
source: GalaxyNotes
tags: #python #backend #agent
---

## Analiza: `src/librarian.py`

Moduł Python zawierający 3 funkcji. Główne: should_skip, extract_imports, generate_mirror_md.

- **Rozszerzenie:** .py
- **Lokalizacja:** `src/librarian.py`
- **Liczba linii:** ~84

### Powiązane
[[os]] [[re]] [[datetime]] [[pathlib]]

### Fragment
```
"""
LIBRARIAN v2.0 (Knowledge Keeper)
Agent Bibliotekarz. Zarządza strukturą lustrzaną `.galaxy_map/`.
Dla każdego pliku projektu tworzy odpowiednik `.md` z analizą kontekstową i linkami.
"""
import os
import re
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GALAXY_MAP_DIR = PROJECT_ROOT / ".galaxy_map"

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".galaxy_map", "data", ".opencode"}
SKIP_EXTS = {".pyc", ".log", ".env", ".png"...
```

---
*Wygenerowane przez Librarian* | [[01_Projects/GalaxyNotes/PLAN|PLAN]] | [[01_Projects/GalaxyNotes/Project_Log|Project Log]]
