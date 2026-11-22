@echo off
rem Stop the catalog dashboard started with start.cmd.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0catalog.ps1" stop %*
if errorlevel 1 pause
