# CODE REVIEW — Galaxy-Pilot v5.1.0
> Analiza wykonana: 2026-05-15  
> Zakres: cały projekt (Python backend + Electron shell + frontend MPA)

---

## 🔴 KRYTYCZNE — Wymagają natychmiastowej poprawy

---

### 1. Hardcoded ścieżka do vaultu użytkownika (`C:\Users\kubar\...`)

**Pliki:** `main.py`, `src/galaxy_mapper.py`, `src/metadata_engine.py`, `electron/main.js`

Domyślna ścieżka `C:\Users\kubar\OneDrive\Dokumenty\BRAIN` jest zakodowana na twardo w co najmniej 4 miejscach. Każda inna osoba uruchamiająca projekt dostanie błąd `FileNotFoundError` bez żadnego przyjaznego komunikatu.

**Propozycja naprawy:**
```python
# Zamiast hardcoded path — sprawdź kolejno:
# 1. Argument CLI --brain
# 2. BRAIN_PATH z config/.env
# 3. Wypisz JASNY komunikat o konieczności konfiguracji i wyjdź
DEFAULT_BRAIN_PATH = None  # brak domyślnej = wymuś jawną konfigurację

if not brain_path or not brain_path.exists():
    print("[MAIN] BŁĄD: Podaj ścieżkę do vaultu przez --brain lub BRAIN_PATH w config/.env")
    sys.exit(1)
```

---

### 2. `src/pipeline_guard.py` (WATCHMAN) — pochłania wszystkie wyjątki

**Plik:** `src/pipeline_guard.py`

Funkcja `run()` łapie **każdy** `Exception` i zwraca `None` bez reraise. Oznacza to, że błąd konfiguracji (np. zły vault path, brak uprawnień) jest cicho logowany, a pipeline kontynuuje i produkuje puste/błędne pliki JSON.

**Propozycja:**
- Dodaj kategorię błędów krytycznych, które zatrzymują pipeline.
- Albo zwracaj obiekt `Result` z `ok: bool` zamiast `None`/wartość, żeby wywołujący mógł sprawdzić status.

```python
FATAL_EXCEPTIONS = (FileNotFoundError, PermissionError, OSError)

def run(agent_name, task_func, *args, **kwargs):
    try:
        result = task_func(*args, **kwargs)
        return result
    except FATAL_EXCEPTIONS as e:
        log_error(agent_name, e)
        raise  # Przerywa pipeline przy błędach FS
    except Exception as e:
        log_error(agent_name, e)
        return None
```

---

### 3. `electron/main.js` — `readJSON` przez `fs.readFileSync` w `preload.js`

**Plik:** `electron/preload.js`

```js
readJSON: (relativePath) => {
    const fullPath = path.join(__dirname, '..', relativePath);
    const data = fs.readFileSync(fullPath, 'utf-8');  // synchroniczny I/O w preload!
    return JSON.parse(data);
}
```

`fs.readFileSync` w preload blokuje główny wątek renderera. Przy dużych plikach JSON (duży vault) UI się zamrozi.

**Propozycja:**
```js
// preload.js — użyj IPC handler zamiast bezpośredniego fs
readJSON: (relativePath) => ipcRenderer.invoke('read-json', relativePath),

// main.js — dodaj handler:
ipcMain.handle('read-json', async (event, relativePath) => {
    const fullPath = path.join(PROJECT_ROOT, relativePath);
    const data = await fs.promises.readFile(fullPath, 'utf-8');
    return JSON.parse(data);
});
```

---

### 4. `electron/main.js` — hardcoded domyślny vault użytkownika

**Plik:** `electron/main.js`, linia ~19:
```js
const defaultVault = 'C:/Users/kubar/OneDrive/Dokumenty/BRAIN';
```

Ten sam problem co w punkcie 1 — specyficzny dla autora, crashuje u innych użytkowników. Przy pierwszym uruchomieniu Electron powinien pokazać okno dialogowe `dialog.showOpenDialog` z prośbą o wybór folderu vaultu i zapisać wybór.

---

## 🟠 WAŻNE — Znaczące problemy jakościowe

---

### 5. Brak `package.json` w repozytorium

**Plik:** `electron/` (brak `package.json`)

