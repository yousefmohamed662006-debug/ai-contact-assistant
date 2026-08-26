@echo off
title AI Executive Contact Assistant
echo ===================================================================
echo    Starting AI Executive Contact Assistant...
echo ===================================================================
python run.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to start with standard 'python'. Trying with py launcher...
    py run.py
)
pause
