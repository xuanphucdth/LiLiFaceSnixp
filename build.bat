@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Build environment missing. The ready-to-use app is in dist\LiLiFaceSnixp.
  exit /b 1
)
".venv\Scripts\python.exe" -m PyInstaller --noconfirm LiLiFaceSnixp.spec
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" tools\package_licenses.py
if errorlevel 1 exit /b 1
copy /y README.md dist\LiLiFaceSnixp\README.md >nul
copy /y THIRD_PARTY.md dist\LiLiFaceSnixp\THIRD_PARTY.md >nul
echo Ready: dist\LiLiFaceSnixp\LiLiFaceSnixp.exe
