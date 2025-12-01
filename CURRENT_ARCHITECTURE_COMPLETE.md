# AetherSignal - Complete Current Architecture Documentation

## 📋 Executive Summary

**AetherSignal** is a **server-side Python/Streamlit application** for pharmacovigilance signal detection and analysis. It provides natural language querying, statistical analysis (PRR/ROR), quantum-inspired ranking, and a ChatGPT-like conversational interface for safety data exploration.

**Architecture Type:** Server-Side, Streamlit-Based, Python-First  
**Deployment:** Streamlit Cloud compatible  
**Status:** Fully functional, production-ready  
**Lines of Code:** ~15,000+ lines  
**Language:** Python 3.12  

---

## 🏗️ Technology Stack

### **Core Framework:**
- **UI Framework:** Streamlit 1.38.0 (Python-based reactive web framework)
- **Language:** Python 3.12
- **Data Processing:** Pandas 2.2.2, NumPy 1.26.4, SciPy
- **Visualization:** Plotly 5.22.0
- **PDF Generation:** fpdf2 2.8.5

### **Backend Services:**
- **Database:** Supabase (PostgreSQL) with Row-Level Security (RLS)
- **Authentication:** Supabase Auth (email/password, email verification)
- **Storage:** 
  - In-memory (session state) for uploaded files
  - Supabase PostgreSQL for persistent multi-tenant data

### **AI/LLM Integration:**
- **LLM Providers:** OpenAI GPT-4o-mini, Anthropic Claude, Groq (LLaMA-3 70B)
- **Frameworks:** OpenAI SDK, Anthropic SDK, HuggingFace Hub
- **Hybrid Approach:** Rule-based parsing first, LLM fallback optional

### **Additional Libraries:**
- **Fuzzy Matching:** rapidfuzz 3.5.2
- **Quantum Computing:** PennyLane 0.38.0 (quantum-inspired algorithms)
- **ML (Optional):** Transformers 4.35.0, PyTorch (optional)
- **Data Matching:** recordlinkage 0.16.0 (cross-source deduplication)

---

## 📁 Complete File Structure

