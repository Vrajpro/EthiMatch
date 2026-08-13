@echo off

REM Launch EthiMatch with the project virtual environment.

REM Always use this script — do NOT run "streamlit run app.py" with system Python.

cd /d "%~dp0"



set "PY="

if exist "venv\Scripts\python.exe" set "PY=venv\Scripts\python.exe"

if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"



if "%PY%"=="" (

  echo [EthiMatch] No virtual environment found. Creating venv ...

  python -m venv venv

  if errorlevel 1 (

    echo Failed to create venv. Install Python 3.10+ and try again.

    exit /b 1

  )

  set "PY=venv\Scripts\python.exe"

)



echo [EthiMatch] Using Python: %CD%\%PY%



"%PY%" -c "import transformers" >nul 2>&1

if errorlevel 1 (

  echo [EthiMatch] transformers not found in this venv. Installing requirements ...

  "%PY%" -m pip install --upgrade pip

  "%PY%" -m pip install -r requirements.txt

  if errorlevel 1 (

    echo pip install failed.

    exit /b 1

  )

)



echo [EthiMatch] Starting Streamlit ...

"%PY%" -m streamlit run app.py

pause

