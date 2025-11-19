# AetherSignal - Hosting Setup Guide

## 🚀 Quick Start (5 minutes)

### Step 1: Start the Server
Double-click `start_server.bat` (or `scripts\start_server.bat`) or run:
```bash
streamlit run app.py --server.port=8501
```
**Local URL:** http://localhost:8501

---

## 🌐 Share with the World (ngrok - Recommended)

### First Time Setup (2 minutes)

1. **Download ngrok**
   - Go to: https://ngrok.com/download
   - Download Windows version
   - Unzip `ngrok.exe` to `C:\ngrok` (or any folder)
   - Add to PATH, OR copy `ngrok.exe` to this project folder

2. **Get your authtoken**
   - Sign up at: https://dashboard.ngrok.com/signup (free)
   - Copy your authtoken from the dashboard

3. **Run setup script**
   ```bash
   setup_ngrok.bat
   ```
   Or: `scripts\setup_ngrok.bat`
   
   Enter your authtoken when prompted.

### Daily Use

**Option A: Separate terminals**
```bash
# Terminal 1: Start server
start_server.bat
# OR: scripts\start_server.bat

# Terminal 2: Start ngrok tunnel
start_ngrok.bat
# OR: scripts\start_ngrok.bat
```

**Option B: Everything at once**
```bash
start_all.bat
# OR: scripts\start_all.bat
```

### Share Your URL

After starting ngrok, you'll see:
```
Forwarding   https://xxxx-xxxx.ngrok-free.app -> http://localhost:8501
```

**Copy the HTTPS URL** and share it with anyone in the world!

---

## 🔒 Alternative: Cloudflare Tunnel (Free, Permanent URL)

### Setup (5 minutes)

1. **Install cloudflared**
   ```bash
   winget install cloudflare.cloudflared
   ```

2. **Login**
   ```bash
   cloudflared tunnel login
   ```

3. **Create tunnel**
   ```bash
   cloudflared tunnel create aethersignal
   ```

4. **Run tunnel**
   ```bash
   cloudflared tunnel run aethersignal
   ```

You'll get a permanent URL like: `https://aethersignal.yourdomain.com`

---

## 💻 System Requirements

- **OS:** Windows 10/11
- **Python:** 3.8+
- **RAM:** 8GB+ (you have 32GB - perfect!)
- **GPU:** Optional but recommended (you have RTX 5090 - excellent!)
- **Internet:** Required for external access

---

## 🛠️ Troubleshooting

### Port 8501 already in use?
```bash
# Find what's using it
netstat -ano | findstr :8501

# Or use a different port
streamlit run app.py --server.port=8502
ngrok http 8502
```

### ngrok not found?
- Make sure `ngrok.exe` is in your PATH
- OR copy `ngrok.exe` to this project folder
- OR use full path: `C:\ngrok\ngrok.exe http 8501`

### Can't access from external network?
- Make sure ngrok/cloudflared is running
- Check firewall isn't blocking port 8501
- Try the HTTPS URL (not HTTP) from ngrok

---

## 📊 Performance Tips

Your RTX 5090 + 32GB RAM is perfect for:
- ✅ Large FAERS datasets (millions of rows)
- ✅ Multiple concurrent users (10-20 users)
- ✅ Real-time quantum ranking calculations

### For maximum performance:
1. Close unnecessary applications
2. Use SSD for data files (if loading from disk)
3. Consider increasing Streamlit memory limit if needed

---

## 🔗 Quick Links

- **ngrok Dashboard:** https://dashboard.ngrok.com
- **Cloudflare Zero Trust:** https://one.dash.cloudflare.com
- **Streamlit Docs:** https://docs.streamlit.io

---

## 📝 Notes

- **Free ngrok tier:** 1 tunnel, 40 connections/min (perfect for demos)
- **Paid ngrok:** $8/month for unlimited (if you scale)
- **Security:** All ngrok connections are HTTPS encrypted
- **Session data:** Data stays on YOUR machine (secure & private)

---

**Ready to share?** Run `start_all.bat` and copy the ngrok HTTPS URL! 🚀

