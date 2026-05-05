# BUGFIX v4.1 — Upload Sector + Ship Rotation

**Data:** 2026-05-05  
**Status:** W trakcie wdrażania

---

## Bug #1: Upload Sector nie działa

**Przyczyny:**
- Brak obsługi folderów (tylko `dataTransfer.files`)
- Brak fallback input (kliknięcie w drop zone nic nie robi)
- Zbyt wąski filtr rozszerzeń (brak pdf/docx/html/py/js)
- Brak realnego zapisu plików (tylko toast CLI)

**Rozwiązanie:**
1. Dodaj ukryte `<input type="file">` (multi-select) i `<input type="file" webkitdirectory>`
2. Rozszerz filtr do `.md .txt .pdf .docx .html .py .js .json`
3. Obsługa folderów przez `dataTransfer.items` + `webkitGetAsEntry()`
4. Kliknięcie w drop zone otwiera file picker
5. Po INITIATE IMPORT — generuj skrypt PowerShell do pobrania, który kopiuje pliki do `data/inbox/`

---

## Bug #2: Statek nie obraca się z kamerą

**Przyczyny:**
- LPM obraca KAMERĘ w orbicie (azimuth/elevation), nie statek
- Statek i kamera są niezależne
- Brak rigid chase-cam

**Rozwiązanie (chase-cam rigid):**
1. LPM + mouse → obraca STATEK (yaw/pitch), nie kamerę
2. Kamera jest sztywno za statkiem (`Vector3(0, 15, 60)` w local space statku)
3. Usuń orbitę azimuth/elevation
4. RMB opcjonalnie na orbitę wokół statku (do obserwacji)
5. Scroll zmienia odległość kamery od statku

---

## Checklist

- [ ] dashboard.html — folder upload, rozszerzenia, file picker, PS1 generator
- [ ] tactical.html — chase-cam, LPM steruje statkiem, usunięta orbita
- [ ] DEBUGGER testy
- [ ] GIT-PUSHER checkpointy
