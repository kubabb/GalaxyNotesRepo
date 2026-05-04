---
title: "pipeline_guard.py – WATCHMAN"
date: 2026-05-04T23:42:00
type: galaxy_map
source: GalaxyNotes
tags: #python #supervisor #logging
---

# pipeline_guard.py – WATCHMAN

## Opis
Strażnik procesu. Monitoruje pipeline, loguje błędy do `00_Runtime/Galaxy_Build.log`.
Łapie wyjątki, wznawia pracę, pomija uszkodzone pliki.

## Powiązania
- [[main.py]] – wywołuje run() dla każdej fazy
- [[00_Runtime/Galaxy_Build.log]] – plik logów
- [[.opencode/watchman.md]] – definicja agenta AI

## Sensor Scan
- **Star_Class**: Projekt aktywny
- **Energy_Level**: Średnia (nadzór, nie obliczenia)
- **Brief**: Monitoruje zdrowie pipeline'u i loguje błędy.
