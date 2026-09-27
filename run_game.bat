@echo off
title Dig and Treasure
echo Starting Dig and Treasure...
python3.11 main.py
if %ERRORLEVEL% NEQ 0 (
    echo Python 3.11 failed, trying python...
    python main.py
)
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Game ended or could not find Python.
    pause
)
