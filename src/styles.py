"""
AetherSignal - Centralized Stylesheet
All CSS styling for consistent theme across the platform
"""

AETHERSIGNAL_THEME_CSS = """
<style>
/* ============================================
   HEADER & SIDEBAR TOGGLE (Must be first)
   ============================================ */
/* Hide Streamlit's default header completely */
header[data-testid="stHeader"] {
    display: none !important;
}

/* Force sidebar toggle button to be visible on ALL pages */
button[kind="header"] {
    display: block !important;
    visibility: visible !important;
    z-index: 1000000 !important;
    background: #1e293b !important;
    color: white !important;
}

/* ============================================
   GLOBAL APP STYLING
   ============================================ */
.stApp {
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 50%, #e2e8f0 100%) !important;
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", system-ui, sans-serif;
    color: #0f172a;
    padding-top: 80px !important; /* Universal padding for fixed nav bar */
}

/* Main content container */
.block-container {
    padding-top: 1.25rem !important;
    padding-bottom: 2rem !important;
    max-width: 1180px !important;
}

/* Ensure nav bar is above everything */
.aether-top-nav {
    position: fixed !important;
    z-index: 999999 !important;
}

/* Force sidebar to start below nav bar */
[data-testid="stSidebar"] {
    margin-top: 70px !important;
}

[data-testid="stSidebar"] .block-container {
    padding-top: 1rem !important;
}

/* Hide Streamlit Cloud Deploy button */
#MainMenu {
    visibility: hidden;
}

.stDeployButton {
    display: none !important;
}

button[title="Deploy this app"],
button[title="Manage app"] {
    display: none !important;
}

/* Hide Streamlit menu button */
header[data-testid="stHeader"] > div:first-child button {
    display: none !important;
}

/* Ensure sidebar toggle button is ALWAYS visible - even when sidebar is collapsed */
button[data-testid="baseButton-header"],
button[aria-label*="sidebar"],
button[aria-label*="Close"],
button[aria-label*="Open"],
button[aria-label*="Settings"],
button[title*="sidebar"],
button[title*="Sidebar"],
button[title*="Settings"],
button[kind="header"] {
    display: block !important;
    visibility: visible !important;
    position: fixed !important;
    top: 16px !important;
    left: 16px !important;
    z-index: 1000001 !important;
    opacity: 1 !important;
    pointer-events: auto !important;
    background: rgba(15,23,42,0.9) !important;
    color: white !important;
    border: 1px solid rgba(148,163,184,0.5) !important;
    border-radius: 999px !important;
    padding: 0.4rem 0.7rem !important;
    box-shadow: 0 6px 18px rgba(15,23,42,0.4) !important;
    min-width: 40px !important;
    min-height: 40px !important;
}

/* Make sure sidebar toggle is not hidden anywhere */
[data-testid="stSidebar"] ~ * button[data-testid="baseButton-header"],
.stApp > div:first-child button[data-testid="baseButton-header"],
.stApp button[kind="header"] {
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
}

/* Ensure sidebar itself doesn't disappear - just slides out */
[data-testid="stSidebar"] {
    display: block !important;
    visibility: visible !important;
}

/* When collapsed, slide sidebar left but keep toggle visible */
[data-testid="stSidebar"][aria-expanded="false"] {
    transform: translateX(-100%) !important;
    transition: transform 300ms ease !important;
}

/* Sidebar toggle should ALWAYS be visible regardless of sidebar state */
[data-testid="stSidebar"][aria-expanded="false"] ~ button[kind="header"],
[data-testid="stSidebar"][aria-expanded="true"] ~ button[kind="header"],
button[kind="header"] {
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
}

/* Full-width hero section override */
.main-hero,
.main-header {
    max-width: 100% !important;
    margin-left: 0 !important;
    margin-right: 0 !important;
    width: 100% !important;
}

/* ============================================
   HEADER / HERO (Enterprise Blue + Slate)
   ============================================ */
.main-header {
    background:
      radial-gradient(circle at 0% 0%, rgba(59,130,246,0.12), transparent 55%),
      radial-gradient(circle at 100% 100%, rgba(15,23,42,0.08), transparent 60%),
      linear-gradient(135deg, #1e40af 0%, #2563eb 45%, #3b82f6 100%);
    color: #ffffff;
    padding: 1.5rem 2rem;
    border-radius: 20px;
    margin-bottom: 1.5rem;
    box-shadow: 
        0 20px 50px rgba(30, 64, 175, 0.3),
        0 0 0 1px rgba(255, 255, 255, 0.1) inset;
    position: relative;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.main-header h1 {
    margin: 0;
    font-size: 2rem;
    font-weight: 700;
    letter-spacing: 0.01em;
    position: relative;
    z-index: 1;
}

.main-header p {
    margin: 0.4rem 0 0 0;
    font-size: 0.96rem;
    opacity: 0.94;
    position: relative;
    z-index: 1;
}

.main-header-pill-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 0.9rem;
    position: relative;
    z-index: 1;
}

.hero-pill-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 0.75rem;
    position: relative;
    z-index: 1;
}

.hero-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 0.4rem 0.9rem;
    border-radius: 999px;
    font-size: 0.78rem;
    backdrop-filter: blur(12px) saturate(180%);
    -webkit-backdrop-filter: blur(12px) saturate(180%);
    border: 1px solid rgba(255, 255, 255, 0.25);
    color: #ffffff;
    background: rgba(15, 23, 42, 0.35);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    transition: all 0.2s ease-out;
}

.hero-pill:hover {
    background: rgba(15, 23, 42, 0.5);
    transform: translateY(-1px);
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
}

.hero-pill span {
    font-size: 0.85rem;
}

.pill-session {
    background: rgba(30, 64, 175, 0.4);
    border-color: rgba(191, 219, 254, 0.4);
}

.pill-faers {
    background: rgba(99, 102, 241, 0.4);
    border-color: rgba(196, 181, 253, 0.4);
}

.pill-quantum {
    background: rgba(59, 130, 246, 0.5);
    border-color: rgba(191, 219, 254, 0.5);
    color: #ffffff;
}

/* Legacy support for main-header-pill-row */
.main-header-pill-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 0.75rem;
    position: relative;
    z-index: 1;
}

/* Soft glow in background (enterprise style) */
.main-header::before,
.main-hero::before {
    content: "";
    position: absolute;
    inset: -30%;
    background:
      radial-gradient(circle at 10% 0%, rgba(191,219,254,0.25), transparent 50%),
      radial-gradient(circle at 95% 90%, rgba(148,163,184,0.15), transparent 55%);
    opacity: 0.6;
    pointer-events: none;
    filter: blur(40px);
}

/* Reset-session button column spacing */
.stButton>button.reset-btn {
    background: #ffffff;
    color: #1e3a8a !important;
    border-radius: 999px;
    border: 1px solid rgba(148,163,184,0.6);
    padding: 0.45rem 1.1rem;
    font-weight: 600;
    font-size: 0.88rem;
    box-shadow: 0 6px 18px rgba(15,23,42,0.12);
    transition: transform 0.12s ease-out, box-shadow 0.12s ease-out, background 0.12s ease-out;
}

.stButton>button.reset-btn:hover {
    transform: translateY(-1px);
    background: #f9fafb;
    box-shadow: 0 10px 24px rgba(15,23,42,0.22);
}

/* Legacy support for .main-hero (if used in app.py) */
.main-hero {
    background:
      radial-gradient(circle at 0% 0%, rgba(59,130,246,0.12), transparent 55%),
      radial-gradient(circle at 100% 100%, rgba(15,23,42,0.08), transparent 60%),
      linear-gradient(135deg, #1e40af 0%, #2563eb 45%, #3b82f6 100%);
    color: #ffffff;
    padding: 1.5rem 2rem;
    border-radius: 20px;
    margin-bottom: 1.5rem;
    box-shadow: 
        0 20px 50px rgba(30, 64, 175, 0.3),
        0 0 0 1px rgba(255, 255, 255, 0.1) inset;
    position: relative;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.main-hero::before {
    content: "";
    position: absolute;
    inset: -30%;
    background:
      radial-gradient(circle at 10% 0%, rgba(191,219,254,0.25), transparent 50%),
      radial-gradient(circle at 95% 90%, rgba(148,163,184,0.15), transparent 55%);
    opacity: 0.6;
    pointer-events: none;
    filter: blur(40px);
}

.main-hero h1 {
    position: relative;
    margin: 0;
    font-size: 2rem;
    font-weight: 700;
    letter-spacing: 0.01em;
    z-index: 1;
}

.main-hero p {
    position: relative;
    margin: 0.4rem 0 0 0;
    font-size: 0.96rem;
    opacity: 0.94;
    z-index: 1;
}

.hero-badge {
    position: relative;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 3px 10px;
    border-radius: 999px;
    background: rgba(15,23,42,0.28);
    border: 1px solid rgba(191,219,254,0.8);
    font-size: 0.78rem;
    margin-bottom: 0.4rem;
    backdrop-filter: blur(10px);
    color: #e5edff;
    z-index: 1;
}

.hero-badge-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #22c55e;
    box-shadow: 0 0 0 0 rgba(34,197,94,0.7);
    animation: pulse-dot 1.6s infinite;
}

@keyframes pulse-dot {
  0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(34,197,94,0.7); }
  70% { transform: scale(1.55); box-shadow: 0 0 0 12px rgba(34,197,94,0); }
  100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(34,197,94,0); }
}

/* ============================================
   TOAST / BANNER / CHIPS
   ============================================ */
.inline-banner {
    background: #fff9e6;
    border-left: 4px solid #f6ad55;
    padding: 0.65rem 0.85rem;
    border-radius: 10px;
    font-size: 0.8rem;
    margin-bottom: 0.9rem;
    color: #744210;
}

.session-chip-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 0.2rem;
}

.session-chip {
    padding: 3px 10px;
    font-size: 0.78rem;
    border-radius: 999px;
    background: #edf2ff;
    border: 1px solid #c7d2fe;
    color: #3730a3;
}

.filter-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #e0f2fe;
    color: #1d4ed8;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 0.78rem;
    margin: 3px 6px 3px 0;
    border: 1px solid #bfdbfe;
}

/* Beta badge in sidebar */
.beta-badge {
    display:inline-flex;
    align-items:center;
    justify-content:center;
    padding: 0.05rem 0.45rem;
    border-radius:999px;
    background: #fff7ed;
    color:#c05621;
    font-size:0.7rem;
    font-weight:600;
    margin-left:0.35rem;
    border: 1px solid #fbd38d;
}

/* ============================================
   CARDS & SECTION TITLES (with fade-in animation)
   ============================================ */
.block-card {
    background: #ffffff;
    padding: 18px 22px;
    border-radius: 24px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 18px 40px rgba(15,23,42,0.08);
    margin-top: 16px;
    margin-bottom: 18px;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    overflow: visible;
    position: relative;
    animation: fadeInUp 0.4s ease-out;
}

@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.block-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 24px 55px rgba(15,23,42,0.14);
    border-color: #bfdbfe;
}

/* Remove top margin from first heading in cards */
.block-card h3:first-child,
.block-card h2:first-child,
.block-card h4:first-child {
    margin-top: 0 !important;
}

/* Reduce top margin for first card in a section */
.block-card:first-of-type {
    margin-top: 8px;
}

.nl-panel {
    background: rgba(255, 255, 255, 0.85);
    border-radius: 20px;
    padding: 1.25rem 1.35rem 1.8rem;
    box-shadow: 0 28px 60px rgba(15, 23, 42, 0.15);
    border: 1px solid rgba(148, 163, 184, 0.3);
    margin-bottom: 1rem;
    width: 100%;
    box-sizing: border-box;
}

.nl-panel .stExpander > div[data-testid="stExpanderContent"] {
    background: #fdfdfd;
    border-radius: 22px;
    padding: 0.9rem 1rem 1rem;
    box-shadow: inset 0 1px 6px rgba(15, 23, 42, 0.08);
}

/* Quick suggestions buttons inside expander */
.nl-panel div[data-testid="stExpander"] .stButton button {
    border-radius: 999px !important;
    min-height: 40px !important;
    border: 1px solid rgba(59, 130, 246, 0.3) !important;
    background: #ffffff !important;
    color: #1f2937 !important;
    font-weight: 600;
    font-size: 0.95rem;
    box-shadow: 0 10px 22px rgba(15, 23, 42, 0.08);
    transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
    padding: 0 1.25rem !important;
    margin-bottom: 0.45rem !important;
}

.nl-panel div[data-testid="stExpander"] .stButton button:hover {
    transform: translateY(-1px);
    border-color: rgba(37, 99, 235, 0.65) !important;
    box-shadow: 0 14px 30px rgba(37, 99, 235, 0.12);
}

.nl-textarea-shell {
    border-radius: 24px;
    padding: 0.5rem;
    background: linear-gradient(180deg, rgba(59, 130, 246, 0.08), rgba(37, 99, 235, 0.03));
    box-shadow: 0 16px 32px rgba(15, 23, 42, 0.07);
}

.nl-textarea-shell .stTextArea textarea {
    background: #f7fbff !important;
    border: 1px solid rgba(148, 163, 184, 0.5) !important;
    border-radius: 18px !important;
    padding: 1rem !important;
    box-shadow: inset 0 2px 6px rgba(15, 23, 42, 0.08);
    font-size: 1rem;
    line-height: 1.5;
    min-height: 140px;
}

.step-label {
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #6b7280;
    margin-bottom: 0.15rem;
}

.section-title {
    font-size: 1.05rem;
    font-weight: 600;
    color: #111827;
    margin-bottom: 0.35rem;
}

/* Headlines */
h2, h3 {
    color: #111827 !important;
}

.disclaimer-banner {
    background-color: #fff9e6;
    border-left: 4px solid #f6ad55;
    padding: 0.9rem 1rem;
    margin-bottom: 1.2rem;
    border-radius: 8px;
    font-size: 0.86rem;
    color: #744210;
}

.session-banner {
    background-color: #eff6ff;
    border-left: 3px solid #3b82f6;
    padding: 0.4rem 0.7rem;
    margin-bottom: 0.9rem;
    border-radius: 6px;
    font-size: 0.8rem;
    color: #1e40af;
}


/* ============================================
   KPI METRICS
   ============================================ */
.kpi-value {
    font-size: 1.6rem;
    font-weight: 700;
    color: #111827;
    line-height: 1.1;
    margin: 0;
}

.kpi-label {
    font-size: 0.78rem;
    font-weight: 500;
    color: #6b7280;
    margin: 2px 0 0 0;
}

/* ============================================
   BUTTONS (with ripple effect)
   ============================================ */
.stButton>button {
    position: relative;
    overflow: hidden;
    background: linear-gradient(135deg,#2563eb 0%,#1d4ed8 100%);
    color: #f9fafb !important;
    border-radius: 999px;
    border: none;
    padding: 0.5rem 1.4rem;
    font-weight: 600;
    font-size: 0.9rem;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    cursor: pointer;
}

/* Ripple effect */
.stButton>button::before {
    content: "";
    position: absolute;
    top: 50%;
    left: 50%;
    width: 0;
    height: 0;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.4);
    transform: translate(-50%, -50%);
    transition: width 0.6s, height 0.6s, opacity 0.6s;
    opacity: 0;
}

.stButton>button:active::before {
    width: 300px;
    height: 300px;
    opacity: 0;
    transition: width 0s, height 0s, opacity 0.6s;
}

.stButton>button::after {
    content: "";
    position: absolute;
    inset: 0;
    background: radial-gradient(circle at center, rgba(255,255,255,0.25), transparent 60%);
    opacity: 0;
    transform: scale(0.8);
    transition: opacity 0.3s ease-out, transform 0.3s ease-out;
}

.stButton>button:hover::after {
    opacity: 1;
    transform: scale(1);
}

.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 30px rgba(37,99,235,0.65);
    background: linear-gradient(135deg,#1d4ed8 0%,#1e40af 100%);
}

.stButton>button:active {
    transform: translateY(0);
    box-shadow: 0 4px 12px rgba(15,23,42,0.3);
}

.stButton>button:disabled {
    background: linear-gradient(135deg, #9ca3af 0%, #6b7280 100%) !important;
    border-color: #6b7280 !important;
    color: #ffffff !important;
    opacity: 0.6;
    cursor: not-allowed;
    transform: none !important;
}

/* Secondary buttons */
.stButton>button[kind="secondary"] {
    background: #ffffff !important;
    color: #1e3a8a !important;
    border: 1px solid rgba(148,163,184,0.6) !important;
    box-shadow: 0 6px 18px rgba(15,23,42,0.12);
}

.stButton>button[kind="secondary"]:hover {
    background: #f9fafb !important;
    box-shadow: 0 10px 24px rgba(15,23,42,0.22);
}

/* ============================================
   TABLES & DATAFRAMES
   ============================================ */
/* Zebra striping and hover for dataframes */
.dataframe tbody tr:nth-child(even) {
    background-color: #f9fafb !important;
}

.dataframe tbody tr:hover {
    background-color: #eff6ff !important;
}

.dataframe th {
    background-color: #f3f4f6 !important;
    color: #374151 !important;
    font-weight: 600 !important;
    font-size: 0.8rem !important;
}

.dataframe td {
    font-size: 0.8rem !important;
    color: #111827 !important;
}

.css-1q1n0ol, .stMetric {
    color: #111827 !important;
}



/* ============================================
   SIDEBAR
   ============================================ */
[data-testid="stSidebar"] {
    background-color: #f8fafc;
    border-right: 1px solid #e2e8f0;
}

[data-testid="stSidebar"] .block-container {
    padding-top: 1.25rem !important;
}

[data-testid="stSidebar"] h3 {
    margin-top: 0.75rem;
    margin-bottom: 0.35rem;
    font-size: 0.95rem;
    font-weight: 600;
}

/* Reset session button styling */
.reset-session-hint {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #94a3b8;
    margin-bottom: 0.25rem;
}

/* Reset session button styling - targets button in sidebar after reset-session-hint */
.reset-session-hint ~ div button {
    border-radius: 999px !important;
    background: #f8fafc !important;
    color: #0f172a !important;
    border: 1px solid #e2e8f0 !important;
    font-size: 0.8rem !important;
    padding: 0.3rem 0.9rem !important;
    font-weight: 500 !important;
    box-shadow: 0 2px 4px rgba(15,23,42,0.05) !important;
}

.reset-session-hint ~ div button:hover {
    background: #e2e8f0 !important;
    border-color: #cbd5e1 !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(15,23,42,0.1) !important;
}

/* More specific selector for reset button by key attribute */
div[data-testid="stSidebar"] button[data-testid="baseButton-secondary"][key="reset_session_sidebar"],
div[data-testid="stSidebar"] .reset-session-hint + div button {
    border-radius: 999px !important;
    background: #f8fafc !important;
    color: #0f172a !important;
    border: 1px solid #e2e8f0 !important;
    font-size: 0.8rem !important;
    padding: 0.3rem 0.9rem !important;
    font-weight: 500 !important;
    box-shadow: 0 2px 4px rgba(15,23,42,0.05) !important;
}

div[data-testid="stSidebar"] button[data-testid="baseButton-secondary"][key="reset_session_sidebar"]:hover,
div[data-testid="stSidebar"] .reset-session-hint + div button:hover {
    background: #e2e8f0 !important;
    border-color: #cbd5e1 !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(15,23,42,0.1) !important;
}



/* ============================================
   FILE UPLOADER / DROPZONE (Frosted Glass Design)
   ============================================ */
/* Hide the default "Limit 200MB per file" text - Streamlit shows this in small text */
[data-testid="stFileUploadDropzone"] small,
[data-testid="stFileUploadDropzone"] p small,
[data-testid="stFileUploadDropzone"] div small,
[data-testid="stFileUploadDropzone"] > div > small,
div[data-testid="stFileUploadDropzone"] small[class*="size"],
[data-testid="stFileUploadDropzone"] p[class*="caption"],
[data-testid="stFileUploadDropzone"] div[class*="caption"] {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}
[data-testid="stFileUploadDropzone"] {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(248, 250, 252, 0.95) 100%) !important;
    backdrop-filter: blur(12px) saturate(180%) !important;
    -webkit-backdrop-filter: blur(12px) saturate(180%) !important;
    border-radius: 24px !important;
    border: 2px dashed rgba(37, 99, 235, 0.3) !important;
    padding: 2rem 1.5rem !important;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 
        0 8px 32px rgba(15, 23, 42, 0.08),
        inset 0 1px 0 rgba(255, 255, 255, 0.9),
        0 0 0 1px rgba(37, 99, 235, 0.05) !important;
    position: relative;
    overflow: hidden;
}

/* Sky gradient border effect on hover */
[data-testid="stFileUploadDropzone"]::before {
    content: "";
    position: absolute;
    inset: -2px;
    border-radius: 24px;
    padding: 2px;
    background: linear-gradient(135deg, 
        rgba(37, 99, 235, 0.4) 0%, 
        rgba(56, 189, 248, 0.3) 50%,
        rgba(129, 230, 217, 0.2) 100%);
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    opacity: 0;
    transition: opacity 0.25s ease-out;
    pointer-events: none;
}

[data-testid="stFileUploadDropzone"]:hover::before {
    opacity: 1;
}

[data-testid="stFileUploadDropzone"]:hover {
    border-color: rgba(37, 99, 235, 0.5) !important;
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(239, 246, 255, 0.98) 100%) !important;
    box-shadow: 
        0 16px 48px rgba(37, 99, 235, 0.15),
        inset 0 1px 0 rgba(255, 255, 255, 0.95),
        0 0 0 1px rgba(37, 99, 235, 0.1) !important;
    transform: translateY(-2px);
}

/* Tweaks to the text/icons inside the dropzone */
[data-testid="stFileUploadDropzone"] div {
    color: #334155 !important;
    font-size: 0.9rem !important;
}

/* File input and Browse files button styling */
input[type="file"] {
    border: 1.5px solid #cbd5e1 !important;
    border-radius: 8px !important;
    background-color: #ffffff !important;
    padding: 0.5rem 0.75rem !important;
    font-size: 0.9rem !important;
    color: #111827 !important;
    box-shadow: 0 2px 4px rgba(15,23,42,0.06) !important;
    transition: all 0.15s ease-out !important;
}

input[type="file"]:hover {
    border-color: #2563eb !important;
    box-shadow: 0 4px 8px rgba(37,99,235,0.15) !important;
    background-color: #f8fafc !important;
}

input[type="file"]:focus {
    border-color: #2563eb !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.1), 0 4px 8px rgba(37,99,235,0.15) !important;
    outline: none !important;
}

/* Hide the empty file input field that appears after upload */
div[data-testid="stFileUploader"] input[type="file"]:not(:focus):not(:hover) {
    opacity: 0.3;
}

/* Hide file input when files are already uploaded (the redundant one below Load button) */
div[data-testid="stFileUploader"]:has(+ button) input[type="file"],
div[data-testid="stFileUploader"] ~ input[type="file"] {
    display: none !important;
}

/* Browse files button styling */
div[data-testid="stFileUploader"] button,
div[data-testid="stFileUploader"] button[data-testid="baseButton-secondary"] {
    border: 1.5px solid #cbd5e1 !important;
    border-radius: 8px !important;
    background-color: #ffffff !important;
    color: #111827 !important;
    padding: 0.5rem 1rem !important;
    font-size: 0.9rem !important;
    font-weight: 500 !important;
    box-shadow: 0 2px 4px rgba(15,23,42,0.06) !important;
    transition: all 0.15s ease-out !important;
}

div[data-testid="stFileUploader"] button:hover {
    border-color: #2563eb !important;
    background-color: #f8fafc !important;
    box-shadow: 0 4px 8px rgba(37,99,235,0.15) !important;
    color: #1e40af !important;
}

/* ============================================
   HIDE EMPTY CONTAINERS (fix white pill bar)
   ============================================ */
/* Kill the ghost white pill between sections */
div[data-testid="element-container"] > div:empty {
    display: none !important;
    height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}

/* If a card has essentially no content, hide it too */
div[data-testid="element-container"]:has(> div.block-card:only-child:empty) {
    display: none !important;
}

/* Hide empty Streamlit containers that create visual gaps */
div[data-testid="stVerticalBlock"] > div:empty,
div[data-testid="stHorizontalBlock"] > div:empty {
    display: none !important;
}

/* Hide any st.empty() containers that create white lines */
div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]:empty,
div[data-testid="stHorizontalBlock"] > div[data-testid="stHorizontalBlock"]:empty,
div[data-testid="element-container"]:empty {
    display: none !important;
    height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    border: none !important;
    background: transparent !important;
}

/* Remove any horizontal lines from empty containers */
div[data-testid="stVerticalBlock"]:has(> div:empty) {
    gap: 0 !important;
}

/* ============================================
   SELECTBOX / DROPDOWN STYLING
   ============================================ */
/* Make selectboxes more visible with better borders and shadows */
div[data-testid="stSelectbox"] > div > div {
    border: 1.5px solid #cbd5e1 !important;
    border-radius: 8px !important;
    background-color: #ffffff !important;
    box-shadow: 0 2px 4px rgba(15,23,42,0.06) !important;
    transition: all 0.15s ease-out !important;
}

div[data-testid="stSelectbox"] > div > div:hover {
    border-color: #2563eb !important;
    box-shadow: 0 4px 8px rgba(37,99,235,0.15) !important;
    background-color: #f8fafc !important;
}

div[data-testid="stSelectbox"] > div > div:focus-within {
    border-color: #2563eb !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.1), 0 4px 8px rgba(37,99,235,0.15) !important;
    outline: none !important;
}

/* Selectbox input text */
div[data-testid="stSelectbox"] input {
    color: #111827 !important;
    font-weight: 500 !important;
}

/* Selectbox dropdown arrow */
div[data-testid="stSelectbox"] svg {
    color: #64748b !important;
}

div[data-testid="stSelectbox"] > div > div:hover svg {
    color: #2563eb !important;
}

/* ============================================
   EXPANDER STYLING
   ============================================ */
/* Make expanders more visible */
div[data-testid="stExpander"] {
    border: 1.5px solid #e2e8f0 !important;
    border-radius: 12px !important;
    background-color: #f8fafc !important;
    padding: 0.5rem !important;
    margin-bottom: 0.75rem !important;
    box-shadow: 0 2px 4px rgba(15,23,42,0.04) !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

div[data-testid="stExpander"]:hover {
    border-color: #cbd5e1 !important;
    box-shadow: 0 4px 12px rgba(15,23,42,0.08) !important;
    background-color: #ffffff !important;
    transform: translateY(-1px);
}

/* Expander header (clickable area) */
div[data-testid="stExpander"] > summary,
div[data-testid="stExpander"] > div[data-testid="stExpanderToggleIcon"] {
    color: #374151 !important;
    font-weight: 500 !important;
    padding: 0.5rem 0.75rem !important;
    border-radius: 6px !important;
    transition: background-color 0.15s ease-out !important;
}

div[data-testid="stExpander"] > summary:hover {
    background-color: #f1f5f9 !important;
}

/* Fix Quick suggestions text color - ensure it's not red */
div[data-testid="stExpander"] summary,
div[data-testid="stExpander"] summary *,
div[data-testid="stExpander"] summary p,
div[data-testid="stExpander"] summary span,
div[data-testid="stExpander"] summary div {
    color: #374151 !important;
}

/* More specific selector for expander text content */
div[data-testid="stExpander"] > summary > div,
div[data-testid="stExpander"] > summary > span,
div[data-testid="stExpander"] > summary > p {
    color: #374151 !important;
}

/* Override any red/warning colors in expander headers */
div[data-testid="stExpander"] summary {
    color: #374151 !important;
}

div[data-testid="stExpander"] summary * {
    color: inherit !important;
}

/* Expander content area */
div[data-testid="stExpander"] > div[data-testid="stExpanderContent"] {
    padding: 0.75rem 1rem !important;
    background-color: #ffffff !important;
    border-radius: 0 0 8px 8px !important;
}

/* ============================================
   QUERY HISTORY BUTTONS
   ============================================ */
/* Style query history buttons with icons and better grouping */
div[data-testid="stExpander"] .stButton button[key^="history_"] {
    background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%) !important;
    border: 1.5px solid #e2e8f0 !important;
    border-radius: 12px !important;
    color: #0f172a !important;
    font-weight: 500 !important;
    font-size: 0.88rem !important;
    padding: 0.65rem 1rem !important;
    margin-bottom: 0.5rem !important;
    text-align: left !important;
    box-shadow: 0 2px 6px rgba(15, 23, 42, 0.06) !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    position: relative;
    overflow: hidden;
}

div[data-testid="stExpander"] .stButton button[key^="history_"]::before {
    content: "";
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 3px;
    background: linear-gradient(180deg, #2563eb 0%, #3b82f6 100%);
    opacity: 0;
    transition: opacity 0.2s ease-out;
}

div[data-testid="stExpander"] .stButton button[key^="history_"]:hover {
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%) !important;
    border-color: #cbd5e1 !important;
    transform: translateX(4px);
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.12) !important;
}

div[data-testid="stExpander"] .stButton button[key^="history_"]:hover::before {
    opacity: 1;
}

div[data-testid="stExpander"] .stButton button[key="clear_history"] {
    background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%) !important;
    border: 1.5px solid #fca5a5 !important;
    color: #991b1b !important;
    font-weight: 600 !important;
    margin-top: 0.75rem !important;
}

div[data-testid="stExpander"] .stButton button[key="clear_history"]:hover {
    background: linear-gradient(135deg, #fecaca 0%, #fca5a5 100%) !important;
    border-color: #ef4444 !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2) !important;
}

/* ============================================
   SMOOTH TRANSITIONS FOR STATE CHANGES
   ============================================ */
/* Fade in for results sections */
div[data-testid="stVerticalBlock"]:has(.block-card) {
    animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
    from {
        opacity: 0;
    }
    to {
        opacity: 1;
    }
}

/* Icon transition effects */
.stButton>button[class*="icon"] svg,
.stButton>button:has(svg) svg {
    transition: transform 0.2s ease-out;
}

.stButton>button:hover:has(svg) svg {
    transform: scale(1.1);
}

/* ============================================
   MISC
   ============================================ */
.text-muted {
    color: #6b7280 !important;
}

.text-quiet {
    color: #9ca3af !important;
}

</style>
"""


def get_theme_css() -> str:
    """
    Returns the complete AetherSignal theme CSS stylesheet.
    
    Returns:
        CSS string ready to be injected via st.markdown(..., unsafe_allow_html=True)
    """
    return AETHERSIGNAL_THEME_CSS


def apply_theme():
    """
    Helper function to apply the theme in Streamlit.
    Call this once at the start of your app.
    """
    import streamlit as st
    st.markdown(get_theme_css(), unsafe_allow_html=True)
