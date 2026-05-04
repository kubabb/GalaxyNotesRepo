---
title: "metadata_engine.py – STORYTELLER"
date: 2026-05-04T23:42:00
type: galaxy_map
source: GalaxyNotes
tags: #python #metadata #ai #semantic
---

# metadata_engine.py – STORYTELLER

## Opis
Analityk semantyczny. Generuje metadane Sci-Fi (Star_Class, Energy_Level, Brief) dla każdego pliku.
Wykorzystuje LLM (OpenRouter, Gemma 4) do analizy kontekstowej i sugerowania nowych linków.

## Powiązania
- [[config/.env]] – klucz API OpenRouter
- [[data/output/metadata.json]] – wyjściowy plik metadanych
- [[.opencode/storyteller.md]] – definicja agenta AI
- [[.galaxy_map/]] – wstrzykuje [[WikiLink]] do plików lustrzanych

## Sensor Scan
- **Star_Class**: Projekt aktywny
- **Energy_Level**: Wysoka (wywołania API LLM)
- **Brief**: Generuje metadane Sci-Fi i linki semantyczne.
