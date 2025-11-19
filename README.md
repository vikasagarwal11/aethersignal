# AetherSignal – Quantum PV Explorer

A session-based, no-login exploratory tool for pharmacovigilance (PV) teams to upload safety datasets and ask natural-language questions about drug–event patterns, with an optional "quantum-inspired" ranking mode.

## ⚠️ Important Disclaimer

**This is an exploratory tool only – not for regulatory decision-making.**

Spontaneous report data are subject to under-reporting and bias; no incidence or causality implied. This tool is designed for exploratory analysis and hypothesis generation only. It should not be used for regulatory submissions or clinical decision-making without proper validation and expert review.

## Features

- 📊 **Automatic Schema Detection**: Fuzzy column detection and mapping to standard PV fields (case_id, drug_name, reaction, age, sex, country, seriousness, onset_date, report_date, outcome, etc.)
- 💬 **Natural Language Queries**: Ask questions in plain English about your safety data
- 📈 **Signal Detection**: Calculate Proportional Reporting Ratio (PRR) and Reporting Odds Ratio (ROR) with 95% confidence intervals
- ⚛️ **Quantum-Inspired Ranking**: Advanced re-ranking using quantum simulators (PennyLane or NumPy-based)
- 📄 **PDF Reports**: Generate comprehensive one-page PDF summaries
- 🔍 **Advanced Search**: Structured filters for precise data exploration
- 📅 **Time Trend Analysis**: Visualize case trends over time
- 🔗 **Co-reaction Analysis**: Identify top co-occurring reactions

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

### Local Development

Run the Streamlit app:
```bash
streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`

### Streamlit Cloud

This application is compatible with Streamlit Cloud. To deploy:

1. Push your code to a GitHub repository
2. Connect your repository to Streamlit Cloud
3. Streamlit Cloud will automatically detect `requirements.txt` and deploy the app

## Usage

### 1. Upload Data

- Use the sidebar to upload safety datasets
- Supported formats: CSV, Excel (.xlsx, .xls), text files, or ZIP archives
- Multiple files can be uploaded simultaneously
- The system will automatically detect and map columns to standard PV fields

### 2. Query Your Data

#### Natural Language Queries

Type questions in plain English, such as:
- "Show all cases with drug aspirin and reaction headache"
- "Find serious cases for patients age 18-65"
- "Cases with drug ibuprofen and reaction nausea in United States"
- "Show all reactions for drug paracetamol since 2020"

#### Advanced Search

Use the sidebar for structured filtering:
- Drug name
- Reaction/event
- Age range
- Sex
- Country
- Seriousness flag
- Date range

### 3. View Results

The application displays:
- Matching case count and percentage
- PRR/ROR statistics (when drug and reaction are specified)
- Time trend charts
- Top drugs and reactions
- Co-occurring reactions
- Matching cases table (first 200 rows)

### 4. Quantum-Inspired Ranking

Enable quantum-inspired ranking from the sidebar to:
- Re-rank drug-event combinations using quantum simulators
- Compare classical vs quantum-inspired rankings
- View enhanced signal prioritization

### 5. Download Reports

Generate and download a one-page PDF summary containing:
- Query summary
- Statistics
- Signal detection metrics
- Top drugs and reactions
- Age statistics

## File Structure

```
aethersignal/
├── app.py                 # Main Streamlit application
├── pv_schema.py          # Schema detection and mapping
├── nl_query_parser.py    # Natural language query parser
├── signal_stats.py       # Statistics and PRR/ROR calculations
├── quantum_ranking.py    # Quantum-inspired ranking
├── pdf_report.py         # PDF report generation
├── utils.py              # Shared utility functions
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Technical Details

### Schema Detection

The system uses fuzzy matching to detect standard PV fields from various column naming conventions. Supported fields include:
- Case identifiers
- Drug names
- Reactions/adverse events
- Demographics (age, sex, country)
- Seriousness indicators
- Dates (onset, report)
- Outcomes

### Signal Detection

Proportional Reporting Ratio (PRR) and Reporting Odds Ratio (ROR) are calculated using 2x2 contingency tables:
- PRR = (a/(a+b)) / (c/(c+d))
- ROR = (a×d) / (b×c)

95% confidence intervals are calculated using log-normal approximation.

### Quantum-Inspired Ranking

The quantum ranking module uses:
- **PennyLane** (if available): Variational Quantum Eigensolver (VQE) and Quantum Approximate Optimization Algorithm (QAOA)
- **NumPy-based simulation**: Simulated annealing with quantum-inspired tunneling effects

Features extracted for ranking:
- Case count
- PRR and ROR values
- Confidence interval widths
- Statistical significance (p-values)

## Limitations

- **No External LLM APIs**: Natural language parsing uses regex and heuristics only
- **No Real Quantum Hardware**: Uses simulators only (PennyLane or NumPy)
- **Session-Based Only**: Data is stored in memory and cleared when session ends
- **No Login/Authentication**: Designed for exploratory use only
- **Limited to 200 Rows Display**: Large result sets are truncated in the UI (full data available via filtering)

## Dependencies

- `streamlit`: Web application framework
- `pandas`: Data manipulation and analysis
- `numpy`: Numerical computing
- `scipy`: Statistical functions
- `plotly`: Interactive visualizations
- `openpyxl`: Excel file support
- `fpdf2`: PDF generation
- `pennylane`: Quantum computing library (optional, falls back to NumPy if unavailable)

## Support

For issues, questions, or contributions, please refer to the project repository.

## License

This tool is provided as-is for exploratory pharmacovigilance analysis. Please ensure compliance with your organization's data handling and regulatory requirements before use.

---

**AetherSignal – Quantum PV Explorer**  
*Exploratory tool only – not for regulatory decision-making*

