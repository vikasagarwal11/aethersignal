@echo off
cd /d "%~dp0\.."
echo ========================================
echo   AetherSignal - Starting Server
echo ========================================
echo.
echo Starting Streamlit on port 8501...
echo.
echo Local URL: http://localhost:8501
echo.
echo Press Ctrl+C to stop the server
echo.
streamlit run app.py --server.port=8501 --server.headless=true

