<#
.SYNOPSIS
  Launch the Accessibility Automator backend (FastAPI) and frontend (Vite) for
  local dev on Windows. The PowerShell counterpart of run_server.sh.

  Backend:  uvicorn backend.app.main:app --reload   (http://localhost:8000)
  Frontend: npm run dev                             (http://localhost:5173)

  Each server opens in its own window. First-time setup (deps, migrate, seed the
  admin) runs only with -Setup. By default the backend runs through `uv run`
  (which self-heals the project .venv for the current OS); pass -NoUv to use the
  currently-activated venv instead.

.EXAMPLE
  ./run_server.ps1
  ./run_server.ps1 -Setup -AdminEmail you@temple.edu
  ./run_server.ps1 -NoUv
#>
param(
  [switch]$Setup,
  [string]$AdminEmail = "you@temple.edu",
  [switch]$NoUv
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Frontend = Join-Path $Root "frontend"

# Backend command prefix: "uv run" or "" (use the activated venv directly).
$Py = if ($NoUv) { "" } else { "uv run " }

if ($Setup) {
  Write-Host "== First-time setup =="
  if (-not $NoUv) {
    Write-Host "[backend] uv sync"
    Push-Location $Root; uv sync; Pop-Location
  }
  Write-Host "[backend] alembic upgrade head"
  Push-Location $Root; Invoke-Expression "$Py alembic upgrade head"; Pop-Location
  Write-Host "[backend] seeding admin ($AdminEmail)"
  Push-Location $Root; Invoke-Expression "$Py python -m backend.app.seed --admin $AdminEmail"; Pop-Location
  Write-Host "[frontend] npm install"
  Push-Location $Frontend; npm install; Pop-Location
  Write-Host "== Setup complete =="
}

Write-Host "Starting backend  -> http://localhost:8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$Root'; $Py uvicorn backend.app.main:app --reload"

Write-Host "Starting frontend -> http://localhost:5173"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$Frontend'; npm run dev"

Write-Host ""
Write-Host "Both servers launching in new windows. Open http://localhost:5173 and use the"
Write-Host "'Local dev login' box with a registered email (e.g. $AdminEmail)."
