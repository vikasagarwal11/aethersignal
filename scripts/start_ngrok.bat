@echo off
cd /d "%~dp0\.."
echo ========================================
echo   AetherSignal - Starting ngrok Tunnel
echo ========================================
echo.
echo IMPORTANT: Make sure you've set up ngrok first!
echo Run: scripts\setup_ngrok.bat (first time only)
echo.
echo Starting ngrok tunnel to localhost:8501...
echo.
echo Copy the HTTPS URL shown below to share with others!
echo.
pause
ngrok http 8501

