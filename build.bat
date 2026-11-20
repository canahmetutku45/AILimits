@echo off
rem AI Limits -> dist\AILimits.exe (single file, no console)
cd /d "%~dp0"
python -m pip install --disable-pip-version-check -q -r requirements-build.txt || exit /b 1
python make_icon.py || exit /b 1
python -m PyInstaller --noconfirm --clean --onefile --windowed ^
  --name AILimits --icon icon.ico ^
  --version-file version_info.txt ^
  --add-data "assets;assets" ^
  ai_limits.pyw || exit /b 1
echo.
echo Done: %~dp0dist\AILimits.exe
