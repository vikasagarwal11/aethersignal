@echo off
echo ========================================
echo   AetherSignal - Deploying via ngrok
echo ========================================
echo.
echo Starting ngrok tunnel to localhost:8501...
echo.
echo Your app will be accessible at:
echo   https://awesomely-pottiest-jani.ngrok-free.dev/
echo.
echo Make sure Streamlit is running on port 8501!
echo.
pause
ngrok http 8501 --domain=awesomely-pottiest-jani.ngrok-free.dev

