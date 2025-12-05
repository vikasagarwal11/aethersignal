"""
Drug Watchlist Tab - Daily Signal Monitor
The killer feature for safety teams: monitor multiple drugs simultaneously
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional
from src import signal_stats
from src import quantum_ranking


def _render_signal_details_panel(
    drug: str,
    reaction: str,
    row_data: pd.Series,
    normalized_df: pd.DataFrame,
    signals_df: pd.DataFrame
) -> None:
    """
    Render comprehensive signal details panel with all metrics, breakdowns, and case-level view.
    
    Args:
        drug: Drug name
        reaction: Reaction/adverse event name
        row_data: Row data from signals dataframe
        normalized_df: Full normalized dataset
        signals_df: DataFrame of all signals
    """
    st.markdown("---")
    st.markdown(f"#### 📊 Signal Details: **{drug}** → **{reaction}**")
    
    # Filter cases for this signal
    from src.utils import normalize_text
    
    drug_col = next((col for col in ["drug_name", "drug", "drug_concept_name"] if col in normalized_df.columns), None)
    reaction_col = next((col for col in ["reaction", "reaction_pt", "pt", "adverse_reaction", "event"] if col in normalized_df.columns), None)
    
    signal_df = None
    if drug_col and reaction_col:
        signal_df = normalized_df[
            (normalized_df[drug_col].astype(str).str.lower().str.contains(normalize_text(drug), na=False)) &
            (normalized_df[reaction_col].astype(str).str.lower().str.contains(normalize_text(reaction), na=False))
        ].copy()
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Classical Metrics",
        "⚛️ Quantum Breakdown",
        "📉 Trend Analysis",
        "👥 Demographics",
        "📝 Case-Level View"
    ])
    
    # TAB 1: Classical Metrics
    with tab1:
        st.markdown("### 📈 All Classical Statistical Metrics")
        
        # Calculate contingency table values
        if drug_col and reaction_col:
            drug_mask = normalized_df[drug_col].astype(str).str.lower().str.contains(normalize_text(drug), na=False)
            reaction_mask = normalized_df[reaction_col].astype(str).str.lower().str.contains(normalize_text(reaction), na=False)
            
            a = ((drug_mask) & (reaction_mask)).sum()
            b = ((drug_mask) & (~reaction_mask)).sum()
            c = ((~drug_mask) & (reaction_mask)).sum()
            d = ((~drug_mask) & (~reaction_mask)).sum()
            
            if a > 0:
                # Import advanced stats
                from src import advanced_stats
                
                # PRR/ROR (already calculated)
                prr = row_data.get('prr')
                ror = row_data.get('ror')
                prr_ci_lower = row_data.get('prr_ci_lower')
                prr_ci_upper = row_data.get('prr_ci_upper')
                
                # Calculate all other metrics
                ebgm = advanced_stats.calculate_ebgm(a, b, c, d)
                ic = advanced_stats.calculate_ic(a, b, c, d)
                bcpnn = advanced_stats.calculate_bcpnn(a, b, c, d)
                chi2_result = advanced_stats.chi_square_test(a, b, c, d)
                fisher_result = advanced_stats.fisher_exact_test(a, b, c, d)
                
                # Display metrics in organized sections
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### Disproportionality Measures")
                    
                    if prr is not None:
                        st.metric(
                            "PRR (Proportional Reporting Ratio)",
                            f"{prr:.2f}",
                            help="PRR > 2 suggests potential signal"
                        )
                        if prr_ci_lower is not None and prr_ci_upper is not None:
                            st.caption(f"95% CI: {prr_ci_lower:.2f} - {prr_ci_upper:.2f}")
                    
                    if ror is not None:
                        ror_ci_lower = row_data.get('ror_ci_lower')
                        ror_ci_upper = row_data.get('ror_ci_upper')
                        st.metric(
                            "ROR (Reporting Odds Ratio)",
                            f"{ror:.2f}",
                            help="ROR > 2 suggests potential signal"
                        )
                        if ror_ci_lower is not None and ror_ci_upper is not None:
                            st.caption(f"95% CI: {ror_ci_lower:.2f} - {ror_ci_upper:.2f}")
                    
                    if ebgm.get('ebgm'):
                        st.metric(
                            "EBGM (Empirical Bayes Geometric Mean)",
                            f"{ebgm['ebgm']:.2f}",
                            help="EBGM > 2 suggests potential signal. FDA standard for FAERS analysis."
                        )
                        st.caption(f"EB05: {ebgm.get('eb05', 0):.2f} | EB95: {ebgm.get('eb95', 0):.2f}")
                
                with col2:
                    st.markdown("#### Bayesian & Information Metrics")
                    
                    if ic.get('ic') is not None:
                        st.metric(
                            "IC (Information Component)",
                            f"{ic['ic']:.3f}",
                            help="IC > 0 = more reports than expected. IC > 2 = strong signal. WHO Vigibase standard."
                        )
                        st.caption(f"IC025: {ic.get('ic_025', 0):.3f} | IC975: {ic.get('ic_975', 0):.3f}")
                    
                    if bcpnn.get('ic') is not None:
                        st.metric(
                            "BCPNN (Bayesian Confidence Propagation Neural Network)",
                            f"{bcpnn['ic']:.3f}",
                            help="Bayesian method using neural network principles. Robust for rare events."
                        )
                        st.caption(f"IC025: {bcpnn.get('ic_025', 0):.3f} | IC975: {bcpnn.get('ic_975', 0):.3f}")
                
                st.markdown("---")
                st.markdown("#### Statistical Tests")
                
                col3, col4 = st.columns(2)
                
                with col3:
                    if chi2_result.get('chi2') is not None:
                        chi2_sig = "✅ Significant" if chi2_result.get('significant') else "❌ Not Significant"
                        st.metric(
                            "Chi-square Test",
                            f"{chi2_result['chi2']:.4f}",
                            help="Tests independence between drug and reaction. p < 0.05 = significant association."
                        )
                        st.caption(f"p-value: {chi2_result.get('p_value', 0):.6f} | {chi2_sig}")
                
                with col4:
                    if fisher_result.get('odds_ratio') is not None:
                        fisher_sig = "✅ Significant" if fisher_result.get('significant') else "❌ Not Significant"
                        st.metric(
                            "Fisher's Exact Test",
                            f"OR: {fisher_result['odds_ratio']:.4f}",
                            help="Exact probability test. Better for small datasets than chi-squared."
                        )
                        st.caption(f"p-value: {fisher_result.get('p_value', 0):.6f} | {fisher_sig}")
                
                # Contingency Table
                st.markdown("---")
                st.markdown("#### 2x2 Contingency Table")
                contingency_df = pd.DataFrame({
                    "": ["Has Drug", "No Drug"],
                    "Has Reaction": [int(a), int(c)],
                    "No Reaction": [int(b), int(d)]
                })
                contingency_df = contingency_df.set_index("")
                st.dataframe(contingency_df, use_container_width=True)
                
                # Interpretation
                st.markdown("---")
                st.markdown("#### 📝 Interpretation")
                
                interpretations = []
                if prr and prr >= 2.0:
                    interpretations.append(f"✅ **PRR ≥ 2.0** ({prr:.2f}) suggests potential safety signal")
                if ror and ror >= 2.0:
                    interpretations.append(f"✅ **ROR ≥ 2.0** ({ror:.2f}) confirms disproportionality")
                if ebgm.get('ebgm') and ebgm['ebgm'] >= 2.0:
                    interpretations.append(f"✅ **EBGM ≥ 2.0** ({ebgm['ebgm']:.2f}) indicates elevated risk (FDA standard)")
                if ic.get('ic') and ic['ic'] > 0:
                    interpretations.append(f"✅ **IC > 0** ({ic['ic']:.3f}) shows more reports than expected")
                if chi2_result.get('significant'):
                    interpretations.append(f"✅ **Chi-square test is significant** (p={chi2_result.get('p_value', 0):.4f}), indicating statistical association")
                if fisher_result.get('significant'):
                    interpretations.append(f"✅ **Fisher's exact test is significant** (p={fisher_result.get('p_value', 0):.4f})")
                
                if interpretations:
                    for interp in interpretations:
                        st.success(interp)
                else:
                    st.info("Classical metrics suggest this may be an expected association. Review quantum score for alternative signal detection.")
            else:
                st.warning("Could not calculate classical metrics - insufficient data.")
    
    # TAB 2: Quantum Breakdown
    with tab2:
        st.markdown("### ⚛️ Quantum Score Breakdown")
        
        quantum_score = row_data.get('quantum_score', 0)
        total_cases = len(normalized_df)
        
        st.metric("Quantum Score", f"{quantum_score:.4f}")
        
        # Get quantum explanation
        try:
            from src.quantum_explainability import explain_quantum_ranking
            
            signal_dict = {
                'drug': drug,
                'reaction': reaction,
                'count': row_data.get('count', 0),
                'quantum_score': quantum_score
            }
            
            explanation = explain_quantum_ranking(signal_dict, total_cases)
            
            if explanation:
                st.markdown("#### Component Breakdown")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    rarity = explanation.get('components', {}).get('rarity', {})
                    if rarity:
                        st.metric(
                            "Rarity (40%)",
                            f"{rarity.get('value', 0):.1%}",
                            f"{rarity.get('contribution', 0):.3f} pts"
                        )
                
                with col2:
                    seriousness = explanation.get('components', {}).get('seriousness', {})
                    if seriousness:
                        st.metric(
                            "Seriousness (35%)",
                            f"{seriousness.get('value', 0):.1%}",
                            f"{seriousness.get('contribution', 0):.3f} pts"
                        )
                
                with col3:
                    recency = explanation.get('components', {}).get('recency', {})
                    if recency:
                        st.metric(
                            "Recency (20%)",
                            f"{recency.get('value', 0):.1%}",
                            f"{recency.get('contribution', 0):.3f} pts"
                        )
                
                with col4:
                    interaction = explanation.get('interaction_score', 0)
                    st.metric(
                        "Interactions",
                        f"{interaction:.3f}",
                        "Quantum boosts"
                    )
                
                # Natural language explanation
                if explanation.get('explanation'):
                    st.markdown("---")
                    st.markdown("#### 💡 Explanation")
                    st.info(explanation['explanation'])
                
                # Interaction terms
                interactions = explanation.get('interactions', [])
                if interactions:
                    st.markdown("---")
                    st.markdown("#### 🔗 Quantum Interactions")
                    for inter in interactions:
                        st.caption(f"**{inter.get('type', '')}**: {inter.get('description', '')} (+{inter.get('contribution', 0):.3f})")
        except Exception as e:
            st.warning(f"Could not generate quantum breakdown: {str(e)}")
            st.info("Quantum score is based on: Rarity (40%), Seriousness (35%), Recency (20%), Count (5%), plus quantum interaction boosts.")
    
    # TAB 3: Trend Analysis
    with tab3:
        st.markdown("### 📉 Case Count Trend Over Time")
        
        if signal_df is not None and not signal_df.empty:
            # Try to extract date column
            date_col = next((col for col in ["event_date", "report_date", "date", "received_date", "onset_date"] if col in signal_df.columns), None)
            
            if date_col:
                try:
                    signal_df[date_col] = pd.to_datetime(signal_df[date_col], errors='coerce')
                    signal_df = signal_df.dropna(subset=[date_col])
                    
                    if not signal_df.empty:
                        # Monthly trend
                        signal_df["year_month"] = signal_df[date_col].dt.to_period("M").astype(str)
                        monthly_counts = signal_df.groupby("year_month").size().reset_index(name="count")
                        monthly_counts = monthly_counts.sort_values("year_month")
                        
                        try:
                            import plotly.express as px
                            fig = px.line(
                                monthly_counts,
                                x="year_month",
                                y="count",
                                title=f"Case Count Trend: {drug} → {reaction}",
                                markers=True
                            )
                            fig.update_layout(
                                xaxis_tickangle=-45,
                                height=400,
                                xaxis_title="Month",
                                yaxis_title="Number of Cases"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        except:
                            st.line_chart(monthly_counts.set_index("year_month"))
                        
                        # Summary stats
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Cases", len(signal_df))
                        with col2:
                            if 'seriousness' in signal_df.columns or 'serious' in signal_df.columns:
                                serious_col = 'seriousness' if 'seriousness' in signal_df.columns else 'serious'
                                serious_count = signal_df[serious_col].astype(str).str.lower().isin(["1", "yes", "y", "true", "serious"]).sum()
                                st.metric("Serious Cases", serious_count)
                            else:
                                st.metric("Serious Cases", "N/A")
                        with col3:
                            date_range = f"{signal_df[date_col].min().strftime('%Y-%m')} to {signal_df[date_col].max().strftime('%Y-%m')}"
                            st.metric("Date Range", date_range)
                        with col4:
                            latest_month = monthly_counts.iloc[-1]['count'] if len(monthly_counts) > 0 else 0
                            prev_month = monthly_counts.iloc[-2]['count'] if len(monthly_counts) > 1 else 0
                            delta = latest_month - prev_month if prev_month > 0 else 0
                            st.metric("Latest Month", int(latest_month), f"{delta:+}")
                    else:
                        st.warning("No valid dates found for trend analysis.")
                except Exception as e:
                    st.warning(f"Could not generate trend chart: {str(e)}")
            else:
                st.info("Date column not available for trend analysis.")
        else:
            st.info("No case data available for trend analysis.")
    
    # TAB 4: Demographics Breakdown
    with tab4:
        st.markdown("### 👥 Demographic & Clinical Breakdown")
        
        if signal_df is not None and not signal_df.empty:
            # Age breakdown
            if 'age' in signal_df.columns:
                st.markdown("#### Age Distribution")
                from src.utils import extract_age
                ages = signal_df['age'].apply(extract_age).dropna()
                if len(ages) > 0:
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Mean Age", f"{ages.mean():.1f} years")
                    with col2:
                        st.metric("Median Age", f"{ages.median():.1f} years")
                    with col3:
                        st.metric("Min Age", f"{ages.min():.1f} years")
                    with col4:
                        st.metric("Max Age", f"{ages.max():.1f} years")
            
            # Sex distribution
            if 'sex' in signal_df.columns:
                st.markdown("---")
                st.markdown("#### Sex Distribution")
                sex_dist = signal_df['sex'].value_counts()
                st.bar_chart(sex_dist)
            
            # Country distribution
            if 'country' in signal_df.columns:
                st.markdown("---")
                st.markdown("#### Country Distribution (Top 10)")
                country_dist = signal_df['country'].value_counts().head(10)
                st.dataframe(country_dist.reset_index(), use_container_width=True, hide_index=True)
            
            # Seriousness breakdown
            if 'seriousness' in signal_df.columns or 'serious' in signal_df.columns:
                st.markdown("---")
                st.markdown("#### Seriousness Breakdown")
                serious_col = 'seriousness' if 'seriousness' in signal_df.columns else 'serious'
                serious_count = signal_df[serious_col].astype(str).str.lower().isin(["1", "yes", "y", "true", "serious"]).sum()
                non_serious_count = len(signal_df) - serious_count
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Serious Cases", serious_count, f"{(serious_count/len(signal_df)*100):.1f}%")
                with col2:
                    st.metric("Non-Serious Cases", non_serious_count, f"{(non_serious_count/len(signal_df)*100):.1f}%")
        else:
            st.info("No case data available for demographic breakdown.")
    
    # TAB 5: Case-Level View
    with tab5:
        st.markdown("### 📝 Individual Case Details")
        
        if signal_df is not None and not signal_df.empty:
            st.info(f"Showing {len(signal_df)} cases for **{drug}** → **{reaction}**")
            
            # Display case table
            display_cols = []
            if 'case_id' in signal_df.columns:
                display_cols.append('case_id')
            if 'age' in signal_df.columns:
                display_cols.append('age')
            if 'sex' in signal_df.columns:
                display_cols.append('sex')
            if 'country' in signal_df.columns:
                display_cols.append('country')
            if 'seriousness' in signal_df.columns or 'serious' in signal_df.columns:
                display_cols.append(serious_col if 'serious_col' in locals() else 'seriousness' if 'seriousness' in signal_df.columns else 'serious')
            if 'outcome' in signal_df.columns:
                display_cols.append('outcome')
            
            if display_cols:
                available_cols = [col for col in display_cols if col in signal_df.columns]
                case_display = signal_df[available_cols].copy().head(100)  # Limit to first 100 for performance
                
                st.dataframe(
                    case_display,
                    use_container_width=True,
                    hide_index=True,
                    height=400
                )
                
                if len(signal_df) > 100:
                    st.caption(f"Showing first 100 of {len(signal_df)} total cases. Use filters to refine.")
            else:
                st.info("Case-level columns not available in this dataset.")
        else:
            st.info("No case data available for case-level view.")


def show_watchlist_tab():
    """
    Display the Drug Watchlist tab for monitoring multiple drugs simultaneously.
    Users can paste a list of drugs and get ranked emerging signals.
    """
    st.markdown("<div class='block-card'>", unsafe_allow_html=True)
    st.markdown("### 🔬 Drug Watchlist – Daily Signal Monitor")
    st.caption(
        "Paste your portfolio drugs (one per line) and get ranked emerging signals in <90 seconds. "
        "This feature scans all cases for each drug and ranks potential safety signals."
    )
    
    # Help section with expandable explanations
    with st.expander("ℹ️ How Drug Watchlist Works & What the Scores Mean", expanded=False):
        st.markdown("""
        #### **What is Drug Watchlist?**
        
        **Drug Watchlist = Automated Daily Surveillance System (Your "Daily Safety Radar")**
        
        Drug Watchlist monitors multiple drugs simultaneously and identifies emerging safety signals by:
        1. **Scanning all cases** for each drug in your portfolio across all uploaded data (FAERS/Argus/Veeva/E2B/etc.)
        2. **Identifying drug-event combinations** with at least 5 cases
        3. **Ranking signals** using quantum-inspired algorithms that favor rare, serious, and recent signals
        4. **Returning top priority risks** that you should review today
        
        ---
        
        #### **Understanding the Scores:**
        
        **📊 Quantum Score (0.0 - 1.0) - Core Innovation**
        
        A composite anomaly score informed by multiple factors:
        
        **Base Components (Weighted):**
        - **Rarity (40%)**: Rare events are more interesting than common ones
          - Formula: 1 - (count / total_cases)
          - Higher rarity = higher score
        - **Seriousness (35%)**: Serious adverse events get higher priority
          - Based on seriousness flags, outcomes (death, hospitalization, disability)
        - **Recency (20%)**: Recent cases are more relevant
          - Cases from last year get full weight
          - Older cases get diminishing weight
        - **Count (5%)**: Minimum threshold for statistical relevance
          - Normalized: min(1.0, count / 10.0)
        
        **Quantum-Inspired Enhancements:**
        - Bayesian priors, disproportionality shifts, novelty detection
        - Temporal spikes, cross-feature correlations
        - Local Outlier Factor, isolation models
        - Quantum-inspired ranking (eigenvector influence)
        
        **Non-linear Interaction Boosts:**
        - Rare + Serious = Critical signals (+0.15 boost)
        - Rare + Recent = Emerging signals (+0.10 boost)
        - Serious + Recent = Urgent signals (+0.10 boost)
        - All three = Highest priority signals (+0.20 boost)
        - Quantum tunneling: Small boost for signals "close" to thresholds
        
        **Interpretation:**
        - **0.70 - 1.0**: Very high priority (investigate immediately)
        - **0.55 - 0.70**: Elevated priority (investigate soon) - Score near 0.55 is already elevated
        - **0.40 - 0.55**: Moderate priority (monitor trends)
        - **0.30 - 0.40**: Lower priority (may be expected)
        - **0.0 - 0.30**: Low priority (likely expected)
        
        **🏆 Quantum Rank**
        - Position when signals are sorted by Quantum Score (highest to lowest)
        - Rank 1 = Highest priority signal (most concerning emerging signal)
        - Signals with same quantum score get same rank
        - This is your machine-prioritized short list of where to look
        
        **📈 Classical Rank**
        - Position when signals are sorted by case count only (most cases = rank 1)
        - Traditional ranking method (highest frequency first)
        - Compare with Quantum Rank to see which signals quantum ranking elevated
        
        **Differences are telling:**
        - **High Quantum Rank + Low Classical Rank** = Rare but serious emerging signal (investigate!)
        - **High Quantum Rank + Low Classical Rank** = Risk is newly emerging (classical methods are slow to detect early signals)
        - **Similar Ranks** = Signal is both common and serious (known issue)
        - **High Classical Rank + Low Quantum Rank** = Common but not rare/serious (may be expected)
        
        ---
        
        #### **Statistical Measures:**
        
        **PRR (Proportional Reporting Ratio)**
        - **Formula**: PRR = (a / (a+b)) / (c / (c+d))
        - **Interpretation**: PRR > 2 suggests potential signal
        - Standard disproportionality measure used in pharmacovigilance
        - Measures how often reaction is reported with drug vs. all other drugs
        
        **ROR (Reporting Odds Ratio)**
        - **Formula**: ROR = (a × d) / (b × c)
        - **Interpretation**: ROR > 2 suggests potential signal
        - Alternative disproportionality measure
        - Uses odds ratio instead of proportions
        
        **Additional Metrics (Available in Full Report):**
        - **EBGM**: Empirical Bayes Geometric Mean (FDA standard, handles sparse data)
        - **IC**: Information Component (WHO Vigibase, log2 ratio)
        - **BCPNN**: Bayesian Confidence Propagation Neural Network
        - **Chi-squared**: Statistical test for independence (p-value < 0.05 = significant)
        - **Fisher's Exact Test**: Exact probability test (better for small datasets)
        
        ---
        
        #### **How to Use:**
        
        **Decision Matrix:**
        - **Quantum Score > 0.70** = Investigate immediately
        - **Quantum Score 0.55-0.70** = Investigate soon
        - **High Quantum Rank + Low Classical Rank** = Rare but serious emerging signal (investigate!)
        - **Similar Ranks** = Signal is both common and serious (known issue)
        - **High Classical Rank + Low Quantum Rank** = Common but not rare/serious (may be expected)
        
        **Real-World Use:**
        - **Daily Monitoring**: Review top 20 quantum-ranked signals daily
        - **Safety Review Meetings**: Prioritize signals based on quantum rank
        - **Regulatory Documentation**: Include signals with quantum_score > 0.55 in PSUR/PBRER
        - **Early Detection**: Catch rare but serious AEs before classical methods
        
        ---
        
        #### **What Information is Shown:**
        
        - **Source Drug**: Drug name from your watchlist
        - **Reaction**: Adverse event/reaction reported (MedDRA PT or combinations)
        - **Count**: Number of cases with this drug-reaction combination (minimum 5 required)
        - **Quantum Score**: Composite priority score (0.0 - 1.0) - higher = more urgent
        - **Quantum Rank**: Ranking by quantum score (1 = highest priority)
        - **Classical Rank**: Ranking by case count (1 = most cases, traditional method)
        - **PRR/ROR**: Statistical disproportionality measures
        
        The table shows **top 50 signals** ranked by quantum score to help you focus on the most important emerging signals first.
        """)

    # Get default drugs from uploaded dataset (data-driven, no hardcoded values)
    default_drugs = ""
    if st.session_state.get("normalized_data") is not None:
        normalized_df = st.session_state.normalized_data
        if "drug_name" in normalized_df.columns and len(normalized_df) > 0:
            # Get top 6 most frequent drugs from uploaded data
            # Split by semicolon if drugs are stored as "Drug1; Drug2"
            drug_series = normalized_df["drug_name"].str.split("; ").explode()
            top_drugs = drug_series.value_counts().head(6).index.tolist()
            default_drugs = "\n".join(top_drugs)
    
    # Initialize session state with defaults if not already set
    if "watchlist_input" not in st.session_state or not st.session_state.watchlist_input:
        st.session_state.watchlist_input = default_drugs
    
    watchlist = st.text_area(
        "Your drugs (one per line)",
        value=st.session_state.watchlist_input if st.session_state.watchlist_input else default_drugs,
        height=180,
        key="watchlist_input",
        help="Enter drug names, one per line. Case-insensitive matching will be used. "
             "Defaults shown are the most frequent drugs from your uploaded dataset.",
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        run_watch = st.button(
            "🚀 Run Daily Signal Watch",
            type="primary",
            use_container_width=True,
            key="run_watchlist",
        )

    if run_watch:
        if st.session_state.get("normalized_data") is None:
            st.error("❌ Please upload and load data first in Step 1.")
            st.markdown("</div>", unsafe_allow_html=True)
            return

        drugs = [d.strip() for d in watchlist.split("\n") if d.strip()]
        if not drugs:
            st.error("❌ Enter at least one drug name.")
            st.markdown("</div>", unsafe_allow_html=True)
            return

        normalized_df = st.session_state.normalized_data
        with st.spinner(
            f"🔍 Scanning {len(normalized_df):,} cases for {len(drugs)} drug(s)..."
        ):
            candidates = []
            for drug in drugs:
                temp_filter = {"drug": drug}
                filtered = signal_stats.apply_filters(normalized_df, temp_filter)
                if not filtered.empty:
                    combos = signal_stats.get_drug_event_combinations(
                        filtered, min_cases=5
                    )
                    for c in combos:
                        c["source_drug"] = drug
                    candidates.extend(combos)

            if candidates:
                # OPTIMIZATION: Apply quantum ranking FIRST (doesn't need PRR/ROR)
                # This allows us to calculate PRR/ROR only for top 50 signals (lazy calculation)
                ranked = quantum_ranking.quantum_rerank_signals(candidates)
                df = pd.DataFrame(ranked).head(50)
                
                # LAZY CALCULATION: Calculate PRR/ROR only for top 50 signals after ranking
                # This is 2-4x faster than calculating for all candidates
                if len(df) > 0:
                    progress_bar = st.progress(0)
                    total_signals = len(df)
                    prr_ror_data = {}
                    
                    for idx, (row_idx, row) in enumerate(df.iterrows()):
                        drug_name = row.get('source_drug', '') or row.get('drug', '')
                        reaction_name = row.get('reaction', '')
                        
                        if drug_name and reaction_name:
                            prr_ror = signal_stats.calculate_prr_ror(
                                drug_name,
                                reaction_name,
                                normalized_df
                            )
                            if prr_ror:
                                prr_ror_data[row_idx] = {
                                    'prr': prr_ror.get('prr', None),
                                    'ror': prr_ror.get('ror', None),
                                    'prr_ci_lower': prr_ror.get('prr_ci_lower', None),
                                    'prr_ci_upper': prr_ror.get('prr_ci_upper', None),
                                }
                        
                        progress_bar.progress((idx + 1) / total_signals)
                    
                    # Update dataframe with PRR/ROR data
                    for row_idx, data in prr_ror_data.items():
                        df.at[row_idx, 'prr'] = data.get('prr')
                        df.at[row_idx, 'ror'] = data.get('ror')
                        df.at[row_idx, 'prr_ci_lower'] = data.get('prr_ci_lower')
                        df.at[row_idx, 'prr_ci_upper'] = data.get('prr_ci_upper')
                    
                    progress_bar.empty()
                
                # Add severity badge based on quantum_score
                def get_severity_badge(quantum_score: float) -> str:
                    """Return severity badge based on quantum score."""
                    if pd.isna(quantum_score):
                        return "⚪ Unknown"
                    if quantum_score >= 0.70:
                        return "🔴 High"
                    elif quantum_score >= 0.40:
                        return "🟡 Medium"
                    else:
                        return "🟢 Low"
                
                if 'quantum_score' in df.columns:
                    df['severity'] = df['quantum_score'].apply(get_severity_badge)

                st.success(
                    f"✅ Found {len(ranked)} potential signals → showing top 50 ranked by quantum score"
                )
                
                # Add column explanations
                st.markdown("""
                <div style='background: #f0f9ff; border-left: 4px solid #3b82f6; padding: 1rem; margin: 1rem 0; border-radius: 4px;'>
                    <strong>📊 Column Explanations:</strong>
                    <ul style='margin: 0.5rem 0; padding-left: 1.5rem;'>
                        <li><strong>Quantum Score:</strong> Composite priority score (0-1) favoring rare, serious, recent signals. Higher = higher priority.</li>
                        <li><strong>Quantum Rank:</strong> Ranking by Quantum Score (1 = highest priority).</li>
                        <li><strong>Classical Rank:</strong> Ranking by case count only (1 = most cases). Compare with Quantum Rank to see elevated signals.</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)

                # Display results with formatted columns
                display_cols = [
                    "source_drug",
                    "reaction",
                    "count",
                    "quantum_score",
                    "severity",  # Add severity badge after quantum_score
                    "quantum_rank",
                    "classical_rank",
                ]
                
                # Add PRR/ROR if available
                if 'prr' in df.columns:
                    display_cols.insert(3, "prr")  # Insert after count
                if 'ror' in df.columns:
                    display_cols.insert(4, "ror")  # Insert after prr
                # Only show columns that exist
                available_cols = [col for col in display_cols if col in df.columns]
                
                # Format dataframe for better display
                display_df = df[available_cols].copy()
                
                # Format quantum_score to 4 decimal places for readability
                if 'quantum_score' in display_df.columns:
                    display_df['quantum_score'] = display_df['quantum_score'].round(4)
                
                # Rename columns for better display
                column_rename = {
                    'source_drug': 'Drug',
                    'reaction': 'Reaction / Adverse Event',
                    'count': 'Case Count',
                    'severity': 'Severity',
                    'quantum_score': 'Quantum Score ⚛️',
                    'quantum_rank': 'Quantum Rank 🏆',
                    'classical_rank': 'Classical Rank 📈',
                    'prr': 'PRR',
                    'ror': 'ROR'
                }
                display_df = display_df.rename(columns=column_rename)
                
                # Build column config
                column_config = {
                    'Quantum Score ⚛️': st.column_config.NumberColumn(
                        'Quantum Score ⚛️',
                        help='Composite priority score (0-1). Higher = higher priority. Favors rare, serious, recent signals. Weighted: Rarity (40%), Seriousness (35%), Recency (20%), Count (5%).',
                        format='%.4f'
                    ),
                    'Quantum Rank 🏆': st.column_config.NumberColumn(
                        'Quantum Rank 🏆',
                        help='Ranking by Quantum Score (1 = highest priority signal). Compare with Classical Rank to see which signals quantum ranking elevated.',
                        format='%d'
                    ),
                    'Classical Rank 📈': st.column_config.NumberColumn(
                        'Classical Rank 📈',
                        help='Ranking by case count only (1 = most cases). Traditional ranking method. Compare with Quantum Rank to identify elevated signals.',
                        format='%d'
                    ),
                    'Case Count': st.column_config.NumberColumn(
                        'Case Count',
                        help='Number of cases with this drug-reaction combination. Minimum 5 cases required for signal detection.',
                        format='%d'
                    ),
                    'Severity': st.column_config.TextColumn(
                        'Severity',
                        help='Priority level based on Quantum Score: 🔴 High (≥0.70), 🟡 Medium (0.40-0.70), 🟢 Low (<0.40)'
                    ),
                }
                
                # Add PRR/ROR column configs if available
                if 'PRR' in display_df.columns:
                    column_config['PRR'] = st.column_config.NumberColumn(
                        'PRR',
                        help='Proportional Reporting Ratio - Measures disproportionality of drug-event combination. PRR > 2 suggests potential signal.',
                        format='%.2f'
                    )
                if 'ROR' in display_df.columns:
                    column_config['ROR'] = st.column_config.NumberColumn(
                        'ROR',
                        help='Reporting Odds Ratio - Alternative disproportionality measure. ROR > 2 suggests potential signal.',
                        format='%.2f'
                    )
                
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config=column_config
                )

                # Download button
                csv = df.to_csv(index=False)
                st.download_button(
                    "📄 Download Full Report",
                    csv,
                    f"aethersignal_watchlist_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    "text/csv",
                    use_container_width=True,
                )
                
                # PHASE 2: Row Selection & Signal Details Panel
                st.markdown("---")
                st.markdown("### 🔍 Signal Details Drill-Down")
                
                # Create signal selection dropdown
                signal_options = []
                signal_data_map = {}
                
                for idx, row in df.iterrows():
                    drug_name = row.get('source_drug', '') or row.get('drug', '')
                    reaction_name = row.get('reaction', '')
                    quantum_score = row.get('quantum_score', 0)
                    quantum_rank = row.get('quantum_rank', 0)
                    count = row.get('count', 0)
                    severity = row.get('severity', '')
                    
                    label = f"#{int(quantum_rank)} | {drug_name} → {reaction_name} | Count: {count} | Score: {quantum_score:.4f} | {severity}"
                    signal_options.append(label)
                    signal_data_map[label] = {
                        'index': idx,
                        'drug': drug_name,
                        'reaction': reaction_name,
                        'row_data': row
                    }
                
                if signal_options:
                    selected_signal = st.selectbox(
                        "Select a signal to view detailed analysis:",
                        options=["-- Select a signal --"] + signal_options,
                        key="watchlist_signal_selection",
                        help="Choose a signal from the table above to see detailed metrics, breakdowns, and case-level data."
                    )
                    
                    if selected_signal and selected_signal != "-- Select a signal --":
                        signal_info = signal_data_map[selected_signal]
                        _render_signal_details_panel(
                            signal_info['drug'],
                            signal_info['reaction'],
                            signal_info['row_data'],
                            normalized_df,
                            df
                        )

                # Track analytics
                if st.session_state.get("analytics_enabled"):
                    from src import analytics

                    analytics.log_event(
                        "watchlist_run",
                        {
                            "drug_count": len(drugs),
                            "signals_found": len(ranked),
                            "top_50_shown": len(df),
                        },
                    )
            else:
                st.info("ℹ️ No emerging signals found — all clear today! ✅")

    st.markdown("</div>", unsafe_allow_html=True)
