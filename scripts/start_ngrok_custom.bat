@echo off
cd /d "%~dp0\.."
echo ========================================
echo   AetherSignal - Starting ngrok Tunnel
echo ========================================
echo.
echo Starting ngrok tunnel to localhost:8501...
echo.
echo Your app will be accessible at the ngrok URL shown below.
echo.
echo If you have a reserved domain, it will use that.
echo Otherwise, ngrok will assign a random domain.
echo.
pause
ngrok http 8501 --domain=awesomely-pottiest-jani.ngrok-free.dev

