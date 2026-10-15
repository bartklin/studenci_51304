@echo off
chcp 65001 >nul
cd /d "%~dp0"
py -3 sprawdz_zadania.py %*
set "RC=%ERRORLEVEL%"
echo.
echo Kod wyniku: %RC%
pause
exit /b %RC%
