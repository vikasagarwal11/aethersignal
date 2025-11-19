@echo off
echo ========================================
echo   AetherSignal - ngrok Setup Guide
echo ========================================
echo.
echo This will help you set up ngrok for external access.
echo.
echo STEP 1: Download ngrok
echo   - Go to: https://ngrok.com/download
echo   - Download Windows version
echo   - Unzip ngrok.exe to a folder (e.g., C:\ngrok)
echo   - Add that folder to your PATH, OR keep ngrok.exe in this directory
echo.
echo STEP 2: Get your authtoken
echo   - Sign up at: https://dashboard.ngrok.com/signup (free)
echo   - Copy your authtoken from the dashboard
echo.
echo STEP 3: Enter your authtoken below
echo.
pause
cd /d "%~dp0\.."
echo.
set /p authtoken="Enter your ngrok authtoken: "
if "%authtoken%"=="" (
    echo Error: No authtoken provided. Please run this script again.
    pause
    exit /b 1
)
echo.
echo Authenticating ngrok...
ngrok config add-authtoken %authtoken%
if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo   SUCCESS! ngrok is now configured.
    echo ========================================
    echo.
    echo Next steps:
    echo   1. Run scripts\start_server.bat (in one terminal)
    echo      OR use convenience wrapper: start_server.bat
    echo   2. Run scripts\start_ngrok.bat (in another terminal)
    echo      OR use convenience wrapper: start_ngrok.bat
    echo   3. Copy the HTTPS URL from ngrok to share!
    echo.
    echo   OR just run: start_all.bat (does both at once)
    echo.
) else (
    echo.
    echo ========================================
    echo   ERROR: Could not authenticate ngrok
    echo ========================================
    echo.
    echo Make sure:
    echo   - ngrok.exe is in your PATH or current directory
    echo   - Your authtoken is correct
    echo   - You have internet connection
    echo.
)
pause

