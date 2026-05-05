# OPERACJA „GALAXY-PILOT REDEPLOYMENT v4.0"

**Data:** 2026-05-05  
**Strateg:** HERMES (koordynacja agentów)  
**Cel:** Pełnowymiarowa galaktyka 3D + upload notatek non-markdown z AI-analizą i auto-powiązaniami.

---

## 1. DIAGNOZA AKTUALNEGO STANU

| Element | Stan | Problem |
|---------|------|---------|
| ASTRONOMER | Kod generuje Z (±4000), ale `plan.txt` v2.2 mówi o „płaskiej płaszczyźnie Z ±9". | Użytkownik potwierdza, że galaktyka **jest postrzegana jako płaska** — węzły nie tworzą wyraźnej struktury przestrzennej (bulge/disk/halo). |
| STORYTELLER | Skanuje tylko `*.md`. `API_ENABLED = False` (LOCAL MODE). | Brak obsługi plików **PDF, TXT, DOCX** itp. |
| Edges | Tylko WikiLinks z markdown. | Notatki non-md **nie mają żadnych powiązań** w galaktyce. |
| Frontend | Cockpit v3.0 ma 6DOF, ale brak UI do uploadu nowych plików. | Użytkownik nie może wgrać nowego sektora bez ręcznego kopiowania do vault. |

**Wniosek:** Potrzebny jest redeployment z nowym modelem galaktyki (3-komponentowy: **bulge + disk + halo**) oraz nowy agent **IMPORTER** obsługujący multi-format.

---

## 2. ARCHITEKTURA v4.0 — SCHEMAT ORKIESTRACJI

```
main.py v4.0
│
├─ FAZA 0: SECURITY-OFFICER (src/env_guard.py)
│     └─ Walidacja .env, .gitignore, nowe zależności (PyPDF2, python-docx)
│
├─ FAZA 1: IMPORTER (src/importer.py) — [opcjonalna, tylko gdy --import <folder>]
│     └─ Skan źródła → ekstrakcja tekstu z non-md → zapis tymczasowych .md w data/inbox/
│
├─ FAZA 2: PARALLEL EXECUTION (ThreadPoolExecutor, max 3)
│     ├─ ASTRONOMER v4.0  (src/galaxy_mapper.py)
│     │     └─ Budowa galaktyki 3D z bulge/disk/halo + edges z WikiLinks + suggested_links
│     ├─ STORYTELLER v4.0 (src/metadata_engine.py)
│     │     └─ Multi-format scan + AI analiza non-md → metadata.json
│     └─ LIBRARIAN v4.0   (src/librarian.py)
│           └─ Sync .galaxy_map/ (także mirrory non-md z YAML frontmatter)
│
├─ FAZA 3: DEBUGGER v4.0 (src/debugger.py)
│     └─ Z-Variance Test + Link Integrity + Upload Sanity
│
└─ FAZA 4: GIT-PUSHER (src/git_manager.py) — [tylko z flagą --push]
```

---

## 3. SZCZEGÓŁY AGENTÓW

### 3.1 IMPORTER — Nowy Agent (`src/importer.py`)

**Zadanie:** Przyjmie dowolny folder (flaga `--import <folder>`), skanuje pliki i przygotowuje je do analizy przez STORYTELLERA.

**Logika:**
1. Rekurencyjny skan rozszerzeń: `.md`, `.txt`, `.pdf`, `.docx`, `.odt`, `.rtf`, `.html`, `.py`, `.js`, `.json`.
2. Dla `.md`: kopiuje bez zmian do `data/inbox/` (struktura folderów zachowana).
3. Dla non-md:
   - **Ekstrakcja tekstu** (zależna od formatu):
     - `.txt/.py/.js/.json/.html` → `path.read_text(encoding="utf-8")`
     - `.pdf` → `PyPDF2.PdfReader` (iteracja po stronach, `extract_text()`)
     - `.docx` → `python-docx.Document` (iteracja po paragrafach)
     - `.odt/.rtf` → opcjonalnie (v4.1), na razie `warning + skip` lub `textract` jeśli dostępne
   - **Sanity check**: pliki > 50 MB są pomijane z logiem.
   - **Zapis tymczasowego `.md`** w `data/inbox/` o nazwie `<oryginał>.imported.md` z frontmatter:
     ```yaml
     ---
     original_file: "rel/path/to/file.pdf"
     format: "pdf"
     imported_at: "2026-05-05T12:00:00"
     extracted_chars: 4200
     ai_ready: true
     ---
     ```
   - Treść pliku: pełny wyciągnięty tekst (nie obcięty — STORYTELLER sam zrobi truncate przed API).
