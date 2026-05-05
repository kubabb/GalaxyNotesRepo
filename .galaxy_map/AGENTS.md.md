---
title: "AGENTS"
date: 2026-05-05T11:53:26
type: SourceFile
source: GalaxyNotes
tags: #markdown #docs #design
---

## Analiza: `AGENTS.md`

Dokumentacja projektu GalaxyNotesProject.

- **Rozszerzenie:** .md
- **Lokalizacja:** `AGENTS.md`
- **Liczba linii:** ~55

### Powiązane


### Fragment
```
# AGENTS.md – GalaxyNotesProject

Compact cheat-sheet for OpenCode. Polish-language Python project that turns an Obsidian vault into an interactive 3D galaxy (Three.js cockpit).

## Entrypoints & Boundaries

- **Main orchestrator:** `main.py` — adds `src/` to `sys.path`, then runs `env_guard` → `galaxy_mapper` → `metadata_engine` → `librarian` → `debugger` → optional `git_manager.push`.
- **Landing page (product):** `index.html` in repo root — cyberpunk marketing page, first entry point for web ...
```

---
*Wygenerowane przez Librarian* | [[01_Projects/GalaxyNotes/PLAN|PLAN]] | [[01_Projects/GalaxyNotes/Project_Log|Project Log]]
