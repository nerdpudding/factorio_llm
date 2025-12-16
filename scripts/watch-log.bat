@echo off
title Factorio Log Viewer
:loop
cls
echo === FACTORIO LOG (refreshes every 3 sec, Ctrl+C to stop) ===
echo.
type "%APPDATA%\Factorio\factorio-current.log"
timeout /t 3 >nul
goto loop
