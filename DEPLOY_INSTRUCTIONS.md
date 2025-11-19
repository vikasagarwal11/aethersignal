# 🚀 Deployment Instructions

## Quick Deploy to ngrok

Your Streamlit app is already running on port 8501. To make it accessible via your ngrok domain:

### Option 1: Use the deployment script (Recommended)

1. **Double-click** `start_ngrok_deploy.bat` in the project root
   
   OR run from command line:
   ```bash
   start_ngrok_deploy.bat
   ```

2. This will start ngrok and tunnel to your Streamlit server

3. Your app will be accessible at:
   **https://awesomely-pottiest-jani.ngrok-free.dev/**

### Option 2: Manual ngrok command

If you prefer to run manually:

```bash
ngrok http 8501 --domain=awesomely-pottiest-jani.ngrok-free.dev
```

### Option 3: Use existing scripts

If you want to start both server and ngrok together:

1. **Terminal 1**: Start Streamlit (if not already running)
   ```bash
   streamlit run app.py --server.port=8501
   ```

2. **Terminal 2**: Start ngrok
   ```bash
   ngrok http 8501 --domain=awesomely-pottiest-jani.ngrok-free.dev
   ```

## Verify Deployment

1. ✅ Streamlit is running on port 8501 (verified)
2. ⏳ Start ngrok tunnel (run `start_ngrok_deploy.bat`)
3. ✅ Access your app at: **https://awesomely-pottiest-jani.ngrok-free.dev/**

## Troubleshooting

### If ngrok command not found:
- Make sure ngrok is installed and in your PATH
- Or download from: https://ngrok.com/download
- Or place `ngrok.exe` in the project root

### If domain doesn't work:
- Make sure you have a reserved domain in your ngrok account
- Check your ngrok dashboard: https://dashboard.ngrok.com/
- Verify the domain is active and linked to your account

### If Streamlit isn't running:
```bash
streamlit run app.py --server.port=8501
```

## Notes

- Keep both Streamlit and ngrok running for the app to be accessible
- The ngrok URL will work as long as both processes are running
- For permanent hosting, consider Streamlit Cloud or other cloud platforms