`package.json` jest prawdopodobnie w `.gitignore` lub nie został dodany do repo. Bez niego klonujący projekt nie może uruchomić `npm install` ani `npm run start`. Plan v5.1 wymienia Electron jako kluczowy komponent.

**Propozycja:** Dodaj `electron/package.json` do repozytorium (upewnij się, że nie zawiera sekretów).

---

### 6. Duplikacja kodu między `pages/` a `renderer/`

**Pliki:** `pages/*.html` vs `renderer/*.html`

Projekt zawiera dwa zestawy tych samych stron HTML:
- `pages/` — wersja webowa (używa `fetch`)
- `renderer/` — wersja Electron (używa IPC)

Jest to fatalny wzorzec: każda zmiana UI musi być aplikowana ręcznie w OBU miejscach. Wystarczy 2 tygodnie, żeby się rozjechały.

**Propozycja:**
- Użyj jednego zestawu stron + `renderer/gp-helper.js` jako abstrakcji. Już *istnieje* `gp-helper.js` — ale nie jest w pełni używany w `pages/`.
- Albo usuń `pages/` i używaj tylko `renderer/` z `GP.loadJSON()`.

---

### 7. `src/metadata_engine.py` — zmienna `all_files` jest nadpisywana w batch ML

**Plik:** `src/metadata_engine.py`, funkcja `process_vault()`

```python
all_files = []
for f in vault_path.rglob("*"):
    ...
    all_files.append(f)

# ... later in batch ML:
all_files = []  # ← NADPISUJE oryginalną listę!
for f in pending:
    ...
    all_files.append(f.stem)
```

Oryginalna lista `all_files` (Path objects) jest zastąpiona listą stringów (`stem`). Potem `pending = [f for f in all_files if f.stem not in processed]` wywołuje `.stem` na stringach → `AttributeError`.

**Propozycja:** Zmień nazwę zmiennej w batch ML na `all_stems` lub `ml_filenames`.

---

### 8. `src/galaxy_mapper.py` — `arm_count` jest nadpisywane lokalnie

**Plik:** `src/galaxy_mapper.py`, funkcja `assign_coordinates()`

```python
def assign_coordinates(nodes, groups, arm_count):
    ...
    # Inside the loop for DISK:
    arm_count = max(3, min(6, int(math.sqrt(n))))  # ← nadpisuje parametr!
    arm_index = hash(name) % arm_count
```

Parametr `arm_count` przekazany z zewnątrz jest ignorowany. Mogą być niespójności między `groups` (obliczonymi z zewnętrznym `arm_count`) a `arm_index` (obliczonym z nowym `arm_count`).

**Propozycja:** Usuń nadpisanie lub zmień nazwę zmiennej wewnętrznej na `disk_arm_count`.

---

### 9. Brak `__all__` lub `if __name__ == "__main__"` guard w kilku modułach

**Pliki:** `src/env_guard.py`, `src/librarian.py`

`env_guard.py` przy `import env_guard` **nie** uruchamia `boot_check()` automatycznie. Ale w `main.py` wywołuje `env_guard.boot_check()`. OK. Ale jeśli ktoś zaimportuje `env_guard` bez wywołania `boot_check`, nie będzie żadnej walidacji. To jest pośrednio niebezpieczne.

**Propozycja:** Dodaj komentarz ostrzegający lub zrób `boot_check()` automatycznym przy imporcie (z flaga żeby można było wyłączyć w testach).

---

### 10. `settings.html` — przyciski UPGRADE bez żadnej funkcjonalności

**Plik:** `pages/settings.html`

Strona zawiera sekcję `/// SUBSCRIPTION` z planami FREE/STANDARD/PREMIUM ($0/$9.99/$19.99/mies.) i przyciskami UPGRADE. Żaden przycisk nie robi nic (`onclick` brak, link brak). To może mylić użytkowników — wyglądają jak prawdziwe plany subskrypcyjne.

**Propozycja:** Albo usuń całą sekcję SUBSCRIPTION (projekt jest open-source/MIT), albo zastąp linkiem do GitHub Sponsors/Patreon, albo dodaj `[COMING SOON]` tooltip.

---

### 11. `settings.html` — ustawienia APPEARANCE nie działają

**Plik:** `pages/settings.html`

