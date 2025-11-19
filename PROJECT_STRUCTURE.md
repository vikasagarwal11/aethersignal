# AetherSignal - Project Structure

## 📁 Current Organization

```
aethersignal/
├── app.py                    # Main Streamlit application (keep at root for Streamlit)
├── requirements.txt          # Python dependencies
├── README.md                 # Main documentation
│
├── src/                      # Source code modules
│   ├── faers_loader.py      # FAERS/PDF file loader
│   ├── nl_query_parser.py   # Natural language query parser
│   ├── pdf_report.py        # PDF report generator
│   ├── pv_schema.py         # Schema detection & normalization
│   ├── quantum_ranking.py   # Quantum-inspired ranking
│   ├── signal_stats.py      # PRR/ROR calculations & statistics
│   └── utils.py             # Utility functions
│
├── scripts/                  # Startup & utility scripts
│   ├── setup_ngrok.bat      # First-time ngrok configuration
│   ├── start_server.bat     # Start Streamlit server
│   ├── start_ngrok.bat      # Start ngrok tunnel
│   ├── start_all.bat        # Start server + ngrok together
│   └── check_server.ps1     # Check if server is running
│
├── docs/                     # Documentation
│   └── HOSTING_SETUP.md     # Complete hosting guide
│
├── __pycache__/             # Python cache (auto-generated)
│
└── [Root convenience scripts]
    ├── setup_ngrok.bat      # → calls scripts\setup_ngrok.bat
    ├── start_all.bat        # → calls scripts\start_all.bat
    └── start_server.bat     # → calls scripts\start_server.bat
```

## 🎯 Design Decisions

### Why `app.py` at root?
- **Streamlit convention**: Streamlit looks for `app.py` at project root by default
- **Easy deployment**: Most hosting platforms expect main file at root
- **Simplicity**: `streamlit run app.py` works without path adjustments

### Why `src/` folder?
- **Organization**: All Python modules in one place
- **Scalability**: Easy to add more modules as project grows
- **Clean root**: Keeps root directory uncluttered
- **Import path**: Automatically added to `sys.path` in `app.py`

### Why `scripts/` folder?
- **Separation**: Batch files and utilities separate from code
- **Maintainability**: Easy to find and update startup scripts
- **Convention**: Common pattern in Python projects

### Why `docs/` folder?
- **Organization**: All documentation in one place
- **Scalability**: Room for API docs, guides, etc.
- **Clean root**: Keeps README at root (standard), other docs organized

### Root convenience scripts?
- **User-friendly**: Quick access to common tasks
- **No path confusion**: Users can run from root without navigating
- **Wrapper pattern**: All point to scripts in `scripts/` folder

## 🚀 Usage

### From root directory:
```bash
# All of these work from root:
streamlit run app.py
scripts\setup_ngrok.bat
scripts\start_all.bat
start_all.bat              # Convenience wrapper
```

### File organization makes sense for:
- ✅ Easy navigation
- ✅ Scalability
- ✅ Professional structure
- ✅ Standard Python project layout
- ✅ Team collaboration

## 📝 Notes

- All imports in `app.py` automatically work via `sys.path` modification
- Batch scripts handle path changes automatically with `cd /d "%~dp0\.."`
- No changes needed to Python imports when adding new modules to `src/`
- Future additions: tests/ folder, data/ folder, config/ folder as needed


