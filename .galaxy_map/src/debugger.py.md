---
title: "debugger"
date: 2026-05-05T11:02:21
type: SourceFile
source: GalaxyNotes
tags: #python #backend #agent
---

## Analiza: `src/debugger.py`

Moduł Python zawierający 3 funkcji. Główne: scan_for_leaks, validate_json, validate_all_python.

- **Rozszerzenie:** .py
- **Lokalizacja:** `src/debugger.py`
- **Liczba linii:** ~95

### Powiązane
[[os]] [[re]] [[sys]] [[json]] [[py_compile]] [[pathlib]]

### Fragment
```
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
    Z...
```

---
*Wygenerowane przez Librarian* | [[01_Projects/GalaxyNotes/PLAN|PLAN]] | [[01_Projects/GalaxyNotes/Project_Log|Project Log]]
