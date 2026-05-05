# UI/UX Standard – Tactical OS

## 1. Architektura podstron

Aplikacja Galaxy-Pilot oparta jest na wielostronicowej architekturze (Multi-Page App).

| Podstrona | Plik | Opis |
|-----------|------|------|
| Landing | `index.html` (root) | Strona produktu, CTA, funkcje, jak to działa |
| Panel Dowodzenia | `pages/dashboard.html` | Statystyki galaktyki, system health, szybkie akcje |
| Wizjer Taktyczny | `pages/tactical.html` | Kokpit 3D z silnikiem 6DOF i galaktyką wolumetryczną |
| Dziennik Lotu | `pages/log.html` | Przeglądarka notatek w stylu terminala, filtry |
| Konfiguracja | `pages/settings.html` | Ustawienia lokalne (localStorage), mock API config |

## 2. Design System – Tactical OS

### Kolory (tokeny)
- `primary: #e3fdff`, `primary-container: #00f3ff`, `primary-dim: #00dce6`
- `secondary: #ffabf3`, `secondary-container: #fe00fe`
- `tertiary: #e8ffda`, `tertiary-container: #36fd0f`
- `bg: #000000`, `surface: #131313`, `surface-container: #1f1f1f`
- `on-surface: #e2e2e2`, `on-surface-variant: #b9cacb`
- `outline: #849495`, `outline-variant: #3a494b`

### Typografia
- **Nagłówki**: Space Grotesk, bold, tracking-tight
- **Dane / UI**: JetBrains Mono, 10–14px, uppercase, tracking-widest
- **Proza**: Inter, 16px, line-height 1.6

### Efekty globalne
- **Scanlines**: fixed div z `linear-gradient` co 4px, `mix-blend-mode: overlay`
- **Bloom**: `text-shadow` i `box-shadow` w kolorze akcentu
- **Tech Border**: pseudo-elementy `::before/::after` z 10px narożnikami
- **Glitch hover**: `translateX(2px)` + zmiana tła

### Nawigacja boczna (Sidebar)
- Szerokość: 56px (rozwinięta: 200px na hover)
- Pozycja: fixed left
- Zawiera: ikony Material Symbols + etykiety tekstowe
- Aktywna podstrona: lewa border-cyan-400 + bg cyan/10

### Top Bar
- Wysokość: 44px
- Tytuł modułu (lewo) + status (prawo)
- `backdrop-filter: blur(12px)`

## 3. Kontrakt danych

- `../data/output/galaxy_data.json` – węzły, krawędzie, meta
- `../data/output/metadata.json` – briefy, klasy, energia, treść

## 4. 6DOF Controls (Wizjer Taktyczny)

| Klawisz | Akcja |
|---------|-------|
| W/S | Ciąg silników (przód/tył) |
| A/D | Strafing (lewo/prawo) |
| R/F | Wysokość (góra/dół) |
| Q/E | Roll (beczka) |
| RMB + mysz | Pitch / Yaw |
| LPM (center) | Skanuj cel / Auto-pilot |
| Shift | Warp Drive |
| C / ESC | Anuluj nawigację / zamknij HUD |

## 5. Bezpieczeństwo

- Klucze API (`OPENROUTER_API_KEY`, `GITHUB_TOKEN`) pozostają wyłącznie w `config/.env` (backend).
- Frontend nie ma dostępu do wrażliwych danych.
- `settings.html` zapisuje jedynie mock-config w `localStorage`.
