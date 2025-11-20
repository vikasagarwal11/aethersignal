@echo off
echo ========================================
echo   AetherSignal - Starting Server (Debug Mode)
echo ========================================
echo.
cd /d "%~dp0"
echo Current directory: %CD%
echo.
echo Testing Python...
python --version
echo.
echo Testing Streamlit import...
python -c "import streamlit; print('Streamlit version:', streamlit.__version__)"
echo.
echo Testing app.py import...
python -c "import app; print('App imported successfully')" 2>&1
echo.
echo Starting Streamlit server...
echo.
streamlit run app.py --server.port=8501 --server.headless=true
pause

