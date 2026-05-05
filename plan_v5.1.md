# PLAN v5.1 — Electron Desktop App

**Status:** W trakcie wdrażania  
**Cel:** Zero terminala — użytkownik klika .exe i aplikacja działa

---

## Postęp

- [x] Krok 1: Inicjalizacja npm w `electron/`
- [x] Krok 2: Instalacja Electron
- [x] Krok 3: `electron/main.js` — główny proces
- [x] Krok 4: `electron/preload.js` — IPC bridge
- [x] Krok 5: Przeniesienie frontendu do `renderer/`
- [x] Krok 6: `renderer/gp-helper.js` — auto-detekcja Electron vs Web
- [x] Krok 7: Zamiana fetch na GP.loadJSON w dashboard/tactical/log
- [x] Krok 8: Upload plików przez IPC (dashboard)
- [x] Krok 9: Test Electron start — PYTHON DZIAŁA
- [x] Krok 10: Upload via IPC
- [x] Krok 11: Build .exe via electron-builder (portable OK, NSIS wymaga uprawnień)
- [x] Krok 12: Menu aplikacji (File, View, Help)
- [ ] Krok 13: Tray icon
- [ ] Krok 14: Final QA + push  

---

## Architektura

```
electron/  ← NOWY FOLDER
├── package.json
├── main.js          # Główny proces Node.js
├── preload.js       # Bridge między main ↔ renderer
└── node_modules/

renderer/  ← PRZENIESIONE Z pages/
├── index.html
├── dashboard.html
├── tactical.html
├── log.html
└── settings.html

src/       # Python backend (bez zmian)
├── main.py
├── ml_engine.py
└── ...
```

## Checkpoint Commits

| # | Co | Hash |
|---|-----|------|
| 1 | Init npm + install Electron | — |
| 2 | main.js + preload.js | — |
| 3 | Renderer structure | — |
| 4 | Python subprocess | — |
| 5 | IPC upload | — |
| 6 | Build scripts | — |
