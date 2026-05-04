---
title: "env_guard.py – SECURITY-OFFICER"
date: 2026-05-04T23:42:00
type: galaxy_map
source: GalaxyNotes
tags: #python #security #env
---

# env_guard.py – SECURITY-OFFICER

## Opis
Strażnik bezpieczeństwa. Waliduje `config/.env`, klucze API (OpenRouter) oraz `.gitignore`.
Blokuje start i push jeśli konfiguracja jest niepełna.

## Powiązania
- [[config/.env]] – plik z kluczami (chroniony przez .gitignore)
- [[main.py]] – wywołuje boot_check() przy starcie
- [[src/git_manager]] – wywołuje validate_before_push()

## Sensor Scan
- **Star_Class**: Projekt aktywny
- **Energy_Level**: Krytyczna (blokuje pipeline)
- **Brief**: Walidator bezpieczeństwa środowiska.
