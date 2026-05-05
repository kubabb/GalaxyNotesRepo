# PLAN v5.1 — Electron Desktop App

**Status:** W trakcie wdrażania  
**Cel:** Zero terminala — użytkownik klika .exe i aplikacja działa

---

## Postęp

- [x] Krok 1: Inicjalizacja npm w `electron/` 
- [ ] Krok 2: Instalacja Electron  
- [ ] Krok 3: `electron/main.js` — główny proces  
- [ ] Krok 4: `electron/preload.js` — IPC bridge  
- [ ] Krok 5: Przeniesienie frontendu do `renderer/`  
- [ ] Krok 6: Python subprocess auto-start  
- [ ] Krok 7: IPC — upload plików  
- [ ] Krok 8: Build i package  

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
