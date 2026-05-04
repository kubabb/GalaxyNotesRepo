---
title: "main.py – Koordynator Pipeline'u"
date: 2026-05-04T23:42:00
type: galaxy_map
source: GalaxyNotes
tags: #python #pipeline #koordynator
---

# main.py – Koordynator Nocnego Pipeline'u

## Opis
Główny entry point operacji „GALAXY-PILOT ENGINE". Koordynuje 5 faz:
1. SECURITY-OFFICER (boot check)
2. ASTRONOMER (galaxy_data.json)
3. STORYTELLER (metadata.json)
4. Podsumowanie
5. GIT-PUSHER (opcjonalny push)

## Powiązania
- [[src/env_guard]] – walidacja bezpieczeństwa
- [[src/pipeline_guard]] – łapanie wyjątków
- [[src/galaxy_mapper]] – astrometria
- [[src/metadata_engine]] – metadane Sci-Fi
- [[src/git_manager]] – deployment

## Sensor Scan
- **Star_Class**: Projekt aktywny
- **Energy_Level**: Wysoka (entry point, krytyczny)
- **Brief**: Główny koordynator nocnego pipeline'u agentów.
