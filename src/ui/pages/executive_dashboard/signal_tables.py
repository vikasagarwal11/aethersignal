"""
Top Signals Table Component - Executive Dashboard
Ranked signal table with sorting and filtering
"""

import streamlit as st
import pandas as pd


def render_top_signals_table():
    """
    Render the top signals ranking table.
    """
    st.markdown("### 🔍 Top Signals")
    
    # Try to get real data
    try:
        from executive_dashboard.aggregator import compute_top_signals
        
        signals = compute_top_signals(limit=20)
        
        if signals:
            df = pd.DataFrame(signals)
        else:
            raise ValueError("No signals data")
            
    except Exception:
        # Fallback to mock data
        df = pd.DataFrame({
            "Reaction": ["Nausea", "Vomiting", "Headache", "Hair Loss", "Fatigue"],
            "Count": [420, 310, 280, 112, 95],
            "Severity Score": [0.64, 0.72, 0.41, 0.15, 0.32],
            "Quantum Score": [0.84, 0.72, 0.51, 0.19, 0.38],
            "Novelty": ["No", "No", "Yes", "Yes", "No"],
            "Sources": ["FAERS, Social", "FAERS", "Social, Literature", "Social", "FAERS"]
        })
    
    # Add color coding for novelty
    def highlight_novel(row):
        if row["Novelty"] == "Yes":
            return ["background-color: #fef3c7"] * len(row)
        return [""] * len(row)
    
    # Display table
    st.dataframe(
        df.style.apply(highlight_novel, axis=1),
        use_container_width=True,
        hide_index=True,
        height=400
    )
    
    # Add download button
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download as CSV",
        data=csv,
        file_name="top_signals.csv",
        mime="text/csv"
    )

