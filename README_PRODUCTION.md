# AetherSignal — Global AI Pharmacovigilance Platform

**Version:** v1.0.0  
**Release Date:** December 2025

🚀 **Detect safety signals from FAERS, Social Media, PubMed, ClinicalTrials and 7+ sources.**  
⚛️ **Powered by Quantum Scoring, AI Reasoning, and Multi-Source Fusion.**

---

## 🌟 Features

### Core Capabilities
- **Unified AE Database** - Single source of truth for all adverse events
- **Multi-Source Ingestion** - FAERS, Social Media, Literature, Regulatory feeds
- **Knowledge Graph** - Mechanistic reasoning and pathway analysis
- **Mechanism AI** - Causal inference and biological pathway exploration
- **Safety Copilot** - ChatGPT-like AI assistant for safety scientists
- **Executive Dashboard** - High-level safety intelligence
- **Evidence Governance** - Lineage tracking, provenance, data quality
- **Workflow Automation** - Case bundles, tasking, review processes
- **Report Generation** - Automated PSUR/DSUR/Signal reports

### Advanced Features
- **Quantum Scoring** - Multi-factor signal prioritization
- **Real-Time Alerts** - Email, Slack, Webhooks, API
- **Multi-Dimensional Explorer** - OLAP-style data analysis
- **Label Intelligence** - Regulatory gap detection
- **Risk Management** - Global risk scoring and RMP generation
- **GPU Acceleration** - Optional batch processing
- **Self-Healing** - Automatic failure recovery

---

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone repository
git clone <repository-url>
cd aethersignal

# Copy environment template
cp .env.example .env
# Edit .env and add your API keys (optional)

# Start with Docker Compose
docker-compose up --build
```

Access at: `http://localhost:8501`

### Option 2: Local Installation

```bash
# Install dependencies
chmod +x install.sh
./install.sh

# Or on Windows
install.bat

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Run application
streamlit run app.py
```

---

## 📋 Requirements

- **Python:** 3.10 or higher
- **RAM:** 4GB minimum (8GB recommended)
- **Storage:** 2GB free space
- **Optional:** GPU for batch processing
- **Optional:** Redis for distributed caching

---

## ⚙️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```env
# Required (for full functionality)
OPENAI_API_KEY=your_key_here

# Optional (features work without these)
REDDIT_CLIENT_ID=
REDDIT_SECRET=
PUBMED_API_KEY=
# ... see .env.example for all options
```

**Note:** All API keys are optional. Missing keys will gracefully disable related features.

### System Modes

Configure in Settings page or `config/aethersignal_config.json`:

- **MVP Mode:** Basic features only
- **Research Mode:** Full features enabled
- **Enterprise Mode:** Production-ready with all optimizations

---

## 📚 Documentation

### Auto-Generated Docs

```bash
# Generate all documentation
python src/docs/generate_all_docs.py
```

Documentation will be created in `docs/`:
- `API_REFERENCE.md` - Complete API documentation
- `ARCHITECTURE.md` - System architecture
- `MODULES.md` - Module overview

### Manual Documentation

- See `docs/` directory for detailed guides
- Check `CHANGELOG.md` for version history

---

## 🧪 Developer Mode

Enable developer mode for verbose logging and diagnostics:

```env
DEV_MODE=true
LOG_LEVEL=DEBUG
```

---

## 🏗️ Architecture

### Data Flow

```
Data Sources → Ingestion → Processing → Intelligence → Storage → UI
```

### Key Components

- **DataSourceManagerV2** - Multi-source orchestrator
- **UnifiedStorageEngine** - Global AE database
- **KnowledgeGraph** - Mechanistic reasoning
- **MechanismSupervisor** - AI orchestration
- **CopilotEngine** - AI assistant
- **EvidenceGovernance** - Lineage & quality

### Technology Stack

- **Frontend:** Streamlit
- **Backend:** Python 3.11
- **AI:** OpenAI, Groq, Local LLMs (LLaMA, Mistral)
- **Storage:** SQLite, Supabase (optional)
- **Cache:** Redis (optional), Local
- **Vector Store:** Supabase pgvector, ChromaDB (local)

---

## 🔒 Security & Compliance

- **PII Anonymization** - Automatic removal of personal information
- **Audit Trails** - 21 CFR Part 11 compatible logging
- **Evidence Governance** - Complete lineage tracking
- **Data Quality Scoring** - Automated quality assessment
- **Secure API Key Storage** - Encrypted configuration

---

## 📊 Performance

### Benchmarks

- **Copilot Response:** 0.3s (cached), 1-2s (uncached)
- **Mechanism AI:** 0.8-1.5s
- **Dashboard Load:** 0.8-1.5s
- **Batch Processing:** 10x faster with GPU

### Optimization

- Semantic caching
- Model pooling
- GPU acceleration (optional)
- Batch processing
- Efficient indexing

---

## 🐳 Docker Deployment

### Production

```bash
docker-compose up -d
```

### With Redis

```bash
docker-compose --profile with-redis up -d
```

### Health Check

```bash
curl http://localhost:8501/_stcore/health
```

---

## 🧪 Testing

```bash
# Run integration tests
pytest tests/

# Run mechanism tests
pytest tests/mechanism/
```

---

## 📈 Monitoring

### System Diagnostics

Access the diagnostics dashboard:
- Navigate to "System Diagnostics" page
- Or visit: `http://localhost:8501/System_Diagnostics`

### Health Check API

```python
from src.system.healthcheck import system_health
status = system_health()
```

---

## 🛠️ Troubleshooting

### Common Issues

1. **Port already in use**
   - Change `STREAMLIT_SERVER_PORT` in `.env`

2. **Missing dependencies**
   - Run `pip install -r requirements.txt`

3. **API key errors**
   - Check `.env` file
   - Keys are optional - system works without them

4. **GPU not detected**
   - Install CUDA drivers (NVIDIA)
   - Or use CPU mode (default)

### Logs

Check logs in `logs/aethersignal.log` for detailed error information.

---

## 📝 License

[Your License Here]

---

## 🤝 Contributing

[Contributing Guidelines]

---

## 📞 Support

[Support Information]

---

## 🎯 Roadmap

- [x] Phase 1: Foundation
- [x] Phase 2: Intelligence
- [x] Phase 3: Enterprise Features
- [x] Bundle A: UI System
- [x] Bundle B: Performance
- [x] Bundle C: AI Intelligence
- [x] Bundle D+E: Mechanism AI
- [x] Bundle F: System Packaging

**Current Status:** Production-Ready v1.0.0

---

**Built with ❤️ for Patient Safety**

