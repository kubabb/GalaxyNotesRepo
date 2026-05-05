---
title: "galaxy_mapper"
date: 2026-05-05T12:18:40
type: SourceFile
source: GalaxyNotes
tags: #python #backend #agent
---

## Analiza: `src/galaxy_mapper.py`

Moduł Python zawierający 5 funkcji. Główne: load_env, get_vault_path, should_skip.

- **Rozszerzenie:** .py
- **Lokalizacja:** `src/galaxy_mapper.py`
- **Liczba linii:** ~100

### Powiązane
[[os]] [[re]] [[json]] [[math]] [[random]] [[argparse]] [[pathlib]] [[collections]]

### Fragment
```
"""
ASTRONOMER v2.0 (Semantic Physics Refiner)
Matematyk galaktyki z fizyką semantyczną.
- Czyta pliki .md z vaultu.
- Ekstrahuje [[WikiLinks]].
- Grupuje węzły w ramiona spiralne na podstawie podobieństwa linków.
- Przypisuje współrzędne 3D: ważniejsze notatki bliżej centrum.
- Zapisuje galaxy_data.json w formacie v2.0.
"""
import os
import re
import json
import math
import random
import argparse
from pathlib import Path
from collections import defaultdict

# Ścieżki projektu
PROJECT_ROOT = Pat...
```

---
*Wygenerowane przez Librarian* | [[01_Projects/GalaxyNotes/PLAN|PLAN]] | [[01_Projects/GalaxyNotes/Project_Log|Project Log]]
