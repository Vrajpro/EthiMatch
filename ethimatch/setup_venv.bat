@echo off

REM One-time (or repair) setup: create venv and install all dependencies.

cd /d "%~dp0"



if not exist "venv\Scripts\python.exe" (

  echo Creating virtual environment ...

  python -m venv venv

  if errorlevel 1 exit /b 1

)



echo Installing requirements into venv ...

venv\Scripts\python.exe -m pip install --upgrade pip

venv\Scripts\python.exe -m pip install -r requirements.txt



echo.

echo Verifying transformers ...

venv\Scripts\python.exe -c "import transformers; print('OK transformers', transformers.__version__)"

echo.

echo Done. Start the app with:  run_app.bat

pause