Sekcja `/// APPEARANCE` ma: toggle Scanlines, slider Bloom Intensity, dropdown Theme (Cyberpunk/Minimal/High Contrast), dropdown Font Size. Żadne z tych ustawień **nie jest implementowane** w JS — są tylko elementami HTML bez event listenerów i bez wpływu na wygląd.

**Propozycja:** Zaimplementuj je lub dodaj `disabled` + `[TODO]` label.

---

### 12. `dashboard.html` — statystyki galaktyki ładowane bez cache/retry

**Plik:** `pages/dashboard.html`

```js
const res = await fetch('../data/output/galaxy_data.json');
```

Brak retry logic, brak informacji o błędzie dla użytkownika (tylko `'ERR'` w stat). Gdy serwer zwróci 404, UI wygląda uszkodzone.

**Propozycja:**
```js
try {
    const res = await fetch('../data/output/galaxy_data.json');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    // ...
} catch(e) {
    document.getElementById('stat-nodes').textContent = 'N/A';
    document.getElementById('activity-log').innerHTML += `
        <div class="font-mono text-xs text-[#ff3333] p-2 border-l-2 border-[#ff3333]">
            ⚠ Brak danych galaktyki. Uruchom: python main.py
        </div>`;
}
```

---

## 🟡 ULEPSZENIA — Poprawiają jakość i UX

---

### 13. `tactical.html` — brak limit FPS / requestAnimationFrame optymalizacji

**Plik:** `pages/tactical.html`

Silnik Three.js używa `requestAnimationFrame(animate)` bez żadnego ograniczenia FPS. Na monitorach 120/144Hz renderuje ciągłe pętle na pełnej prędkości, co nieproduktywnie obciąża CPU/GPU gdy scena jest statyczna.

**Propozycja:**
```js
let lastFrameTime = 0;
const TARGET_FPS = 60;
const FRAME_MS = 1000 / TARGET_FPS;

function animate(timestamp) {
    requestAnimationFrame(animate);
    if (timestamp - lastFrameTime < FRAME_MS) return;
    lastFrameTime = timestamp;
    // ... reszta logiki
}
```

---

### 14. `tactical.html` — krawędzie grafu używają `O(n)` wyszukiwania

**Plik:** `pages/tactical.html`, funkcja `buildGalaxy()`

```js
edgeList.forEach(e => {
    const s = S.nodes.find(n => n.id === e.source);  // O(n) dla każdej krawędzi
    const t = S.nodes.find(n => n.id === e.target);  // O(n) dla każdej krawędzi
```

Dla 1000 węzłów i 2000 krawędzi = ~2 miliony porównań. Przy dużym vaulcie inicjalizacja galaktyki będzie bardzo wolna.

**Propozycja:**
```js
// Zbuduj mapę raz
const nodeMap = new Map(S.nodes.map(n => [n.id, n]));
edgeList.forEach(e => {
    const s = nodeMap.get(e.source);
    const t = nodeMap.get(e.target);
    ...
});
```

---

### 15. `src/ml_engine.py` — tylko 5 klastrów na sztywno

**Plik:** `src/ml_engine.py`

```python
cluster_names = ['Naukowy', 'Techniczny', 'Projektowy', 'Archiwalny', 'Ogólny']
n_clusters = min(5, n_docs)
```

Dla vaultu z 500 notatkami o 10 różnych tematach, KMeans ze stałym `k=5` daje słabe klastrowanie. Liczba klastrów powinna być wyznaczana dynamicznie (np. metodą łokcia lub silhouette score dla małych datasetów).

**Propozycja:**
```python
# Dynamiczne k = sqrt(n_docs / 2), ograniczone do [3, 15]
optimal_k = max(3, min(15, int(math.sqrt(n_docs / 2))))
n_clusters = min(optimal_k, n_docs)
```

---

### 16. `src/librarian.py` — timestamp mtime do sprawdzania aktualizacji jest zawodny

**Plik:** `src/librarian.py`, funkcja `sync_galaxy_map()`

```python
if mirror_path.stat().st_mtime >= src.stat().st_mtime:
    needs_update = False
```

`st_mtime` jest resetowane przy operacjach takich jak `git checkout`, `git reset`, klonowanie repo. Po fresh clone wszystkie mirrors będą uznane za aktualne nawet jeśli source pliki są nowsze logicznie.