```
aethersignal/
│
├── app.py                          # Main Streamlit application entry point
├── requirements.txt                # Python dependencies
├── runtime.txt                     # Python version specification
│
├── pages/                          # Streamlit multi-page app structure
│   ├── 1_Quantum_PV_Explorer.py   # Main PV analysis page (protected)
│   ├── 2_Social_AE_Explorer.py    # Social media AE analysis (protected)
│   ├── Login.py                    # Authentication page
│   ├── Register.py                 # User registration page
│   └── Profile.py                  # User profile management
│
├── src/                            # Core application code
│   │
│   ├── ui/                         # User Interface Components
│   │   ├── chat_interface.py       # ChatGPT-like chat UI component (NEW)
│   │   ├── query_interface.py      # Natural language query interface
│   │   ├── upload_section.py       # File upload and processing
│   │   ├── results_display.py      # Results visualization (tables, charts)
│   │   ├── top_nav.py              # Top navigation bar
│   │   ├── sidebar.py              # Sidebar navigation and filters
│   │   ├── header.py               # Page header component
│   │   ├── schema_mapper.py        # Schema mapping UI
│   │   ├── drill_down.py           # Drill-down analysis views
│   │   ├── case_series_viewer.py   # Case series viewer
│   │   └── auth/                   # Auth UI components
│   │       ├── login.py
│   │       ├── register.py
│   │       └── profile.py
│   │
│   ├── ai/                         # AI/LLM Components
│   │   ├── hybrid_router.py        # Route queries (rule-based + LLM)
│   │   ├── conversational_engine.py # Process conversational queries
│   │   ├── llm_interpreter.py      # LLM query interpretation
│   │   ├── medical_llm.py          # Unified LLM interface
│   │   ├── signal_summarizer.py    # Generate signal summaries
│   │   ├── narrative_analyzer.py   # Analyze case narratives
│   │   ├── literature_enhancer.py  # Literature integration
│   │   ├── meddra_enhancer.py      # MedDRA terminology enhancement
│   │   └── stream_helpers.py       # Streaming UI helpers (NEW)
│   │
│   ├── auth/                       # Authentication & User Management
│   │   ├── auth.py                 # Core auth functions (login, register, logout)
│   │   └── user_management.py      # User profile management
│   │
│   ├── social_ae/                  # Social Media Adverse Event Module
│   │   ├── social_fetcher.py       # Fetch from Reddit/X
│   │   ├── social_cleaner.py       # Clean and normalize
│   │   ├── social_mapper.py        # Map to PV schema
│   │   ├── ml_classifier.py        # ML-based AE classification
│   │   ├── social_anonymizer.py    # PII anonymization
│   │   ├── social_storage.py       # Storage utilities
│   │   ├── social_ae_integration.py # Integration layer
│   │   ├── social_dashboard.py     # Dashboard UI
│   │   └── social_ae_scheduler.py  # Scheduled fetching
│   │
│   ├── core/                       # Core Processing Modules
│   │   ├── signal_stats.py         # PRR/ROR, statistical analysis
│   │   ├── nl_query_parser.py      # Natural language query parsing
│   │   ├── query_correction.py     # Query typo correction
│   │   ├── faers_loader.py         # FAERS file format loader
│   │   ├── pv_schema.py            # PV schema detection
│   │   ├── pv_storage.py           # Database storage/retrieval
│   │   ├── utils.py                # Utility functions
│   │   ├── case_processing.py      # Case processing logic
│   │   └── app_helpers.py          # Application helpers
│   │
│   ├── advanced/                   # Advanced Analysis Features
│   │   ├── quantum_ranking.py      # Quantum-inspired ranking
│   │   ├── quantum_clustering.py   # Quantum clustering
│   │   ├── quantum_anomaly.py      # Anomaly detection
│   │   ├── quantum_duplicate_detection.py # Duplicate detection
│   │   ├── quantum_explainability.py # Explainability
│   │   ├── longitudinal_spike.py   # Temporal spike detection
│   │   ├── time_to_onset.py        # Time-to-onset analysis
│   │   ├── class_effect_detection.py # Drug class effects
│   │   ├── subgroup_discovery.py   # Subgroup analysis
│   │   ├── signal_prioritization.py # Signal prioritization
│   │   ├── new_signal_detection.py # New signal detection
│   │   ├── advanced_stats.py       # Advanced statistics
│   │   └── cross_source_deduplication.py # Cross-source dedup
│   │
│   ├── normalization/              # Data Normalization
│   │   ├── drug_name_normalization.py # Drug name standardization
│   │   ├── exposure_normalization.py  # Exposure normalization
│   │   └── mapping_templates.py      # Mapping templates
│   │
│   ├── integration/                # External Integrations
│   │   ├── literature_integration.py # Literature APIs
│   │   ├── e2b_import.py           # E2B format import
│   │   ├── e2b_export.py           # E2B format export
│   │   └── analytics.py            # Analytics tracking
│   │
│   ├── reporting/                  # Reporting & Export
│   │   ├── pdf_report.py           # PDF report generation
│   │   └── audit_trail.py          # Audit logging
│   │
│   ├── watchlist_tab.py            # Drug watchlist feature
│   ├── styles.py                   # Global CSS styles
│   └── llm_explain.py              # LLM explanation utilities
│
├── database/                       # Database Schema
│   ├── schema.sql                  # Main schema (user_profiles, pv_cases)
│   └── schema_tenant_upgrade.sql   # Multi-tenant upgrades
│
├── api/                            # API Endpoints (if any)
│   └── social_api.py               # Social AE API
│
├── analytics/                      # Analytics Data
│   └── audit_log.jsonl             # Audit trail logs
│
└── .env                            # Environment variables (not in git)
```

---

## 🔄 Complete Data Flow

### **1. Application Startup Flow:**

```
app.py (Entry Point)
    ↓
Load .env file (dotenv)
    ↓
Restore authentication session (restore_session())
    ↓
Apply theme (apply_theme())
    ↓
Render top navigation (render_top_nav())
    ↓
User selects page (Streamlit navigation)
```

### **2. Authentication Flow:**

```
User visits Login/Register page
    ↓
Enter credentials
    ↓
Supabase Auth API call
    ↓
Email verification (if new user)
    ↓
Create/Update user profile (user_profiles table)
    ↓
Store session token (st.session_state.user_session)
    ↓
Redirect to protected page
```

### **3. Data Upload & Processing Flow:**

