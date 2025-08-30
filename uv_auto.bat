@echo off
REM Windows batch file wrapper for uv_auto.ps1
REM Usage: uv_auto.bat [clean]

if "%1"=="clean" (
    powershell -ExecutionPolicy Bypass -File "%~dp0uv_auto.ps1" clean
) else (
    powershell -ExecutionPolicy Bypass -File "%~dp0uv_auto.ps1"
)
