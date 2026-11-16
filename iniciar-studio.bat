@echo off
REM Abre o Studio da Agencia Zero1 (http://localhost:4747)
cd /d "%~dp0"
start "" /min node studio\server.js
timeout /t 2 >nul
start "" http://localhost:4747