4. Zwraca do `main.py` słownik: `{"imported": N, "skipped": M, "inbox_path": "data/inbox/"}`.

**Wywołanie:**
```powershell
python main.py --import "C:/Users/kubar/Downloads/NoweNotatki"
```

**Agent odpowiedzialny za implementację:** IMPORTER (nowy skrypt, HERMES deleguje zadanie deweloperskie do ogólnego agenta kodującego zgodnie z `.opencode/coder.md`, ale ponieważ to backend Python, można potraktować jako rozszerzenie pipeline — wykona odpowiedni agent dev).

---

### 3.2 ASTRONOMER v4.0 — Model Galaktyki 3D (`src/galaxy_mapper.py`)

**Problem do rozwiązania:** Galaktyka jest płaska — węzły nie tworzą wyraźnej struktury 3D (brak wyróżnionego jądra, dysku i halo).

**Nowy model: 3-komponentowa galaktyka spiralna**

| Komponent | Typ węzłów | Geometria 3D |
|-----------|-----------|--------------|
| **BULGE** (jądro kuliste) | `degree >= 8` (super-hub) | Gęsta sfera o promieniu `R_bulge = 1200`. Rozkład `Normal(0, sigma=600)` na X, Y, Z. |
| **DISK** (dysk spiralny) | `degree > 0` (linked, ale < 8) | Logarytmiczna spirala z grubością: <br>`theta = base_angle + hash(seed)` <br>`r = a * exp(b * theta)` <br>`z = random.gauss(0, sigma_z(r))` gdzie `sigma_z(r) = 400 * exp(-r / 3000)` — cieńszy na zewnątrz. |
| **HALO** (halo) | `degree == 0` (orphans) | Sferyczny rozkład o promieniu `R_halo = 8000`, gęstość malejąca z `1/r^2` (metoda Marsaglia + weight). |

**Szczegóły implementacyjne:**
1. **Spiralne ramiona:** `arm_count = max(3, min(6, int(sqrt(n))))`. Węzłom przypisuje się ramiona na podstawie `hash(name) % arm_count` (zamiast Jaccard dla pozycji — Jaccard zostaje tylko do kolorów/grup).
2. **Pozycja w ramieniu:**
   - Kąt początkowy `theta_0 = (arm_index / arm_count) * 2π`
   - Kąt wzrostu `delta_theta = (degree + 1) * 0.4 + random.uniform(0, 0.5)`
   - Promień `r = 400 * exp(0.25 * delta_theta)`
   - `x = r * cos(theta_0 + delta_theta)`
   - `y = r * sin(theta_0 + delta_theta)`
   - `z = random.gauss(0, 400 * exp(-r / 3000))`
   - Szum pozycyjny: `±200` na X/Y, `±100` na Z.
3. **Bulge:** `x, y, z = random.gauss(0, 600)` dla każdej osi niezależnie.
4. **Halo:** `random_point_in_sphere(8000)` ale z wagą `1/r^2` (prawdopodobieństwo odwrotnie proporcjonalne do kwadratu odległości od centrum — więcej orphanów bliżej zewnętrznego brzegu).
5. **Edges:**
   - Czytamy `metadata.json` — dla każdego węzła bierzemy:
     - `links_out` z WikiLinks (dla `.md`)
     - `suggested_links` (dla wszystkich, w tym non-md)
   - Tworzymy krawędź `{"source": node, "target": target}` jeśli target istnieje w słowniku węzłów (bez względu na to, czy target ma fizyczny plik md czy jest virtualnym węzłem z non-md).
   - Jeśli `suggested_links` wskazuje na nieistniejący węzeł — **tworzymy go jako orphan w HALO** (stub node). Dzięki temu non-md pliki mogą tworzyć nowe gwiazdy w galaktyce.