**Propozycja:** Dodaj flagę `--force` do wymuszenia pełnej resync:
```python
parser.add_argument('--force', action='store_true', help='Wymuś resync wszystkich plików')
# i w sync_galaxy_map: needs_update = force or (mtime check)
```

---

### 17. `pages/log.html` — brak paginacji dla dużych vaultów

**Plik:** `pages/log.html`

Przy 500+ notatkach funkcja `renderList()` tworzy 500+ elementów DOM naraz. Przeglądarka może się zawiesić lub scrollowanie będzie lagować.

**Propozycja:** Dodaj wirtualizację listy lub prostą paginację (np. 50 na stronę z przyciskami PREV/NEXT).

---

### 18. `src/debugger.py` — brak testu integralności metadata.json ↔ galaxy_data.json

**Plik:** `src/debugger.py`

Debugger sprawdza, czy linki w metadata mają cel, ale nie sprawdza:
- Czy każdy `id` w `metadata.json` ma odpowiadający węzeł w `galaxy_data.json`
- Czy każdy węzeł w `galaxy_data.json` ma wpis w `metadata.json`

Brak synchronizacji = gwiazdy bez HUD lub HUD bez gwiazd.

**Propozycja:**
```python
# W full_qa_report():
galaxy_ids = set(galaxy_data.get("nodes", {}).keys())
meta_ids = set(metadata.keys())
in_galaxy_not_meta = galaxy_ids - meta_ids
in_meta_not_galaxy = meta_ids - galaxy_ids
if in_galaxy_not_meta:
    print(f"[DEBUGGER] WARN: {len(in_galaxy_not_meta)} gwiazd bez metadanych")
if in_meta_not_galaxy:
    print(f"[DEBUGGER] WARN: {len(in_meta_not_galaxy)} metadanych bez gwiazd")
```

---

### 19. `electron/main.js` — Python subprocess nie ma timeout

**Plik:** `electron/main.js`

```js
pythonProcess = spawn('python', [PYTHON_SCRIPT, '--brain', projectPath], {...});
```

Jeśli Python pipeline zawiesi się (np. blokada pliku, nieskończona pętla), `pythonProcess` nigdy nie zakończy. Użytkownik nie dostanie żadnej informacji.

**Propozycja:**
```js
const PIPELINE_TIMEOUT_MS = 5 * 60 * 1000; // 5 minut
const timeout = setTimeout(() => {
    console.error('[ELECTRON] Python backend timeout — killing process');
    pythonProcess.kill('SIGTERM');
    if (mainWindow) mainWindow.webContents.send('python-error', 'Pipeline timeout (>5min)');
}, PIPELINE_TIMEOUT_MS);
pythonProcess.on('close', () => clearTimeout(timeout));
```

---

### 20. `index.html` — wersja v3.0 w hero, ale projekt jest na v5.1

**Plik:** `index.html`

```html
<div class="...">SYSTEM ONLINE // v3.0 – 6DOF ENGINE</div>
```

Wiele miejsc w `index.html` pokazuje `v3.0`, podczas gdy `AGENTS.md`, `README.md` i `plan_v5.1.md` mówią o v5.1.0. Niespójna wersja dezorientuje użytkownika.

**Pliki z niespójnymi wersjami:**
- `index.html` — badge "v3.0" w hero i footerze
- `settings.html` — sekcja About: "Version: v5.0"
- `renderer/gp-helper.js` — `'5.1.0-web'`
- `electron/main.js` — `'Galaxy-Pilot v5.1'`

**Propozycja:** Centralny plik `version.js` lub użyj `package.json` jako single source of truth dla wersji.

---

### 21. `src/env_guard.py` — `boot_check()` wywołuje `sys.exit(1)` zamiast rzucać wyjątek

**Plik:** `src/env_guard.py`

```python
def load_env():
    if ENV_PATH.exists():
        load_dotenv(...)
    else:
        print("[SECURITY-OFFICER] BŁĄD: Brak pliku config/.env!")
        sys.exit(1)  # ← trudne do obsłużenia w testach i przy imporcie
```

`sys.exit()` w bibliotece (nie w skrypcie CLI) to zły wzorzec. Uniemożliwia unit testing i sprawia, że WATCHMAN nie może złapać błędu.

