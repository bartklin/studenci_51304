@echo off
chcp 65001 >nul
cd /d "%~dp0"
py -3 kontrola_wyniku.py %*
set "RC=%ERRORLEVEL%"
echo.
echo Kod wyniku: %RC%
pause
exit /b %RC%
