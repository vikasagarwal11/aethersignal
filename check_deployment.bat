@echo off
echo ========================================
echo   AetherSignal - Deployment Diagnostics
echo ========================================
echo.

echo [1] Checking if Streamlit is running on port 8501...
netstat -ano | findstr :8501
if %ERRORLEVEL% EQU 0 (
    echo   [OK] Streamlit is listening on port 8501
) else (
    echo   [ERROR] Streamlit is NOT running on port 8501
    echo   [INFO] Please start Streamlit first:
    echo          streamlit run app.py --server.port=8501
)
echo.

echo [2] Checking if ngrok process is running...
tasklist | findstr /I "ngrok.exe"
if %ERRORLEVEL% EQU 0 (
    echo   [OK] ngrok process is running
) else (
    echo   [ERROR] ngrok process is NOT running
    echo   [INFO] Please start ngrok:
    echo          ngrok http 8501 --domain=awesomely-pottiest-jani.ngrok-free.dev
)
echo.

echo [3] Checking if Streamlit server is responding...
curl -s -o nul -w "%%{http_code}" http://localhost:8501 2>nul
if %ERRORLEVEL% EQU 0 (
    echo   [OK] Streamlit server is responding
) else (
    echo   [ERROR] Streamlit server is NOT responding
)
echo.

echo [4] Checking if ngrok API is accessible...
curl -s http://localhost:4040/api/tunnels 2>nul | findstr /C:"tunnels"
if %ERRORLEVEL% EQU 0 (
    echo   [OK] ngrok API is accessible
    echo   [INFO] Check tunnel status at: http://localhost:4040
) else (
    echo   [ERROR] ngrok API is NOT accessible
    echo   [INFO] ngrok may not be running
)
echo.

echo [5] Testing remote URL...
curl -s -o nul -w "HTTP %%{http_code}" https://awesomely-pottiest-jani.ngrok-free.dev/ 2>nul
if %ERRORLEVEL% EQU 0 (
    echo   [INFO] Remote URL check completed
) else (
    echo   [ERROR] Cannot reach remote URL
)
echo.

echo ========================================
echo   Diagnostic Complete
echo ========================================
echo.
echo Next steps:
echo   1. If Streamlit is not running: Start it with 'streamlit run app.py'
echo   2. If ngrok is not running: Start it with 'ngrok http 8501 --domain=awesomely-pottiest-jani.ngrok-free.dev'
echo   3. Check ngrok status: Open http://localhost:4040 in browser
echo   4. Check ngrok authentication: Run 'ngrok config check'
echo.
pause

