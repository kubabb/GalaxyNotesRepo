---
title: "setup"
date: 2026-05-05T11:02:21
type: SourceFile
source: GalaxyNotes
tags: #powershell #setup
---

## Analiza: `setup.ps1`

Plik źródłowy `setup.ps1` w projekcie GalaxyNotesProject.

- **Rozszerzenie:** .ps1
- **Lokalizacja:** `setup.ps1`
- **Liczba linii:** ~95

### Powiązane


### Fragment
```
# GalaxyNotesProject – Setup v2.0 (Windows PowerShell)
# SECURITY-OFFICER + LIBRARIAN: Interaktywny setup z drag&drop i dynamicznym TARGET_PATH

Write-Host "=== GALAXY-PILOT EVOLUTION v2.0: FAZA INICJACJI ===" -ForegroundColor Cyan
Write-Host ""

# Sprawdź czy config istnieje
if (-not (Test-Path "config")) {
    New-Item -ItemType Directory -Path "config" | Out-Null
    Write-Host "[LIBRARIAN] Utworzono folder config/" -ForegroundColor Green
}

# Wczytaj istniejący .env jeśli jest
$envPath = "co...
```

---
*Wygenerowane przez Librarian* | [[01_Projects/GalaxyNotes/PLAN|PLAN]] | [[01_Projects/GalaxyNotes/Project_Log|Project Log]]
