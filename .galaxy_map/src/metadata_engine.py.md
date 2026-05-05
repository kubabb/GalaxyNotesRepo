---
title: "metadata_engine"
date: 2026-05-05T11:02:21
type: SourceFile
source: GalaxyNotes
tags: #python #backend #agent
---

## Analiza: `src/metadata_engine.py`

Moduł Python zawierający 4 funkcji. Główne: clean_markdown, extract_first_sentence, star_class_from_name.

- **Rozszerzenie:** .py
- **Lokalizacja:** `src/metadata_engine.py`
- **Liczba linii:** ~96

### Powiązane
[[os]] [[re]] [[json]] [[time]] [[concurrent]] [[pathlib]] [[dotenv]] [[requests]]

### Fragment
```
"""
STORYTELLER (Metadata Agent) – EVOLUTION v2.0
Deep Scan AI z retry logic, batch processing i fallbackiem lokalnym.
Wykorzystuje OpenRouter API (Google Gemma 4) z backoff.
"""
import os
import re
import json
import time
import concurrent.futures
from pathlib import Path
from dotenv import load_dotenv

try:
    import requests
except ImportError:
    requests = None

# Ładuj .env z config/
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
ENV_PATH = PROJECT_ROOT / "...
```

---
*Wygenerowane przez Librarian* | [[01_Projects/GalaxyNotes/PLAN|PLAN]] | [[01_Projects/GalaxyNotes/Project_Log|Project Log]]
