# GalaxyNotesProject – Setup (Windows PowerShell)
# SECURITY-OFFICER: Interaktywny setup środowiska

Write-Host "=== GALAXY-PILOT ENGINE: FAZA INICJACJI ===" -ForegroundColor Cyan
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
        Write-Host "[SECURITY-OFFICER] Klucz API załadowany z .env" -ForegroundColor Green
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
    $apiKey = Read-Host "Podaj klucz API OpenRouter (Google Gemma 4 26B A4B free)"
}

# Jeśli brak ścieżek, zapytaj
if ([string]::IsNullOrWhiteSpace($targetPath)) {
    $defaultTarget = (Get-Location).Path -replace '\\', '/'
    $targetPath = Read-Host "Podaj ścieżkę do projektu (TARGET_PATH) [$defaultTarget]"
    if ([string]::IsNullOrWhiteSpace($targetPath)) {
        $targetPath = $defaultTarget
    }
}

if ([string]::IsNullOrWhiteSpace($brainPath)) {
    $defaultBrain = "C:/Users/kubar/OneDrive/Dokumenty/BRAIN"
    $brainPath = Read-Host "Podaj ścieżkę do vaultu BRAIN [$defaultBrain]"
    if ([string]::IsNullOrWhiteSpace($brainPath)) {
        $brainPath = $defaultBrain
    }
}

# Zapisz .env
@"
# GalaxyNotesProject – Konfiguracja środowiska
# SECURITY-OFFICER: Ten plik jest chroniony przez .gitignore
# NIGDY nie commituj tego pliku!

# OpenRouter API – Model: Google Gemma 4 26B A4B (free)
OPENROUTER_API_KEY=$apiKey
OPENROUTER_MODEL=google/gemma-4-26b-it

# Ścieżki (używaj slashów, nawet na Windows)
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
Write-Host "[LIBRARIAN] Przygotowuję strukturę .galaxy_map/ ..." -ForegroundColor Cyan

# Utwórz foldery
$dirs = @("data/output", "00_Runtime", ".galaxy_map", "dist")
foreach ($d in $dirs) {
    if (-not (Test-Path $d)) {
        New-Item -ItemType Directory -Path $d | Out-Null
        Write-Host "  + $d/" -ForegroundColor DarkGray
    }
}

Write-Host ""
Write-Host "=== FAZA INICJACJI ZAKOŃCZONA ===" -ForegroundColor Green
Write-Host "Uruchom pipeline: python main.py" -ForegroundColor Cyan
