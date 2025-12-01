"""
Causal Inference UI Panel (CHUNK 6.27 - Part E)
UI integration for causal inference engine in Trend Alerts and Signal File.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, Optional, List

try:
    from src.ai.causal_inference import CausalInferenceEngine, CausalResult
    from src.ai.causal_graph_builder import CausalGraphBuilder, build_causal_graph
    from src.ai.confounder_detector import ConfounderDetector, identify_confounders
    from src.ai.counterfactual_engine import CounterfactualEngine, simulate_counterfactual
    CAUSAL_AVAILABLE = True
except ImportError:
    CAUSAL_AVAILABLE = False


def render_causal_inference_panel(
    df: Optional[pd.DataFrame] = None,
    drug: Optional[str] = None,
    reaction: Optional[str] = None
) -> None:
    """
    Render causal inference analysis panel.
    
    Args:
        df: Safety data DataFrame
        drug: Drug name to analyze
        reaction: Reaction/event to analyze
    """
    st.header("🔬 Causal Inference Analysis")
    st.caption("FDA/EMA-grade causal analysis to determine if drug truly causes event")
    
    if not CAUSAL_AVAILABLE:
        st.error("Causal inference engines not available. Please install required dependencies.")
        return
    
    if df is None or df.empty:
        st.info("⚠️ Upload safety data to perform causal inference analysis.")
        return
    
    # Drug and reaction selection
    col1, col2 = st.columns(2)
    
    with col1:
        if drug:
            selected_drug = st.text_input("Drug Name", value=drug)
        else:
            # Try to extract from dataframe
            drug_col = _find_column(df, ["drug", "drug_name", "drug_normalized"])
            if drug_col:
                unique_drugs = df[drug_col].dropna().unique()[:20]
                selected_drug = st.selectbox("Select Drug", ["All"] + list(unique_drugs))
                if selected_drug == "All":
                    selected_drug = None
            else:
                selected_drug = st.text_input("Drug Name", placeholder="e.g., Dupixent")
    
    with col2:
        if reaction:
            selected_reaction = st.text_input("Reaction Name", value=reaction)
        else:
            reaction_col = _find_column(df, ["reaction", "reaction_pt", "reaction_normalized"])
            if reaction_col:
                unique_reactions = df[reaction_col].dropna().unique()[:20]
                selected_reaction = st.selectbox("Select Reaction", ["All"] + list(unique_reactions))
                if selected_reaction == "All":
                    selected_reaction = None
            else:
                selected_reaction = st.text_input("Reaction Name", placeholder="e.g., Pyrexia")
    
    if not selected_drug or not selected_reaction:
        st.info("Please select both drug and reaction to perform causal inference.")
        return
    
    # Run analysis
    if st.button("🔬 Run Causal Inference Analysis", type="primary"):
        with st.spinner("Running causal inference analysis..."):
            try:
                # 1. Core causal inference
                engine = CausalInferenceEngine()
                causal_result = engine.analyze(df, selected_drug, selected_reaction)
                
                # 2. Causal graph
                graph_builder = CausalGraphBuilder()
                causal_graph = graph_builder.build_graph(df, selected_drug, selected_reaction)
                
                # 3. Confounder detection
                confounder_detector = ConfounderDetector()
                confounders = identify_confounders(
                    df,
                    exposure=selected_drug,
                    outcome=selected_reaction
                )
                
                # 4. Counterfactual simulation
                counterfactual_engine = CounterfactualEngine()
                counterfactual_result = counterfactual_engine.simulate(
                    df, selected_drug, selected_reaction
                )
                
                # Store in session state
                st.session_state["causal_result"] = causal_result
                st.session_state["causal_graph"] = causal_graph
                st.session_state["confounders"] = confounders
                st.session_state["counterfactual_result"] = counterfactual_result
                
                st.success("✅ Causal inference analysis complete!")
                
            except Exception as e:
                st.error(f"Error running causal inference: {str(e)}")
                return
    
    # Display results
    if "causal_result" in st.session_state:
        _render_causal_results(
            st.session_state["causal_result"],
            st.session_state.get("causal_graph"),
            st.session_state.get("confounders", []),
            st.session_state.get("counterfactual_result")
        )


def _render_causal_results(
    causal_result: CausalResult,
    causal_graph: Optional[Any] = None,
    confounders: Optional[List[Any]] = None,
    counterfactual_result: Optional[Any] = None
) -> None:
    """Render causal inference results."""
    
    # Main causal score
    st.markdown("---")
    st.subheader("📊 Causal Score Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Causal score with color coding
        score = causal_result.causal_score
        if score >= 0.8:
            color = "🔴"
            level = "Very Strong"
        elif score >= 0.6:
            color = "🟠"
            level = "Strong"
        elif score >= 0.4:
            color = "🟡"
            level = "Moderate"
        else:
            color = "🟢"
            level = "Weak"
        
        st.metric(
            "Causal Score",
            f"{score:.2%}",
            delta=level,
            delta_color="normal"
        )
        st.caption(f"{color} Evidence Strength: {causal_result.evidence_strength}")
    
    with col2:
        st.metric(
            "Risk Difference",
            f"{causal_result.risk_difference:.2%}",
            delta=f"Risk Ratio: {causal_result.risk_ratio:.2f}"
        )
    
    with col3:
        st.metric(
            "Odds Ratio",
            f"{causal_result.odds_ratio:.2f}",
            delta=f"Methods: {len(causal_result.methods_used)}"
        )
    
    # Methods used
    st.markdown("---")
    st.subheader("🔧 Methods Used")
    methods_badges = " ".join([f"`{m}`" for m in causal_result.methods_used])
    st.markdown(methods_badges)
    
    # Confidence interval
    if causal_result.confidence_interval:
        ci_lower, ci_upper = causal_result.confidence_interval
        st.info(
            f"**95% Confidence Interval:** [{ci_lower:.3f}, {ci_upper:.3f}]\n\n"
            f"This interval {'excludes zero' if ci_lower > 0 or ci_upper < 0 else 'includes zero'}, "
            f"suggesting {'statistically significant' if ci_lower > 0 else 'inconclusive'} causal effect."
        )
    
    # Key drivers
    if causal_result.drivers:
        st.markdown("---")
        st.subheader("🎯 Key Drivers")
        for driver in causal_result.drivers:
            st.markdown(f"- {driver}")
    
    # Confounders
    if confounders:
        st.markdown("---")
        st.subheader("⚠️ Confounders Identified")
        conf_df = pd.DataFrame([
            {
                "Variable": c.variable,
                "Type": c.variable_type,
                "Strength": f"{c.strength:.2%}",
                "Adjustment Recommended": "Yes" if c.adjustment_recommended else "No"
            }
            for c in confounders[:10]
        ])
        st.dataframe(conf_df, use_container_width=True)
    
    # Counterfactual analysis
    if counterfactual_result:
        st.markdown("---")
        st.subheader("🔮 Counterfactual Analysis")
        st.markdown(
            f"""
            **"What if patients had NOT taken the drug?"**
            
            - **Actual Risk (with drug):** {counterfactual_result.actual_risk:.2%}
            - **Counterfactual Risk (without drug):** {counterfactual_result.counterfactual_risk:.2%}
            - **Causal Effect:** {counterfactual_result.risk_difference:.2%} (Risk difference)
            - **Risk Ratio:** {counterfactual_result.risk_ratio:.2f}
            """
        )
        
        # Visualize counterfactual
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=["With Drug", "Without Drug (Counterfactual)"],
            y=[counterfactual_result.actual_risk, counterfactual_result.counterfactual_risk],
            marker_color=["#ef4444", "#3b82f6"],
            text=[f"{counterfactual_result.actual_risk:.2%}", 
                  f"{counterfactual_result.counterfactual_risk:.2%}"],
            textposition="auto"
        ))
        fig.update_layout(
            title="Counterfactual Risk Comparison",
            yaxis_title="Risk",
            yaxis=dict(tickformat=".0%"),
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Causal graph visualization
    if causal_graph and hasattr(causal_graph, 'edges') and len(causal_graph.edges) > 0:
        st.markdown("---")
        st.subheader("🕸️ Causal Graph")
        st.caption("Visual representation of causal relationships")
        
        # Simple graph visualization
        nodes = causal_graph.nodes
        edges = causal_graph.edges
        
        graph_data = {
            "nodes": [{"id": n, "label": n.replace("_", " ")} for n in nodes],
            "edges": [
                {
                    "from": e.source,
                    "to": e.target,
                    "label": f"{e.strength:.2f}",
                    "type": e.edge_type
                }
                for e in edges[:20]  # Limit to 20 edges
            ]
        }
        
        # Create network graph visualization
        st.json(graph_data)
        st.info("💡 Graph shows causal relationships. Stronger edges (higher values) indicate stronger causal links.")


def _find_column(df: pd.DataFrame, candidates: list) -> Optional[str]:
    """Find column in DataFrame."""
    for candidate in candidates:
        if candidate in df.columns:
            return candidate
    return None


def render_causal_summary_card(causal_result: CausalResult) -> None:
    """Render a compact causal summary card for embedding in other panels."""
    if causal_result.causal_score >= 0.6:
        st.success(
            f"🔬 **Causal Evidence:** {causal_result.evidence_strength} "
            f"(Score: {causal_result.causal_score:.2%})"
        )
    elif causal_result.causal_score >= 0.4:
        st.warning(
            f"🔬 **Causal Evidence:** {causal_result.evidence_strength} "
            f"(Score: {causal_result.causal_score:.2%})"
        )
    else:
        st.info(
            f"🔬 **Causal Evidence:** {causal_result.evidence_strength} "
            f"(Score: {causal_result.causal_score:.2%})"
        )