```
User uploads file (upload_section.py)
    ↓
Detect file type (CSV, Excel, ZIP, FAERS)
    ↓
Parse file (faers_loader.py or pandas)
    ↓
Schema detection (pv_schema.py)
    ↓
Column mapping (schema_mapper.py UI)
    ↓
Data normalization (drug_name_normalization.py, etc.)
    ↓
Store in session state (st.session_state.normalized_data)
    ↓
IF authenticated:
    ↓
    Store in Supabase (pv_storage.py)
    ↓
    Batch insert with user_id + organization
    ↓
    RLS automatically filters by user/company
```

### **4. Query Processing Flow (Current Implementation):**

```
User enters query (chat_interface.py or query_interface.py)
    ↓
Query correction (query_correction.py) - optional
    ↓
Hybrid Router (hybrid_router.py):
    ├─ Rule-based parser (nl_query_parser.py) ← Tries first
    └─ LLM interpreter (llm_interpreter.py) ← Fallback if enabled
    ↓
Extract filters (drug, reaction, age, date, etc.)
    ↓
Load data:
    ├─ IF in session: Use st.session_state.normalized_data
    └─ IF authenticated: Load from Supabase (pv_storage.py)
    ↓
Apply filters (signal_stats.apply_filters())
    ↓
Calculate statistics:
    ├─ Summary stats (get_summary_stats())
    ├─ PRR/ROR (calculate_prr_ror())
    ├─ Trends (longitudinal_spike.py)
    └─ Demographics (age, sex distribution)
    ↓
Generate response:
    ├─ Rule-based summary (conversational_engine.py)
    └─ LLM summary (signal_summarizer.py) - if enabled
    ↓
Display results (results_display.py):
    ├─ Chat interface (chat_interface.py) ← Shows AI response
    ├─ Overview tab (metrics, KPIs)
    ├─ Signals tab (PRR/ROR, charts)
    ├─ Trends tab (time series, spikes)
    ├─ Cases tab (data table)
    └─ Report tab (PDF download)
```

### **5. Database Interaction Flow:**

```
Supabase Connection (pv_storage.py)
    ↓
Authenticate with service_role key (for writes)
    OR anon key with user session (for reads)
    ↓
RLS Policies (database/schema.sql):
    ├─ Users can only see their organization's data
    ├─ Automatic filtering by user_id
    └─ Enforced at database level
    ↓
Query/Insert Operations:
    ├─ store_pv_data() → Batch insert with user_id + org
    ├─ load_pv_data() → SELECT with user_id filter
    └─ get_user_data_stats() → Aggregated stats per user
```

---

## 🧩 Component Architecture

### **Layer 1: UI Layer (Streamlit Components)**

**Purpose:** User interface rendering and interaction

**Key Files:**
- `app.py` - Application entry point
- `pages/*.py` - Multi-page navigation
- `src/ui/*.py` - Reusable UI components

**Responsibilities:**
- Render Streamlit UI elements
- Handle user input
- Manage session state (`st.session_state`)
- Display results and charts

**State Management:**
```python
# All state managed via Streamlit session state
st.session_state.normalized_data    # Current dataset
st.session_state.chat_history       # Chat conversation history
st.session_state.last_filters       # Last query filters
st.session_state.last_query_text    # Last query text
st.session_state.show_results       # Show results flag
st.session_state.user_session       # Supabase auth session
```

### **Layer 2: Business Logic Layer**

**Purpose:** Core application logic and data processing

**Key Modules:**

#### **A. Query Processing (`nl_query_parser.py`, `query_correction.py`)**
- Parse natural language queries
- Extract filters (drug, reaction, age, date, etc.)
- Typo correction and query suggestions
- Intent detection

#### **B. Statistical Analysis (`signal_stats.py`)**
- Filter data by criteria
- Calculate PRR/ROR with confidence intervals
- Summary statistics (counts, percentages)
- Demographic analysis
- Time trend analysis

#### **C. Data Processing (`faers_loader.py`, `case_processing.py`)**
- File parsing (FAERS, CSV, Excel)
- Data normalization
- Schema mapping
- Data cleaning

#### **D. Advanced Analytics (`quantum_*.py`, `longitudinal_spike.py`)**
- Quantum-inspired ranking
- Temporal spike detection
- Subgroup discovery
- Class effect detection

### **Layer 3: AI/LLM Layer**

**Purpose:** Natural language understanding and generation

**Key Components:**

#### **A. Hybrid Router (`hybrid_router.py`)**
```python
# Routes queries through rule-based first, LLM fallback
filters, method, confidence = route_query(
    query, normalized_df, use_llm=False
)
```

