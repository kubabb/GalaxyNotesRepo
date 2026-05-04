# GalaxyNotesProject – Setup v2.0 (Windows PowerShell)
# SECURITY-OFFICER + LIBRARIAN: Interaktywny setup z drag&drop i dynamicznym TARGET_PATH

Write-Host "=== GALAXY-PILOT EVOLUTION v2.0: FAZA INICJACJI ===" -ForegroundColor Cyan
Write-Host ""

# Sprawdź czy config istnieje
if (-not (Test-Path "config")) {
    New-Item -ItemType Directory -Path "config" | Out-Null
    Write-Host "[LIBRARIAN] Utworzono folder config/" -ForegroundColor Green
}

# Wczytaj istniejący .env jeśli jest
$envPath = "config/.env"
$apiKey = ""
$targetPath = ""
$brainPath = ""

if (Test-Path $envPath) {
    Write-Host "[SECURITY-OFFICER] Znaleziono istniejący config/.env" -ForegroundColor Yellow
    $content = Get-Content $envPath -Raw
    if ($content -match 'OPENROUTER_API_KEY=(.+)') {
        $apiKey = $matches[1].Trim()
    }
    if ($content -match 'TARGET_PATH=(.+)') {
        $targetPath = $matches[1].Trim()
    }
    if ($content -match 'BRAIN_PATH=(.+)') {
        $brainPath = $matches[1].Trim()
    }
}

# Jeśli brak klucza, zapytaj
if ([string]::IsNullOrWhiteSpace($apiKey)) {
    $apiKey = Read-Host "Podaj klucz API OpenRouter (opcjonalnie, Enter=pomiń)"
}

# Ścieżka do projektu – drag&drop lub wpisana
Write-Host ""
Write-Host "[LIBRARIAN] Wybierz folder projektu do wizualizacji:" -ForegroundColor Cyan
Write-Host "  1. Wpisz ścieżkę ręcznie" -ForegroundColor Gray
Write-Host "  2. Użyj aktualnego folderu (GalaxyNotesProject)" -ForegroundColor Gray
Write-Host "  3. Użyj vaultu BRAIN jako źródła" -ForegroundColor Gray
Write-Host ""

$choice = Read-Host "Wybierz opcje (1/2/3) [domyslnie 2]"
switch ($choice) {
    "1" { $targetPath = Read-Host "Podaj pelna sciezke do folderu" }
    "3" { $targetPath = "C:/Users/kubar/OneDrive/Dokumenty/BRAIN" }
    default { 
        if ([string]::IsNullOrWhiteSpace($targetPath)) {
            $targetPath = (Get-Location).Path -replace '\\', '/'
        }
    }
}

# Walidacja ścieżki
$targetPath = $targetPath -replace '\\', '/'
if (-not (Test-Path $targetPath)) {
    Write-Host "[SECURITY-OFFICER] BLAD: Sciezka nie istnieje: $targetPath" -ForegroundColor Red
    exit 1
}

Write-Host "[LIBRARIAN] TARGET_PATH ustawiony na: $targetPath" -ForegroundColor Green

# BRAIN path
if ([string]::IsNullOrWhiteSpace($brainPath)) {
    $defaultBrain = "C:/Users/kubar/OneDrive/Dokumenty/BRAIN"
    $brainPath = Read-Host "Podaj sciezke do vaultu BRAIN [$defaultBrain]"
    if ([string]::IsNullOrWhiteSpace($brainPath)) {
        $brainPath = $defaultBrain
    }
}
$brainPath = $brainPath -replace '\\', '/'

# Zapisz .env
@"
# GalaxyNotesProject v2.0 – Konfiguracja
# SECURITY-OFFICER: Ten plik jest chroniony przez .gitignore
# NIGDY nie commituj tego pliku!

# OpenRouter API – Model: Google Gemma 4 26B A4B (free)
OPENROUTER_API_KEY=$apiKey
OPENROUTER_MODEL=google/gemma-4-26b-a4b-it:free

# Sciezki (uzywaj slashow, nawet na Windows)
TARGET_PATH=$targetPath
BRAIN_PATH=$brainPath

# GitHub (opcjonalnie, do pusha)
GITHUB_TOKEN=
GITHUB_REPO=

# Logi
LOG_LEVEL=INFO
"@ | Set-Content $envPath -Encoding UTF8

Write-Host ""
Write-Host "[SECURITY-OFFICER] Konfiguracja zapisana w $envPath" -ForegroundColor Green
Write-Host "[LIBRARIAN] Przygotowuje strukture .galaxy_map/ ..." -ForegroundColor Cyan

# Utwórz foldery
$dirs = @("data/output", "00_Runtime", ".galaxy_map", "dist", "assets")
foreach ($d in $dirs) {
    if (-not (Test-Path $d)) {
        New-Item -ItemType Directory -Path $d | Out-Null
        Write-Host "  + $d/" -ForegroundColor DarkGray
    }
}

Write-Host ""
Write-Host "=== FAZA INICJACJI ZAKONCZONA ===" -ForegroundColor Green
Write-Host "  TARGET_PATH: $targetPath" -ForegroundColor Cyan
Write-Host "  BRAIN_PATH:  $brainPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "Nastepne kroki:" -ForegroundColor Yellow
Write-Host "  1. Uruchom pipeline: python main.py" -ForegroundColor White
Write-Host "  2. Otworz kokpit:   python -m http.server 8080  ->  http://localhost:8080/dist/" -ForegroundColor White
Write-Host "  3. Drag&Drop:       Przeciagnij folder na ekran kokpitu 3D" -ForegroundColor White
Write-Host ""