**Propozycja:** Rzuć wyjątek zamiast `sys.exit()`:
```python
class ConfigError(RuntimeError):
    pass

def load_env():
    if not ENV_PATH.exists():
        raise ConfigError(f"Brak pliku config/.env. Utwórz go z {PROJECT_ROOT}/.env.example")
    load_dotenv(dotenv_path=ENV_PATH, override=True)
```

---

## 🟢 DOBRE PRAKTYKI — Warto kontynuować

- ✅ `pipeline_guard.py` jako wzorzec supervisor — dobry pomysł
- ✅ LOCAL ML (TF-IDF + KMeans) zamiast zależności od API — świetna decyzja
- ✅ `gp-helper.js` jako abstrakcja Electron vs Web — prawidłowe podejście
- ✅ Design system jako oddzielny plik `UI_UX_Standard.md` — czytelny kontrakt
- ✅ Parallel agents via `ThreadPoolExecutor` — dobry performance pattern
- ✅ Scan for API key leaks before push — ważne zabezpieczenie
- ✅ Fallback galaxy gdy brak JSON — dobry UX dla pierwszego uruchomienia
- ✅ `content` truncated to 3000 chars — zapobiega przeciążeniu HUD

---

## 📋 PRIORYTETYZACJA NAPRAW

| # | Problem | Priorytet | Czas szacowany |
|---|---------|-----------|----------------|
| 1 | Hardcoded `C:\Users\kubar` | 🔴 Krytyczny | 1h |
| 2 | `all_files` nadpisana w metadata_engine | 🔴 Krytyczny | 15min |
| 3 | `arm_count` nadpisana w galaxy_mapper | 🟠 Ważny | 15min |
| 4 | `preload.js` sync readJSON | 🟠 Ważny | 1h |
| 5 | Duplikacja `pages/` vs `renderer/` | 🟠 Ważny | 2h |
| 6 | Brak `package.json` w repo | 🟠 Ważny | 30min |
| 7 | Settings APPEARANCE bez implementacji | 🟡 Średni | 3h |
| 8 | SUBSCRIPTION w settings — wprowadza w błąd | 🟡 Średni | 30min |
| 9 | Niespójna wersja (v3.0/v5.0/v5.1) | 🟡 Średni | 30min |
| 10 | `sys.exit()` w env_guard zamiast wyjątku | 🟡 Średni | 1h |
| 11 | Edge finding O(n) w tactical.html | 🟡 Średni | 30min |
| 12 | Brak limit FPS w render loop | 🟡 Średni | 30min |
| 13 | Python subprocess bez timeout | 🟡 Średni | 45min |
| 14 | Brak debugger cross-check meta↔galaxy | 🟡 Średni | 1h |
| 15 | Paginacja log.html dla dużych vaultów | 🟢 Niski | 2h |
| 16 | ML k=5 hardcoded | 🟢 Niski | 1h |
| 17 | Librarian mtime zawodne przy git ops | 🟢 Niski | 1h |
| 18 | Dashboard brak friendly error | 🟢 Niski | 30min |
| 19 | Watchman bez kategorii błędów fatal | 🟢 Niski | 2h |

---

## 🚀 PROPOZYCJE NOWYCH FUNKCJI (Nice-to-Have)

1. **Fulltext search w Log.html** — ctrl+F po treści notatek, nie tylko po nazwach
2. **Export galaktyki do PNG** — `renderer.domElement.toDataURL()` + download
3. **Minimap** — 2D overhead view galaktyki jako overlay w tactical.html
4. **Klastry etykietowane** — wyświetlanie nazwy ramienia spiralnego nad grupą gwiazd
5. **Tooltip hover** na gwiazdach zamiast klikania — szybszy preview
6. **Dark/Light mode** — minimal theme z ciemnym tłem ale bez scanlines (dla osób z photosensitivity)
7. **Keyboard shortcut cheatsheet** — overlay `?` pokazujący wszystkie skróty
8. **Progress bar podczas generowania galaktyki** — WebSocket lub polling `/progress.json`
9. **Lokalne wyszukiwanie pliku po kliknięciu "OPEN FILE"** — działa już dla ścieżek absolutnych, ale nie dla relatywnych
10. **Auto-reload** po zmianie `galaxy_data.json` — `setInterval` polling lub `EventSource`

---

*Wygenerowano przez Kiro na podstawie analizy kodu. Każda propozycja jest sugestią — decyzja o implementacji należy do autora.*
