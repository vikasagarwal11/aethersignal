# 🚀 Deployment Instructions

## Option 1: Cloud Deployment (Recommended)

### Deploy to Render.com

1. **Go to**: https://render.com → Sign up/Login
2. **New** → **Web Service**
3. **Connect GitHub** → Select your `aethersignal` repository
4. **Configure**:
   - **Name**: `aethersignal-app`
   - **Environment**: `Python 3`
   - **Build Command**: 
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
     ```
5. **Environment Variables** (optional - app works without them):
   - Add any API keys you want to enable (see ENV_TEMPLATE.md)
6. **Create Web Service**
7. **Wait for deployment** (~5-10 minutes)
8. **Access your app**: `https://your-app.onrender.com`

### Deploy to Railway

1. **Go to**: https://railway.app → Sign up/Login
2. **New Project** → **Deploy from GitHub**
3. **Select** your `aethersignal` repository
4. **Configure**:
   - Root Directory: `/`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
5. **Set Environment Variables** (optional)
6. **Deploy** - Railway auto-deploys on push
7. **Access your app**: Railway provides a URL automatically

---

## Option 2: Local Docker Deployment

### Prerequisites
- Docker Desktop installed and running

### Steps

1. **Start Docker Desktop** (if not running)

2. **Deploy**:
   ```bash
   docker-compose up --build -d
   ```

3. **Access**: http://localhost:8501

4. **View logs**:
   ```bash
   docker-compose logs -f
   ```

5. **Stop**:
   ```bash
   docker-compose down
   ```

---

## Option 3: Local Streamlit (No Docker)

### Steps

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run**:
   ```bash
   streamlit run app.py
   ```

3. **Access**: http://localhost:8501

---

## Quick Deploy Script

For Windows, you can use:
```bash
start_server.bat
```

This will start the Streamlit server locally.

---

## Environment Variables

The app works without API keys! Free data sources (OpenFDA, PubMed, ClinicalTrials.gov) work without configuration.

To enable additional features, create a `.env` file (see ENV_TEMPLATE.md) with your API keys.

---

## Verification

After deployment, verify:
- ✅ App loads at the URL
- ✅ No errors in logs
- ✅ Can navigate between pages
- ✅ Data sources are accessible

---

## Troubleshooting

### Docker Issues
- Ensure Docker Desktop is running
- Check: `docker ps` should work without errors

### Port Already in Use
- Change port in docker-compose.yml or use: `STREAMLIT_SERVER_PORT=8502`

### Missing Dependencies
- Run: `pip install -r requirements.txt`

### API Key Errors
- Keys are optional - app works without them
- Check `.env` file if you added keys

