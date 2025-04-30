@echo off
cd /d "%~dp0"
echo Now running from: %cd%
powershell -ExecutionPolicy Bypass -File setup.ps1
pause