**Strategy:**
1. Try rule-based parser first (fast, deterministic)
2. If confidence < threshold AND use_llm=True → Try LLM
3. Return filters with method and confidence score

#### **B. Conversational Engine (`conversational_engine.py`)**
```python
# Processes query and generates response
result = process_conversational_query(
    query, normalized_df, use_llm=False
)
```

**Flow:**
1. Route query → Extract filters
2. Apply filters → Get filtered dataset
3. Calculate statistics
4. Generate natural language response (rule-based or LLM)

#### **C. LLM Integration (`medical_llm.py`, `llm_interpreter.py`)**
- Unified interface for multiple LLM providers (OpenAI, Claude, Groq)
- Query interpretation
- Response generation
- Error handling and fallbacks

### **Layer 4: Data Layer**

**Purpose:** Data persistence and retrieval

#### **A. Session Storage (In-Memory)**
- `st.session_state` - Temporary session data
- Cleared on page refresh (unless persisted)

#### **B. Database Storage (Supabase PostgreSQL)**
- **Tables:**
  - `user_profiles` - User accounts and organizations
  - `pv_cases` - Pharmacovigilance case data (multi-tenant)
  
- **Features:**
  - Row-Level Security (RLS) for multi-tenancy
  - Automatic data isolation by organization
  - Batch inserts for performance
  - User-scoped queries

#### **C. Storage Functions (`pv_storage.py`)**
```python
# Store data with user/company association
store_pv_data(df, user_id, organization, source)

# Load data filtered by user/company (RLS enforced)
load_pv_data(user_id, organization)

# Get statistics
get_user_data_stats(user_id, organization)
```

### **Layer 5: Integration Layer**

**Purpose:** External service integration

- **Supabase Auth** - Authentication
- **Supabase Database** - Data persistence
- **LLM APIs** - OpenAI, Anthropic, Groq
- **Social Media APIs** - Reddit, X (Twitter) - for Social AE module

---

## 🔐 Authentication & Authorization

### **Authentication Flow:**

1. **Registration:**
   ```
   User fills form → Supabase Auth API → Email verification
   → Create user_profiles record → Login
   ```

2. **Login:**
   ```
   User credentials → Supabase Auth API → Get session token
   → Store in st.session_state.user_session → Restore on page load
   ```

3. **Session Management:**
   - Session token stored in `st.session_state.user_session`
   - `restore_session()` called on every page load
   - Session persists across Streamlit page navigation

### **Authorization (Multi-Tenant):**

**Database-Level (RLS):**
```sql
-- Users can only see their organization's data
CREATE POLICY "Users can view own company data"
    ON pv_cases FOR SELECT
    USING (
        auth.uid() = user_id OR
        EXISTS (
            SELECT 1 FROM user_profiles
            WHERE user_profiles.id = auth.uid()
            AND user_profiles.organization = pv_cases.organization
        )
    );
```

**Application-Level:**
- Protected pages check `is_authenticated()` before rendering
- Database queries automatically filtered by RLS
- UI shows/hides features based on auth state

---

## 📊 Key Features & Capabilities

### **1. Natural Language Querying**
- Plain English queries ("Show me Dupixent conjunctivitis cases")
- Query correction and suggestions
- Hybrid parsing (rule-based + LLM)
- Multi-turn conversation support (chat interface)

### **2. Statistical Analysis**
- PRR/ROR with 95% confidence intervals
- Disproportionality analysis
- Time trend detection
- Spike detection
- Demographic analysis

### **3. ChatGPT-Like Interface**
- Conversational chat interface
- Streaming responses
- Progressive updates
- Multi-turn context
- Natural language responses

### **4. Data Management**
- Multi-format file support (FAERS, CSV, Excel, ZIP)
- Automatic schema detection
- Column mapping UI
- Data normalization
- Persistent storage (Supabase)

### **5. Advanced Features**
- Quantum-inspired ranking
- Signal prioritization
- Cross-source deduplication
- Class effect detection
- Subgroup discovery

### **6. Reporting**
- PDF report generation
- Exportable results
- Audit trail logging

---

## 🔄 Request/Response Flow Example

### **Example: User Query "Show me Dupixent conjunctivitis cases"**

