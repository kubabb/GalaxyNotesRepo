# AGENTS.md – GalaxyNotesProject

Compact cheat-sheet for OpenCode. Polish-language Python project that turns an Obsidian vault into an interactive 3D galaxy (Three.js cockpit).

## Entrypoints & Boundaries

- **Main orchestrator:** `main.py` — adds `src/` to `sys.path`, then runs `env_guard` → `galaxy_mapper` → `metadata_engine` → `librarian` → `debugger` → optional `git_manager.push`.
- **Landing page (product):** `index.html` in repo root — cyberpunk marketing page, first entry point for web users. Links to cockpit and dashboard.
- **Multi-Page App (Tactical OS):**
  - `pages/dashboard.html` — Mission Control (stats, health, quick actions)
  - `pages/tactical.html` — 3D Cockpit with 6DOF flight engine
  - `pages/log.html` — Terminal-style flight log / note browser
  - `pages/settings.html` — System settings (localStorage only)
- **Legacy cockpit (frozen):** `dist/index.html` — old v2.3 single-file cockpit. Kept for reference.
- **Legacy dashboard (frozen):** `stich_galaxy_pilot_obsidian_cockpit/index.html` — old mission control.
- **Python agents:** all in `src/`. No `__init__.py` package; modules are imported directly after `sys.path.insert(0, "src")`.
- **Generated artifacts:** `data/output/*.json` (galaxy graph + metadata + checkpoints) and `.galaxy_map/` (mirror markdowns of source). Both are `.gitignore`d.
- **Design system:** `design/03_Standards/UI_UX_Standard.md` — Tactical OS spec (colors, typography, sidebar nav, page structure).

## Developer Commands

```powershell
# First-time setup (interactive)
.\setup.ps1

# Run pipeline (all agents)
python main.py
python main.py --brain "C:/path/to/vault"   # override default vault
python main.py --push                         # also git-push at the end

# Serve the whole project (required for all HTML files to load JSON)
python -m http.server 8080
# Then open:
#   http://localhost:8080/                          -> product landing page
#   http://localhost:8080/pages/dashboard.html      -> Mission Control
#   http://localhost:8080/pages/tactical.html       -> 3D cockpit (6DOF)
#   http://localhost:8080/pages/log.html            -> Flight log
#   http://localhost:8080/pages/settings.html       -> System settings

# QA / leak scan / compile check
python src/debugger.py

# Sync mirror markdowns manually
python src/librarian.py
```

## Config & Environment

- **Real config lives at** `config/.env` (not root `.env`). Multiple modules load it explicitly with `PROJECT_ROOT / "config" / ".env"`.
- **Root `.env.example`** is only a stub; do not treat it as the active config.
- **Required keys in `config/.env`:** `OPENROUTER_API_KEY`, `TARGET_PATH`, `BRAIN_PATH`. Optional: `GITHUB_TOKEN`, `GITHUB_REPO` for push.
- **Path convention:** forward slashes even on Windows (setup.ps1 normalizes them).
- **Default vault path** is hardcoded in several files: `C:\Users\kubar\OneDrive\Dokumenty\BRAIN`. If that path does not exist on your machine, always pass `--brain` or update `config/.env`.

## API / AI Mode (Important)

- **`src/metadata_engine.py` has `API_ENABLED = False` hardcoded.** The project runs in **LOCAL MODE** by default because the free OpenRouter tier (`google/gemma-4-26b-a4b-it:free`) hits rate limits (≈50 req/day).
- To re-enable AI analysis, flip `API_ENABLED = True` in `metadata_engine.py` and ensure `OPENROUTER_API_KEY` is set.
- Retry config: 3 attempts, backoff `[2, 4, 8]` s, max 3 concurrent threads.

## Pipeline Guard Behaviour

- `src/pipeline_guard.py` wraps every agent call in `try/except`. **A failing agent does not crash the pipeline**; it logs to `logs/watchman.log` and returns `None`.
- Check `logs/watchman.log` if an agent silently produces no output.

## Git & Security Quirks

- `env_guard.boot_check()` runs at startup and **exits the process** if `config/.env` is missing or `.gitignore` lacks required patterns (`.env`, `config/.env`, `__pycache__/`, etc.).
- `git_manager.py` reads `GITHUB_TOKEN` + `GITHUB_REPO` from `config/.env`, builds an HTTPS URL with token, and pushes to `origin main`.
- `debugger.py` scans the last 32 characters of the API key against all source files before push. If a leak is found, push is blocked.
- `design/` is `.gitignore`d (local-only assets), **except** `design/03_Standards/` which documents the UI standard.

## Frontend Data Contract

- `pages/*.html` expect two sibling-relative files:
  - `../data/output/galaxy_data.json` — shape: `{ nodes: { id: {x,y,z,val,color,group} }, edges: [{source,target}], meta: {...} }`
  - `../data/output/metadata.json` — shape: `{ id: { file, tooltip, star_class, energy_level, brief, content, suggested_links, stats, source } }`
- The HUD content field (`content`) is truncated to 3000 chars during generation.

## Cockpit 3D Controls (v3.0 – 6DOF)

- **W / S** – thrust forward / back (ciąg silników)
- **A / D** – strafe left / right (ruch na boki)
- **R / F** – strafe up / down (wysokość)
- **Q / E** – roll left / right (beczka)
- **RMB hold + mouse** – pitch / yaw (lot myszą)
- **LMB (center screen)** – scan / auto-pilot to star
- **Shift** – warp speed
- **C / ESC** – close HUD / cancel nav
- **Camera** is rigidly attached to ship model (child of ship group)

## Agent Personas

- `.opencode/*.md` files (`astronomer.md`, `coder.md`, `debugger.md`, `git-pusher.md`, `librarian.md`, `security_officer.md`, `storyteller.md`, `watchman.md`) are agent personas used by the OpenCode plugin. They are kept in git (`!.opencode/*.md` in `.gitignore`).
- `plan.txt` is the living project roadmap (Polish). Check it before large architectural changes.

## New / Updated Agents

- **`src/librarian.py`** — syncs `.galaxy_map/` mirror structure. Creates `.md` mirror for every source file with YAML frontmatter, tags, and WikiLinks. Run manually or via `main.py` Faza 4.
- **`src/debugger.py`** — QA agent. Compiled into `main.py` Faza 5. Runs `full_qa_report()` automatically after pipeline.
- **`src/galaxy_mapper.py` (ASTRONOMER v3.0)** — extreme volumetric dispersion. Clusters spread across ±700 on all axes, orphans up to ±1400. True 3D cloud.
