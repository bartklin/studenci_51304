@echo off
chcp 65001 >nul
cd /d "%~dp0"
py -3 -m unittest discover -s testy -p test_przeplyw.py -v %*
set "RC=%ERRORLEVEL%"
echo.
echo Kod wyniku: %RC%
pause
exit /b %RC%