6. **Kolory:**
   - Bulge: `#FFFFFF` (białe, jądro galaktyki)
   - Disk: kolory ramion spiralnych (cyjan, magenta, limonka, pomarańcz, fiolet)
   - Halo: `#444444` (szare, przygaszone)

**Output JSON:** ten sam format `galaxy_data.json` (pola `x, y, z, val, color, group`).

---

### 3.3 STORYTELLER v4.0 — Multi-format + AI Links (`src/metadata_engine.py`)

**Zmiany:**

1. **Rozszerzenie skanowania:**
   - Obecnie: `vault_path.rglob("*.md")`
   - Nowość: `vault_path.rglob("*")` ale z filtrem — pomijamy binary (sprawdzamy magic bytes lub rozszerzenia), pomijamy foldery specjalne (`.git`, `__pycache__`, `data/`, `.galaxy_map/`).
   - Obsługiwane rozszerzenia: `.md`, `.txt`, `.pdf`, `.docx`, `.html`, `.py`, `.js`, `.json`.
   - Pliki `.imported.md` (z IMPORTERA) traktujemy jako źródło tekstu — STORYTELLER czyta frontmatter, wie że `original_file` był non-md.

2. **Ekstrakcja tekstu dla non-md:**
   - Jeśli plik to `.imported.md` — tekst jest już w treści (po frontmatter).
   - Jeśli plik to `.md` natywny — obecna logika (czytanie + czyszczenie).
   - Dla non-md **bez** `.imported.md` (fallback): STORYTELLER sam próbuje ekstrahować (np. `.txt` read_text, `.html` via BeautifulSoup jeśli dostępne).

3. **AI Analiza dla non-md (i opcjonalnie dla md):**
   - **Prompt systemowy (sci-fi):**
     ```
     Jesteś systemem klasyfikacji gwiezdnej Galaktyki BRAIN.
     Otrzymasz tekst notatki. Zwróć wyłącznie JSON w formacie:
     {
       "brief": "maksymalnie 15 słów",
       "star_class": "jedno słowo opisujące naturę notatki",
       "energy_level": "liczba 1-10",
       "content": "skrót treści do 3000 znaków",
       "suggested_links": ["max 5 nazw powiązanych notatek lub tematów"]
     }
     suggested_links mogą być nazwami istniejących notatek lub nowymi tematami.
     ```
   - **Warunki wywołania API:**
     - Jeśli `API_ENABLED = True` **oraz** plik jest non-md (lub md bez WikiLinks) → wysyłamy do API.
     - Jeśli `API_ENABLED = False` → dla non-md używamy heurystyk lokalnych (pierwsze 15 słów jako brief, długość tekstu jako energy, nazwa pliku jako star_class), a `suggested_links` pozostaje puste.
   - **Dynamiczne przełączanie:** jeśli w batchu jest > 0 plików non-md i `API_ENABLED = False`, WATCHMAN loguje warning: „Non-md files require AI analysis but API is disabled. Links will be empty."

4. **Output metadata.json:**
   - Dla non-md klucz to stem oryginalnego pliku (np. `raport_kwartalny` dla `raport_kwartalny.pdf`).
   - Pole `source`: `"ai-upload"` (gdy API użyte) lub `"local-upload"` (gdy API wyłączone).
   - Pole `file`: ścieżka względna do oryginalnego pliku (np. `data/inbox/raport_kwartalny.pdf`).
   - Pole `suggested_links`: lista stringów (max 5). **To są virtualne WikiLinks** — ASTRONOMER użyje ich do edges.

---

### 3.4 LIBRARIAN v4.0 — Mirrory non-md (`src/librarian.py`)

