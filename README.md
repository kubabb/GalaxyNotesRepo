<div align="center">

<img src="design/screen.png" width="120" height="120" style="border-radius: 50%; border: 2px solid #00f3ff; box-shadow: 0 0 30px rgba(0,243,255,0.4);">

# `▛ GALAXY-PILOT ▜`

### `◄ Twój Obsidian jako interaktywna galaktyka 3D ►`

[![Version](https://img.shields.io/badge/VERSION-5.1.0-00f3ff?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0iIzAwZjNmZiIgZD0iTTEyIDJDNi40OCAyIDIgNi40OCAyIDEyczQuNDggMTAgMTAgMTAgMTAtNC40OCAxMC0xMFMyMC40OCAxMiAxMiAyem0tMSAxN2MtMi43NiAwLTUtMi4yNC01LTVzMi4yNC01IDUtNSA1IDIuMjQgNSA1LTIuMjQgNS01IDV6Ii8+PC9zdmc+)](https://github.com/kubabb/GalaxyNotesRepo)
[![Python](https://img.shields.io/badge/PYTHON-3.12+-36fd0f?style=for-the-badge&logo=python&logoColor=black)](https://python.org)
[![Electron](https://img.shields.io/badge/ELECTRON-33+-fe00fe?style=for-the-badge&logo=electron&logoColor=white)](https://electronjs.org)
[![Three.js](https://img.shields.io/badge/THREE.JS-WebGL-00f3ff?style=for-the-badge&logo=three.js&logoColor=white)](https://threejs.org)
[![License](https://img.shields.io/badge/LICENSE-MIT-ffabf3?style=for-the-badge)](LICENSE)

<br>

```
╔══════════════════════════════════════════════════════════════════╗
║  SYSTEM STATUS: ONLINE      │  ENGINE: 6DOF      │  ML: LOCAL   ║
║  NODES: 61                  │  EDGES: 91         │  DEPTH: 3D   ║
╚══════════════════════════════════════════════════════════════════╝
```

</div>

---

## `⚡ ARCHITEKTURA SYSTEMU`

```
┌─────────────────────────────────────────────────────────────────────┐
│                        GALAXY-PILOT v5.1                             │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   VAULT      │  │   PYTHON     │  │   ELECTRON   │              │
│  │   OBSIDIAN   │──│   PIPELINE   │──│   DESKTOP    │              │
│  │   (.md)      │  │   (ML/3D)    │  │   APP        │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│         │                 │                   │                    │
│         ▼                 ▼                   ▼                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │              TACTICAL OS — MULTI-PAGE APP                    │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │  │
│  │  │DASHBOARD │ │ TACTICAL │ │   LOG    │ │ SETTINGS │       │  │
│  │  │  PANEL   │ │  6DOF    │ │ TERMINAL │ │  SYSTEM  │       │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │  │
│  └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## `🚀 DEployMENT MODES`

<div align="center">

| `🌐 PRZEGLĄDARKA` | `🖥️ DESKTOP (Electron)` |
|:---|:---|
| Zero instalacji | Aplikacja natywna |
| `python -m http.server 8080` | `npm run start` |
| Działa w każdej przeglądarce | Tray icon, skróty klawiszowe |
| Wymaga serwer HTTP | Python bundlowany wewnątrz |
| [▶ URUCHOM TERAZ](http://localhost:8080/pages/tactical.html) | [⬇ POBIERZ .EXE](https://github.com/kubabb/GalaxyNotesRepo/releases) |

</div>

---

## `🎮 TACTICAL COCKPIT — 6DOF FLIGHT ENGINE`

> *"Nie oglądasz galaktyki z zewnątrz. Jesteś w środku."*

```
┌────────────────────────────────────────────────────────────┐
│  KONTROLA STATKU KOSMICZNEGO                               │
├────────────────────────────────────────────────────────────┤
│  W / S        →  Ciąg silników (przód / tył)               │
│  A / D        →  Strafe lewo / prawo                       │
│  R / F        →  Strafe góra / dół                         │
│  Q / E        →  Roll (beczka)                             │
│  RMB + mysz   →  Pitch / Yaw (lot myszą)                   │
│  Shift        →  WARP SPEED                                │
│  LMB (cel)    →  Auto-pilot do gwiazdy                     │
│  C / ESC      →  Zamknij HUD / anuluj nawigację            │
└────────────────────────────────────────────────────────────┘
```

**Kamera chase-cam:** Sztywno przyczepiona do modelu statku — obraca się razem z myszką. LPM wybiera cel, RMB kontroluje orbitę.

---

## `🧠 SILNIK ML — 100% OFFLINE`

```python
# Bez API. Bez rate-limitów. Bez kluczy.
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity

# TF-IDF + K-Means automatycznie grupuje notatki w konstelacje
# Cosine similarity generuje hiperprzestrzenne krawędzie między gwiazdami
```

- ✅ **TF-IDF** — ekstrakcja cech tekstowych
- ✅ **K-Means** — klasteryzacja w spiralne ramiona galaktyki  
- ✅ **Cosine Similarity** — wykrywanie powiązań między notatkami
- ✅ **Lokalne przetwarzanie** — zero zewnętrznych zależności API

---

## `📊 STATYSTYKI GALAKTYKI`

<div align="center">

| Metryka | Wartość | Status |
|:---|---:|:---|
| `Węzły (gwiazdy)` | **61** | 🟢 Active |
| `Krawędzie (powiązania)` | **91** | 🟢 Active |
| `Ramiona spiralne` | **7** | 🟢 Active |
| `Z-Variance (głębokość 3D)` | **1745.67** | 🟢 Excellent |
| `Wirtualne linki` | 60 | 🟡 Orphans |

</div>

---

## `⚙️ QUICK START`

### Instalacja

```bash
# 1. Klonuj repo
git clone https://github.com/kubabb/GalaxyNotesRepo.git
cd GalaxyNotesRepo

# 2. Pierwsze uruchomienie (instalacja zależności)
.\setup.ps1

# 3. Konfiguracja
# Edytuj config/.env:
#   OPENROUTER_API_KEY=opcjonalne
#   TARGET_PATH=sciezka/do/output
#   BRAIN_PATH=sciezka/do/vault
```

### Tryb Web

```bash
# Generuj dane galaktyki
python main.py

# Uruchom serwer
python -m http.server 8080

# Otwórz w przeglądarce
# http://localhost:8080/                 → Landing Page
# http://localhost:8080/pages/tactical.html → 3D Cockpit
```

### Tryb Desktop (Electron)

```bash
cd electron
npm install
npm run start        # Dev mode
npm run build:win    # Build .exe
npm run build:mac    # Build .dmg
npm run build:linux  # Build AppImage
```

---

## `🗂️ STRUKTURA PROJEKTU`

```
GalaxyNotesProject/
├── 📁 src/                     # Agenci Python (pipeline)
│   ├── main.py                 # Orkiestrator
│   ├── galaxy_mapper.py        # ASTRONOMER — generuje galaktykę 3D
│   ├── metadata_engine.py      # STORYTELLER — ML + metadane
│   ├── ml_engine.py            # LOCAL ML — TF-IDF + K-Means
│   ├── librarian.py            # LIBRARIAN — synchronizacja .galaxy_map/
│   ├── debugger.py             # DEBUGGER — QA i walidacja
│   └── env_guard.py            # SECURITY-OFFICER — weryfikacja .env
│
├── 📁 pages/                   # Web App (przeglądarka)
│   ├── index.html              # Landing page
│   ├── dashboard.html          # Mission Control
│   ├── tactical.html           # 3D Cockpit (6DOF)
│   ├── log.html                # Terminal / Dziennik
│   └── settings.html           # System Settings
│
├── 📁 renderer/                # Electron App (desktop mirror)
│   ├── index.html              # Landing (wspólny)
│   ├── dashboard.html          # Panel (IPC)
│   ├── tactical.html           # Cockpit (IPC)
│   ├── gp-helper.js            # Auto-detect Electron vs Web
│   └── ...
│
├── 📁 electron/                # Desktop Shell
│   ├── main.js                 # Główny proces (menu, tray, Python)
│   ├── preload.js              # IPC Bridge
│   └── package.json            # Build config (win/mac/linux)
│
├── 📁 data/output/             # Generowane artefakty
│   ├── galaxy_data.json        # Graf 3D (nodes, edges, meta)
│   └── metadata.json           # Metadane gwiazd
│
├── 📁 .galaxy_map/             # Mirror dokumentacji (librarian)
├── 📁 design/                  # UI/UX Standards & assets
├── 📁 .opencode/               # Persony agentów AI
└── index.html                  # 🌐 Główny landing page (Web/Desktop choice)
```

---

## `🎨 DESIGN SYSTEM`

```css
/* Tactical OS Color Palette */
--bg:              #000000;    /* Czarna dziura */
--surface:         #131313;    /* Panel główny */
--primary:         #00f3ff;    /* Cyber-cyan (HUD) */
--secondary:       #fe00fe;    /* Magenta (akcenty) */
--tertiary:        #36fd0f;    /* Zielony (status OK) */
--error:           #ffb4ab;    /* Czerwony (alert) */
--outline:         #849495;    /* Szary (tekst drugorzędny) */
```

**Typografia:** Space Grotesk (nagłówki) + JetBrains Mono (dane taktyczne) + Inter (body)

---

## `🔄 PIPELINE — JAK TO DZIAŁA`

```
┌──────────────────────────────────────────────────────────────────┐
│  FAZA 1: SECURITY-OFFICER                                        │
│  └─▶ Walidacja .env, .gitignore, kluczy API                     │
├──────────────────────────────────────────────────────────────────┤
│  FAZA 2-4: RÓWNOLEGŁE (max 3 wątki)                              │
│  ├─▶ ASTRONOMER    → galaxy_data.json  (3D graf)                │
│  ├─▶ STORYTELLER   → metadata.json     (ML + metadane)          │
│  └─▶ LIBRARIAN     → .galaxy_map/      (dokumentacja)           │
├──────────────────────────────────────────────────────────────────┤
│  FAZA 5: DEBUGGER                                                │
│  └─▶ Skan wycieków API + walidacja JSON + kompilacja Python     │
├──────────────────────────────────────────────────────────────────┤
│  FAZA 6: GIT-PUSHER (opcjonalnie --push)                         │
│  └─▶ Automatyczny push do GitHub z sanity-check                 │
└──────────────────────────────────────────────────────────────────┘
```

---

## `🖼️ SCREENSHOTS`

<div align="center">

| `Dashboard` | `3D Cockpit` | `Terminal` |
|:---:|:---:|:---:|
| *Mission Control* | *6DOF Flight* | *Flight Log* |
| ![Dashboard](design/screen.png) | ![Cockpit](design/screen.png) | ![Log](design/screen.png) |

</div>

---

## `🛡️ BEZPIECZEŃSTWO`

- 🔒 **API Key Leak Scanner** — skanuje ostatnie 32 znaki klucza we wszystkich plikach źródłowych
- 🔒 **Env Guard** — proces startuje tylko gdy `.env` i `.gitignore` są poprawne
- 🔒 **Gitignore Validator** — wymaga wzorców na `.env`, `node_modules/`, `dist*/`
- 🔒 **No Secrets in Git** — wszystkie klucze w `config/.env` (poza repo)

---

## `📦 WYMAGANIA`

| Komponent | Wersja | Uwagi |
|:---|:---|:---|
| Python | `>= 3.10` | Wymagany scikit-learn, numpy |
| Node.js | `>= 18` | Dla Electron build |
| npm | `>= 9` | Dla zależności Electron |
| Chrome/FF/Edge | Latest | Dla trybu web |

---

## `🤝 KONTRYBUCJA`

```bash
# 1. Fork
# 2. Branch:  feat/nazwa-ficzera
# 3. Commit zgodnie z konwencją:
#    feat: nowa funkcja
#    fix: naprawa błędu
#    docs: dokumentacja
#    refactor: zmiana struktury
# 4. DEBUGGER musi przejść: python src/debugger.py
# 5. Pull Request
```

---

## `📜 LICENCJA`

```
MIT License — Galaxy-Pilot Team
Wolno używać, modyfikować i rozpowszechniać.
Autor nie odpowiada za utratę danych w czasie skoku warp.
```

---

<div align="center">

## `◄ GALAKTYKA CZEKA ►`

```
     ✦           ✦              ✦
         ✦                  ✦
    ✦         ✦      ✦           ✦
        ✦                       ✦
             ✦   [ YOU ARE HERE ]
    ✦                              ✦
         ✦         ✦        ✦
              ✦           ✦
```

**[⬆ WRÓĆ NA GÓRĘ](#-galaxy-pilot-)**

`System v5.1.0 │ Status: OPERATIONAL │ Z-Depth: ACTIVE`

</div>
