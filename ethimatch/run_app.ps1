# Launch EthiMatch Streamlit using the project virtual environment.
# Usage (from this folder):  .\run_app.ps1

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $Root "venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    Write-Error "Virtual environment not found. Run: python -m venv venv"
    exit 1
}

Set-Location $Root
& $Python -m streamlit run app.py