**Zmiany:**
1. Podczas sync `.galaxy_map/`:
   - Dla natywnych `.md` — bez zmian.
   - Dla plików non-md (rozpoznawanych po `data/inbox/` lub rozszerzeniu) — tworzy mirror `<nazwa>.md` w `.galaxy_map/` z:
     ```yaml
     ---
     original_file: "rel/path/to/file.pdf"
     format: "pdf"
     extracted_chars: 4200
     star_class: "..."
     energy_level: "..."
     suggested_links: ["Note1", "Note2"]
     ---
     ```
   - Treść mirroru: wyciągnięty tekst (pierwsze 3000 znaków) lub link do oryginału.
2. `Project_Log.md` — dodaje wpis o liczbie zaimportowanych non-md plików.

---

### 3.5 CODER v4.0 — Frontend Upload (`pages/dashboard.html`, opcjonalnie `pages/tactical.html`)

**Nowy komponent: Panel „Upload Sector" w `pages/dashboard.html`**

**Wymagania UI/UX (zgodnie z `design/03_Standards/UI_UX_Standard.md`):**
1. **Drop Zone** (połowa szerokości ekranu, wysokość 200px, neonowa ramka `#00FFFF`, dashed):
   - Obsługa `dragover`, `dragleave`, `drop`.
   - Akceptuje pliki i foldery (`webkitdirectory`).
