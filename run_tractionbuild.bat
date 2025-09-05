@echo off
REM Quick batch file to start TractionBuild with Salem AI
echo 🚀 Starting TractionBuild with Salem AI...
echo.

REM Change to project directory
cd /d C:\Users\jthri\Dev\MySauce\TractionBuild

REM Start PowerShell script
powershell.exe -ExecutionPolicy Bypass -File .\start_tractionbuild.ps1

echo.
echo 🎯 TractionBuild started! Access at: http://localhost:8000
echo 🤖 Salem AI marketing automation ready!
echo.
pause