```
1. User enters query in chat interface
   ↓
2. Chat interface calls on_send("Show me Dupixent conjunctivitis cases")
   ↓
3. Add user message to chat_history
   ↓
4. Show "thinking" indicator
   ↓
5. Query correction (if enabled):
   - Check for typos
   - Suggest corrections if needed
   ↓
6. Hybrid Router:
   - Rule-based parser extracts: drug="Dupixent", reaction="conjunctivitis"
   - Returns filters + confidence score
   ↓
7. Load data:
   - Check session state first
   - If authenticated: Load from Supabase with RLS filtering
   ↓
8. Apply filters:
   - Filter DataFrame: drug_name contains "Dupixent"
   - Filter DataFrame: reaction contains "conjunctivitis"
   ↓
9. Calculate statistics:
   - Matching cases: 1,234
   - Total cases: 438,512
   - Percentage: 0.28%
   - PRR/ROR (if drug+reaction both specified)
   - Time trends
   - Demographics
   ↓
10. Generate response:
    - Rule-based: Format statistics into natural language
    - OR LLM: Pass stats to LLM for natural language summary
    ↓
11. Update chat interface:
    - Replace "thinking" with final response
    - Store metadata (filters, stats) in message
    ↓
12. Display results:
    - Chat shows AI response
    - Results tabs show:
      - Overview: Metrics, KPIs
      - Signals: PRR/ROR charts
      - Trends: Time series
      - Cases: Data table
      - Report: PDF download
```

---

## 🎨 UI Architecture

### **Streamlit Multi-Page App:**

```
app.py (Landing Page)
├── pages/1_Quantum_PV_Explorer.py (Main PV Analysis)
│   ├── Sidebar: Filters, upload, settings
│   ├── Main Area: Tabs
│   │   ├── Upload Tab: File upload + schema mapping
│   │   ├── Natural Language Query Tab: Chat interface + query input
│   │   ├── Advanced Search Tab: Structured filters
│   │   └── Watchlist Tab: Drug watchlist
│   └── Results: Displayed below (when show_results=True)
│
├── pages/2_Social_AE_Explorer.py (Social Media AE)
│   └── Social media adverse event analysis
│
├── pages/Login.py (Authentication)
├── pages/Register.py (Registration)
└── pages/Profile.py (User Profile)
```

### **Component Hierarchy:**

```
Top Navigation (top_nav.py)
    ↓
Page Content (pages/*.py)
    ├── Sidebar (sidebar.py)
    │   ├── Filters
    │   ├── Upload Section
    │   └── Settings
    │
    └── Main Content
        ├── Upload Section (upload_section.py)
        ├── Query Interface (query_interface.py)
        │   └── Chat Interface (chat_interface.py) ← NEW
        ├── Results Display (results_display.py)
        └── Other Components
```

---

## 🗄️ Database Schema

### **user_profiles Table:**
```sql
- id (UUID, PK, FK to auth.users)
- email (text)
- organization (text)
- created_at (timestamp)
- updated_at (timestamp)
```

### **pv_cases Table:**
```sql
- id (UUID, PK)
- user_id (UUID, FK to auth.users)
- organization (text)
- drug_name (text)
- reaction (text)
- age (numeric)
- sex (text)
- country (text)
- serious (boolean)
- outcome (text)
- report_date (date)
- ... (other PV fields)
- raw_data (jsonb) - Original row data
- created_at (timestamp)
- updated_at (timestamp)
```

### **RLS Policies:**
- Users can only SELECT their organization's data
- Users can only INSERT with their user_id
- Users can only UPDATE/DELETE their own records

---

## 🔌 External Dependencies

### **APIs:**
- **Supabase Auth API** - Authentication
- **Supabase Database API** - Data persistence (PostgreSQL)
- **OpenAI API** - GPT-4o-mini
- **Anthropic API** - Claude
- **Groq API** - LLaMA-3 70B

### **Libraries:**
- **Streamlit** - UI framework
- **Pandas** - Data processing
- **NumPy/SciPy** - Statistical computing
- **Plotly** - Visualization
- **Supabase Python SDK** - Database client
- **rapidfuzz** - Fuzzy matching
- **PennyLane** - Quantum computing

---

## 🚀 Deployment Architecture

### **Current Deployment:**
- **Platform:** Streamlit Cloud (recommended)
- **Requirements:**
  - Python 3.12
  - Dependencies from requirements.txt
  - Environment variables in Streamlit Cloud dashboard