2. **Lista plików** (pod drop zone):
   - Checkbox per plik (domyślnie zaznaczone).
   - Kolumny: nazwa, format, rozmiar, status („Ready" / „Too large" / „Unsupported").
   - Filtr rozszerzeń: `.md`, `.txt`, `.pdf`, `.docx`, `.html`, `.py`, `.js`, `.json`.
3. **Przycisk „INITIATE IMPORT"** (magenta `#FF00FF`, glow):
   - Kliknięcie zapisuje zaakceptowane pliki do `data/inbox/` przez **fetch POST** do lokalnego serwera (wymaga backendu do zapisu) **LUB** wyświetla instrukcję CLI:
     ```
     Skopiuj pliki do folderu data/inbox/ i uruchom:
     python main.py --brain data/inbox
     ```
   - W v4.0 rekomendujemy **instrukcję CLI + localStorage** (bez konieczności backendu), aby nie komplikować architektury.
4. **Progress Bar:** jeśli użytkownik kopiuje pliki ręcznie, dashboard pokazuje „Scanning inbox..." po odświeżeniu ( sprawdza `fetch('../data/inbox/status.json')` ).

**Opcjonalne zmiany w `pages/tactical.html`:**
- Upewnić się, że kontrolki 6DOF prawidłowo pokazują głębokość Z (obecny kod już to robi, ale warto zweryfikować czy RMB + mouse yaw nie jest zablokowane na płaszczyźnie XY).
- Dodanie przycisku „GALAXY VIEW" (Space) resetującego kamerę do `(0, 0, 12000)` z `lookAt(0,0,0)` — umożliwia zobaczenie pełnej struktury 3D.

---

### 3.6 DEBUGGER v4.0 — Nowe testy (`src/debugger.py`)

**Nowe testy QA:**

1. **Z-Variance Test (3D Sanity):**
   ```python
   z_coords = [node["z"] for node in galaxy_data["nodes"].values()]
   z_std = statistics.stdev(z_coords)
   assert z_std > 200, f"Galaktyka zbyt płaska (std={z_std}). ASTRONOMER powinien generować pełne 3D."
   ```
   - Sprawdza czy węzły mają różne Z (czyli czy disk i halo działają).

2. **Link Integrity (Virtual Links):**
   ```python
   for node_id, meta in metadata.items():
       for link in meta.get("suggested_links", []):
           assert link in galaxy_data["nodes"] or link in metadata, \
               f"Virtual link {link} z {node_id} nie ma odpowiedniej gwiazdy."
   ```
   - Sprawdza czy `suggested_links` z non-md zostały przekształcone w edges/stub nodes.

3. **Upload Sanity:**
   - Sprawdza czy `data/inbox/` nie zawiera plików > 50 MB.
   - Sprawdza czy `.galaxy_map/` zawiera mirrory dla plików z `data/inbox/`.

4. **Dependency Check:**
   - Jeśli w `data/inbox/` są `.pdf` — sprawdza czy `PyPDF2` jest zainstalowane.
   - Jeśli `.docx` — sprawdza `python-docx`.

---

### 3.7 SECURITY-OFFICER v4.0 (`src/env_guard.py`)

**Dodatkowe walidacje:**
1. `.gitignore` musi zawierać:
   - `data/inbox/` (aby nie commitować zaimportowanych plików binarnych)
   - `__pycache__/` (już jest)
2. Jeśli w `config/.env` nie ma `OPENROUTER_API_KEY` a w `data/inbox/` są non-md pliki — **warning** (nie exit): „Non-md upload detected but API key missing. AI analysis disabled."

---

### 3.8 MAIN.PY Orchestrator v4.0

**Zmiany w argumentach:**
```python
parser.add_argument("--import", dest="import_folder", help="Folder to import non-md notes from")
```

**Nowa sekwencja:**
```python
env_guard.boot_check()           # FAZA 0

if args.import_folder:
    importer.run(args.import_folder)  # FAZA 1
    # Po imporcie, źródłem dla STORYTELLERA i ASTRONOMERA jest data/inbox/
    brain_path = PROJECT_ROOT / "data" / "inbox"
else:
    brain_path = Path(BRAIN_PATH)

# FAZA 2 — Parallel (jak obecnie)
with ThreadPoolExecutor(max_workers=3) as executor:
    ...
```

---

## 4. ZALEŻNOŚCI I INSTALACJA

**Nowe paczki (dodaj do `requirements.txt` lub `setup.ps1`):**
```text
PyPDF2>=3.0.0
python-docx>=0.8.11
beautifulsoup4>=4.12.0
```

**Uwaga:** Wszystkie paczki są opcjonalne — jeśli którejś brak, IMPORTER pomija dany format z warningiem (nie crashuje).

---

## 5. HARMONOGRAM WDRAŻANIA — CHECKPOINT COMMITS

**Zasada:** Po **każdej fazie** LIBRARIAN aktualizuje `Project_Log.md`, DEBUGGER waliduje, GIT-PUSHER wykonuje commit+push. Brak zielonego światła = stop.

| Krok | Agent | Zadanie | Wyjście | Checkpoint |
|------|-------|---------|---------|------------|
| 0 | HERMES | Finalizacja `plan_redeploy_v4.md` + `AGENTS.md` (poprawione role agentów) | Dokumentacja | — |
| 1 | SECURITY-OFFICER | Dodaj `data/inbox/`, `data/output/`, `logs/`, `__pycache__/` do `.gitignore`. Walidacja `.env` i zależności. | `.gitignore` v4 | — |
| 2 | LIBRARIAN | Zapisz ADR-001 (Redeployment v4.0) i aktualizację `Project_Log.md` z planem. | `.galaxy_map/` + vault | — |
| 3 | DEBUGGER | Sanity check repo (brak wycieków, poprawne `.gitignore`) | Raport | ✅ |
| 4 | GIT-PUSHER | **CHECKPOINT A:** Commit `docs: plan v4.0 + AGENTS roles` → push | Remote | ✅ |
| 5 | CODER | Zaktualizuj `pages/dashboard.html` — panel „Upload Sector" (drop zone, lista plików, instrukcja CLI). | Frontend | — |
| 6 | DEBUGGER | Walidacja `dashboard.html` (brak błędów JS, poprawne linki) | Raport | ✅ |
| 7 | GIT-PUSHER | **CHECKPOINT B:** Commit `feat(dashboard): upload sector panel` → push | Remote | ✅ |
| 8 | CODER / HERMES | Stwórz `src/importer.py` — szkielet + ekstraktory (txt/pdf/docx/html). | Nowy plik `.py` | — |
| 9 | DEBUGGER | `py_compile src/importer.py`, sprawdź brak wycieków | Raport | ✅ |
| 10 | GIT-PUSHER | **CHECKPOINT C:** Commit `feat(importer): multi-format note importer` → push | Remote | ✅ |
| 11 | CODER / HERMES | Zaktualizuj `src/metadata_engine.py` — multi-format scan + `suggested_links` (virtual WikiLinks). | Backend | — |
| 12 | LIBRARIAN | Dokumentacja zmiany w `Project_Log.md` + ADR-002 (Virtual Links). | Dokumentacja | — |
| 13 | DEBUGGER | `py_compile`, walidacja struktury `metadata.json` | Raport | ✅ |
| 14 | GIT-PUSHER | **CHECKPOINT D:** Commit `feat(metadata): multi-format + virtual links` → push | Remote | ✅ |
| 15 | CODER / HERMES | Zaktualizuj `src/galaxy_mapper.py` — model 3D bulge/disk/halo. | Backend | — |
| 16 | LIBRARIAN | Dokumentacja zmiany w `Project_Log.md` + ADR-003 (Galaxy 3D Model). | Dokumentacja | — |
| 17 | DEBUGGER | Uruchom `python main.py`, Z-Variance Test (`std(z) > 200`) | Raport QA | ✅ |
| 18 | GIT-PUSHER | **CHECKPOINT E:** Commit `feat(galaxy): bulge/disk/halo 3D model` → push | Remote | ✅ |
| 19 | CODER / HERMES | Zaktualizuj `src/debugger.py` — Z-Variance + Link Integrity + Upload Sanity. | Backend | — |
| 20 | DEBUGGER | Self-test: `py_compile`, sprawdź czy nowe testy nie psują starego flow | Raport | ✅ |
| 21 | GIT-PUSHER | **CHECKPOINT F:** Commit `feat(debugger): Z-Variance + Link Integrity tests` → push | Remote | ✅ |
| 22 | CODER / HERMES | Zaktualizuj `main.py` — flaga `--import`, nowa kolejność faz. | Orkiestrator | — |
| 23 | LIBRARIAN | Finalny wpis w `Project_Log.md` — podsumowanie redeploymentu v4.0. | Dokumentacja | — |
| 24 | DEBUGGER | Full QA: `python main.py` + wszystkie testy | Raport QA | ✅ |
| 25 | GIT-PUSHER | **CHECKPOINT G (FINAL):** Commit `chore(release): redeployment v4.0` → push | Remote | ✅ |

---

## 6. RYZYKA I OCHRONA

| Ryzyko | Wpływ | Ochrona |
|--------|-------|---------|
| **Rate limit API** (OpenRouter free tier ~50 req/day) | STORYTELLER nie przeanalizuje non-md | Progress JSON checkpoint (`data/output/progress.json`), batch size = 1, dynamiczny fallback do local mode. Użytkownik może włączyć `API_ENABLED = True` tylko dla sesji uploadu. |
| **Duże pliki PDF** (100+ stron) | Timeout, wysokie zużycie tokenów | Limit 50 MB w IMPORTERZE, truncate tekstu do 8000 znaków przed API. |
| **Brak zależności** (PyPDF2) | IMPORTER pomija PDF | Log warning, nie crash. Użytkownik może doinstalować paczkę. |
| **Niespójność Z** (frontend wyświetla płasko) | Użytkownik nadje widzi 2D | CODER weryfikuje czy Three.js używa `z` w pozycjach gwiazd (powinno być ok w v3.0). |
| **Circular suggested_links** | Nieskończone edges lub duże stub nodes | ASTRONOMER tworzy stub node tylko raz — deduplikacja w `nodes` dict. |

---

## 7. KRYTERIA SUKCESU

- [ ] `galaxy_data.json` ma `std(z) > 200` (DEBUGGER Z-Variance PASS).
- [ ] Notatka `.pdf` wgrana przez `--import` pojawia się jako gwiazda w `galaxy_data.json`.
- [ ] Notatka `.pdf` ma `suggested_links` w `metadata.json`.
- [ ] Krawędzie z `suggested_links` istnieją w `galaxy_data.json["edges"]`.
- [ ] `.galaxy_map/` zawiera mirror `.md` dla wgranego pliku `.pdf`.
- [ ] Panel uploadu widoczny w `pages/dashboard.html`.
- [ ] `python main.py --push` przechodzi bez błędów (DEBUGGER + GIT-PUSHER).

---

*Plan sporządzony przez HERMES. Realizacja wyłącznie przez agentów — nie ręcznie.*
