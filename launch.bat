@echo off
cd /d "%~dp0"
echo Now running from: %cd%
powershell -ExecutionPolicy Bypass -File src\setup.ps1
pause
