@echo off
rem Start the catalog dashboard (double-click or run from a terminal).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0catalog.ps1" start %*
if errorlevel 1 pause