### **Alternative Deployments:**
- **Docker:** Dockerfile provided
- **Railway:** railway.json provided
- **Render:** render.yaml provided

### **Environment Variables:**
```env
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=xxx
SUPABASE_SERVICE_KEY=xxx
SUPABASE_DB_PASSWORD=xxx
OPENAI_API_KEY=xxx (optional)
ANTHROPIC_API_KEY=xxx (optional)
GROQ_API_KEY=xxx (optional)
```

---

## 📈 Performance Characteristics

### **Current Performance:**
- **File Upload:** 1-5 minutes for 100MB FAERS file
- **Query Processing:** 200-2000ms (rule-based) or 2-5s (with LLM)
- **Database Storage:** Batch inserts, ~1000 rows/second
- **Large Datasets:** Handles 500K+ rows in memory

### **Bottlenecks:**
- File parsing (pandas read operations)
- Large DataFrame operations
- Database batch inserts
- LLM API calls (if enabled)

### **Optimizations Applied:**
- Caching for unique values (drug/reaction lists)
- Batch database inserts
- Query correction caching
- Lazy loading of data

---

## 🔒 Security Architecture

### **Authentication:**
- Supabase Auth (industry standard)
- Email verification required
- Password hashing (handled by Supabase)

### **Authorization:**
- Row-Level Security (RLS) at database level
- Multi-tenant data isolation
- User-scoped queries

### **Data Privacy:**
- User data isolated by organization
- RLS policies prevent cross-tenant access
- Audit trail logging

---

## 📝 Key Design Decisions

### **1. Why Streamlit?**
- Rapid development
- Python-first (matches data science stack)
- Built-in components (tables, charts, file upload)
- Easy deployment (Streamlit Cloud)

### **2. Why Server-Side Processing?**
- No browser memory limitations
- Full pandas/NumPy/SciPy ecosystem
- Can handle large datasets (500K+ rows)
- Mature libraries and tools

### **3. Why Hybrid Router?**
- Rule-based is fast and deterministic
- LLM adds flexibility but is slower/costly
- User can choose based on needs
- Privacy option (rule-based only)

### **4. Why Supabase?**
- PostgreSQL (powerful, familiar)
- Built-in auth
- Row-Level Security (multi-tenant)
- Managed service (no infrastructure)

### **5. Why Session State + Database?**
- Session state for temporary/uploads
- Database for persistent/user data
- Allows both use cases (anonymous + authenticated)

---

## 🎯 Current Status

### **✅ Completed Features:**
- ✅ Full authentication system
- ✅ Multi-tenant database with RLS
- ✅ Natural language querying
- ✅ ChatGPT-like conversational interface
- ✅ Statistical analysis (PRR/ROR, trends)
- ✅ File upload and processing
- ✅ Results visualization
- ✅ PDF report generation
- ✅ Advanced analytics (quantum ranking, spike detection)
- ✅ Social media AE integration
- ✅ Query correction and suggestions

### **⚠️ Known Limitations:**
- File upload can be slow for very large files (>100MB)
- LLM features require API keys
- Session state lost on page refresh (unless using database)
- Browser must stay open during processing

### **🚀 Ready for:**
- Production deployment
- User testing
- Feature enhancements
- Performance optimization

---

## 📚 Additional Documentation

For more details, see:
- `PROJECT_SUMMARY_FOR_AI_REVIEW.md` - Project overview
- `CHATGPT_INTERFACE_ARCHITECTURE_EXPLANATION.md` - Chat interface details
- `ARCHITECTURE_SHIFT_ANALYSIS.md` - Analysis of alternative architectures
- `CHAT_INTERFACE_IMPLEMENTATION_COMPLETE.md` - Chat implementation details

---

## 🔄 Summary: How Everything Connects

```
User Browser
    ↓
Streamlit Server (Python)
    ├─ UI Layer (Streamlit components)
    ├─ Business Logic (pandas, NumPy, SciPy)
    ├─ AI Layer (LLM APIs)
    └─ Data Layer (Supabase)
        ↓
    PostgreSQL Database (RLS enforced)
```

**All processing happens server-side.**
**All state managed via Streamlit session state + Supabase database.**
**All UI rendered server-side via Streamlit's reactive framework.**

---

**Document Version:** 1.0  
**Last Updated:** November 2025  
**Status:** Current as of chat interface implementation completion

