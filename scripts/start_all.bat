@echo off
cd /d "%~dp0\.."
echo ========================================
echo   AetherSignal - Complete Setup
echo ========================================
echo.
echo This will start both Streamlit server AND ngrok tunnel.
echo.
echo IMPORTANT: Make sure you've run scripts\setup_ngrok.bat first!
echo.
pause
echo.
echo Starting Streamlit server...
start "AetherSignal Server" cmd /c "%~dp0start_server.bat"
timeout /t 5 /nobreak >nul
echo.
echo Starting ngrok tunnel...
echo (Check the ngrok window for your public HTTPS URL)
echo.
start "ngrok Tunnel" cmd /c "%~dp0start_ngrok.bat"
echo.
echo ========================================
echo   Both services are starting...
echo ========================================
echo.
echo Local URL: http://localhost:8501
echo Public URL: Check the ngrok window
echo.
echo To stop: Close both terminal windows or press Ctrl+C in each
echo.
pause

