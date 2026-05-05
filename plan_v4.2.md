# PLAN v4.2 — Upload Folders + Camera Sensitivity + Project History

**Data:** 2026-05-05

---

## Problem #1: Upload folderów nie działa

**Diagnoza:**
- `webkitdirectory` na `<input type="file">` jest przestarzałe i działa tylko w Chrome/Edge
- Drag&drop folderów przez `webkitGetAsEntry()` wymaga specyficznych uprawnień i nie jest niezawodne
- Brak fallbacku dla przeglądarek które nie obsługują `webkitGetAsEntry()`

**Rozwiązanie (3-warstwowe):**

| Warstwa | Metoda | Działanie |
|---------|--------|-----------|
| 1 (najlepsza) | `showDirectoryPicker()` | File System Access API — natywne okno wyboru folderu |
| 2 (fallback) | `<input webkitdirectory>` | Dla Chrome/Edge — wyraźny przycisk "SELECT FOLDER" |
| 3 (legacy) | Drag&drop plików | Wielokrotny wybór plików (Ctrl+A) jako zamiennik folderu |

**Zmiany w `pages/dashboard.html`:**
1. Dwa przyciski obok siebie: `[ SELECT FILES ]` i `[ SELECT FOLDER ]`
2. `showDirectoryPicker()` — główna metoda, jeśli przeglądarka wspiera
3. `webkitdirectory input` — fallback
4. Drag&drop obsługuje zarówno pliki jak i foldery przez `getAsFileSystemHandle()`

---

## Problem #2: Czułość kamery za mała

**Zmiany w `pages/tactical.html`:**
- Zwiększyć bazową `mouseSensitivity` z `0.0008` na `0.0018`
- Dodać suwak czułości w `settings.html` (obok istniejących przycisków Low/Normal/High)
- Zapisać wybraną czułość w `localStorage`

---

## Problem #3: Historia projektów + otwieranie różnych formatów

**Nowa funkcjonalność:**

### A) Historia projektów (localStorage)
```javascript
// Struktura w localStorage:
// key: "galaxy_projects"
// value: [
//   { id: "brain_default", name: "BRAIN (Domyślny)", path: "C:/Users/.../BRAIN", date: "2026-05-05T10:00:00" },
//   { id: "projekt_x", name: "Projekt X", path: "C:/Projekty/X", date: "2026-05-05T11:30:00" }
// ]
```

### B) UI w dashboard.html
Nowa sekcja "/// PROJECT.HISTORY" pod Upload Sector:
- Lista ostatnich 5 projektów (nazwa, ścieżka, data ostatniego użycia)
- Przycisk "LOAD" przy każdym — przeładowuje galaktykę z tego źródła
- Przycisk "REMOVE" — usuwa z historii
- Przycisk "CURRENT: [nazwa]" — pokazuje aktywny projekt

### C) Obsługa różnych formatów w log.html
- Obecnie `log.html` pokazuje tylko nazwy plików
- Rozszerzyć o:
  - Ikona formatu (📄 PDF, 📝 MD, 🐍 PY, itp.)
  - Treść notatki (dla .md — markdown, dla .txt — plain text, dla innych — preview)
  - Przycisk "OPEN" — otwiera oryginalny plik (jeśli możliwe) lub pokazuje treść w modalu

---

## HARMONOGRAM (checkpoint commits)

| Krok | Agent | Zadanie | Commit |
|------|-------|---------|--------|
| 1 | HERMES | Zapisać ten plan | — |
| 2 | CODER | Naprawić upload folderów w dashboard.html (3-warstwowy fallback) | ✅ |
| 3 | CODER | Zwiększyć czułość kamery w tactical.html | ✅ |
| 4 | CODER | Dodać historię projektów w dashboard.html (localStorage) | ✅ |
| 5 | CODER | Rozszerzyć log.html o formaty i treść | ✅ |
| 6 | DEBUGGER | Walidacja wszystkich zmian | ✅ |
| 7 | LIBRARIAN | Dokumentacja | — |
| 8 | GIT-PUSHER | Push | ✅ |
