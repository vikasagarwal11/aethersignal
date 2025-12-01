"""
Automated Benefit-Risk Visualizations Engine (CHUNK 6.21.1 - Part 21)
Generates regulatory-grade visualizations for benefit-risk assessment:
Forest plots, tornado sensitivity charts, LLR maps, and balance visualizations.
"""
import datetime
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    from .benefit_risk_engine import BenefitRiskEngine
    BENEFIT_RISK_AVAILABLE = True
except ImportError:
    BENEFIT_RISK_AVAILABLE = False


class BenefitRiskVisualizationEngine:
    """
    Generates regulatory-grade benefit-risk visualizations:
    - Forest plots (meta-analysis style)
    - Tornado sensitivity charts
    - LLR (Log-Likelihood Ratio) maps
    - Benefit-Risk balance visualizations
    - Probability of benefit/risk charts
    """

    def __init__(self):
        """Initialize the Benefit-Risk Visualization Engine."""
        if not PLOTLY_AVAILABLE:
            raise ImportError(
                "plotly is required for benefit-risk visualizations. "
                "Install it with: pip install plotly"
            )
        if BENEFIT_RISK_AVAILABLE:
            self.br_engine = BenefitRiskEngine()

    def generate_forest_plot(self, benefit_risk_data: Dict[str, Any],
                            outcome_type: str = "all") -> go.Figure:
        """
        Generate forest plot (meta-analysis style) for benefit-risk outcomes.
        
        Args:
            benefit_risk_data: Dictionary with benefit and risk outcomes
            outcome_type: "benefits", "risks", or "all"
            
        Returns:
            Plotly figure object
        """
        # Extract data for forest plot
        outcomes = []
        
        # Benefits
        if outcome_type in ["benefits", "all"]:
            benefits = benefit_risk_data.get("benefits", [])
            for benefit in benefits:
                outcomes.append({
                    "name": benefit.get("outcome", "Benefit"),
                    "type": "Benefit",
                    "effect_size": benefit.get("effect_size", benefit.get("relative_risk", 1.0)),
                    "ci_lower": benefit.get("ci_lower", benefit.get("ci_95_lower", 0.8)),
                    "ci_upper": benefit.get("ci_upper", benefit.get("ci_95_upper", 1.2)),
                    "weight": benefit.get("weight", benefit.get("sample_size", 100))
                })
        
        # Risks
        if outcome_type in ["risks", "all"]:
            risks = benefit_risk_data.get("risks", [])
            for risk in risks:
                outcomes.append({
                    "name": risk.get("outcome", "Risk"),
                    "type": "Risk",
                    "effect_size": risk.get("effect_size", risk.get("relative_risk", 1.0)),
                    "ci_lower": risk.get("ci_lower", risk.get("ci_95_lower", 0.8)),
                    "ci_upper": risk.get("ci_upper", risk.get("ci_95_upper", 1.2)),
                    "weight": risk.get("weight", risk.get("sample_size", 100))
                })
        
        if not outcomes:
            # Create default data for demonstration
            outcomes = [
                {"name": "Primary Efficacy", "type": "Benefit", "effect_size": 0.85, "ci_lower": 0.75, "ci_upper": 0.95, "weight": 100},
                {"name": "Secondary Efficacy", "type": "Benefit", "effect_size": 0.90, "ci_lower": 0.82, "ci_upper": 0.98, "weight": 80},
                {"name": "Serious AEs", "type": "Risk", "effect_size": 1.15, "ci_lower": 1.05, "ci_upper": 1.25, "weight": 120},
                {"name": "Discontinuations", "type": "Risk", "effect_size": 1.10, "ci_lower": 1.00, "ci_upper": 1.20, "weight": 100}
            ]
        
        df = pd.DataFrame(outcomes)
        
        # Create forest plot
        fig = go.Figure()
        
        # Add horizontal line at effect_size = 1.0 (no effect)
        fig.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="No Effect (1.0)")
        
        # Add outcomes
        y_positions = []
        for i, row in df.iterrows():
            y_pos = i
            y_positions.append(y_pos)
            
            color = "green" if row["type"] == "Benefit" else "red"
            
            # Add CI bars
            fig.add_trace(go.Scatter(
                x=[row["ci_lower"], row["ci_upper"]],
                y=[y_pos, y_pos],
                mode="lines",
                line=dict(width=3, color=color),
                showlegend=False,
                hoverinfo="x+text",
                text=f"95% CI: [{row['ci_lower']:.3f}, {row['ci_upper']:.3f}]"
            ))
            
            # Add point estimate
            fig.add_trace(go.Scatter(
                x=[row["effect_size"]],
                y=[y_pos],
                mode="markers",
                marker=dict(size=row["weight"]/10, color=color, line=dict(width=2, color="black")),
                name=row["type"],
                showlegend=(i == 0 or row["type"] not in [t["name"] for t in fig.data]),
                text=f"{row['name']}<br>Effect: {row['effect_size']:.3f}<br>95% CI: [{row['ci_lower']:.3f}, {row['ci_upper']:.3f}]",
                hoverinfo="text"
            ))
        
        # Update layout
        fig.update_layout(
            title="Benefit-Risk Forest Plot",
            xaxis_title="Effect Size (Relative Risk / Hazard Ratio)",
            yaxis_title="",
            yaxis=dict(
                tickmode="array",
                tickvals=y_positions,
                ticktext=df["name"].tolist(),
                autorange="reversed"
            ),
            xaxis=dict(range=[0.5, 2.0], type="log"),
            height=400 + len(outcomes) * 40,
            template="plotly_white",
            hovermode="closest"
        )
        
        return fig

    def generate_tornado_chart(self, sensitivity_data: Dict[str, Any],
                              base_scenario: str = "base_case") -> go.Figure:
        """
        Generate tornado sensitivity chart for benefit-risk parameters.
        
        Args:
            sensitivity_data: Dictionary with parameter sensitivity analysis
            base_scenario: Name of base case scenario
            
        Returns:
            Plotly figure object
        """
        # Extract sensitivity parameters
        parameters = sensitivity_data.get("parameters", [])
        
        if not parameters:
            # Create default data for demonstration
            parameters = [
                {"name": "Efficacy Weight", "low": 0.3, "high": 0.7, "base": 0.5},
                {"name": "Seriousness Weight", "low": 0.1, "high": 0.3, "base": 0.2},
                {"name": "Frequency Weight", "low": 0.2, "high": 0.6, "base": 0.4},
                {"name": "Duration Weight", "low": 0.1, "high": 0.4, "base": 0.25}
            ]
        
        # Calculate range for each parameter
        param_data = []
        for param in parameters:
            param_data.append({
                "name": param.get("name", "Parameter"),
                "low": param.get("low", param.get("min", 0)),
                "high": param.get("high", param.get("max", 1)),
                "base": param.get("base", param.get("baseline", 0.5)),
                "range": abs(param.get("high", 1) - param.get("low", 0))
            })
        
        # Sort by range (widest at top)
        param_data.sort(key=lambda x: x["range"], reverse=True)
        
        df = pd.DataFrame(param_data)
        
        # Create tornado chart
        fig = go.Figure()
        
        # Add bars for low and high
        fig.add_trace(go.Bar(
            y=df["name"],
            x=df["low"] - df["base"],
            base=df["base"],
            orientation="h",
            name="Low Sensitivity",
            marker_color="lightcoral",
            text=[f"{v:.3f}" for v in df["low"]],
            textposition="outside"
        ))
        
        fig.add_trace(go.Bar(
            y=df["name"],
            x=df["high"] - df["base"],
            base=df["base"],
            orientation="h",
            name="High Sensitivity",
            marker_color="lightblue",
            text=[f"{v:.3f}" for v in df["high"]],
            textposition="outside"
        ))
        
        # Update layout
        fig.update_layout(
            title="Tornado Sensitivity Analysis - Benefit-Risk Parameters",
            xaxis_title="Parameter Value",
            yaxis_title="Parameters",
            barmode="overlay",
            height=300 + len(parameters) * 50,
            template="plotly_white",
            hovermode="y unified"
        )
        
        return fig

    def generate_llr_map(self, benefit_risk_data: Dict[str, Any],
                        dimensions: Tuple[str, str] = ("benefit", "risk")) -> go.Figure:
        """
        Generate Log-Likelihood Ratio (LLR) map for benefit-risk visualization.
        
        Args:
            benefit_risk_data: Dictionary with benefit and risk metrics
            dimensions: Tuple of (x_dimension, y_dimension)
            
        Returns:
            Plotly figure object
        """
        # Extract benefit and risk metrics
        benefit_score = benefit_risk_data.get("benefit_score", benefit_risk_data.get("efficacy_score", 0.5))
        risk_score = benefit_risk_data.get("risk_score", benefit_risk_data.get("safety_score", 0.5))
        
        # Create grid for LLR map
        x_range = np.linspace(0, 1, 50)
        y_range = np.linspace(0, 1, 50)
        X, Y = np.meshgrid(x_range, y_range)
        
        # Calculate LLR values (example: distance from neutral point)
        Z = np.sqrt((X - benefit_score)**2 + (Y - risk_score)**2)
        
        # Create contour plot
        fig = go.Figure(data=go.Contour(
            x=x_range,
            y=y_range,
            z=Z,
            colorscale="RdYlGn",
            showscale=True,
            colorbar=dict(title="LLR Distance")
        ))
        
        # Add point for current benefit-risk position
        fig.add_trace(go.Scatter(
            x=[benefit_score],
            y=[risk_score],
            mode="markers+text",
            marker=dict(size=20, color="black", symbol="star"),
            text=["Current B/R Position"],
            textposition="top center",
            showlegend=False
        ))
        
        # Add regions
        fig.add_shape(
            type="rect",
            x0=0, y0=0, x1=0.5, y1=0.5,
            fillcolor="green",
            opacity=0.1,
            line=dict(color="green", dash="dash"),
            label=dict(text="Favorable")
        )
        
        fig.add_shape(
            type="rect",
            x0=0.5, y0=0.5, x1=1.0, y1=1.0,
            fillcolor="red",
            opacity=0.1,
            line=dict(color="red", dash="dash"),
            label=dict(text="Unfavorable")
        )
        
        # Update layout
        fig.update_layout(
            title="Log-Likelihood Ratio (LLR) Map - Benefit-Risk",
            xaxis_title=f"{dimensions[0].title()} Score",
            yaxis_title=f"{dimensions[1].title()} Score",
            width=700,
            height=600,
            template="plotly_white"
        )
        
        return fig

    def generate_benefit_risk_balance_chart(self, benefit_risk_data: Dict[str, Any]) -> go.Figure:
        """
        Generate benefit-risk balance visualization (scales/balance chart).
        
        Args:
            benefit_risk_data: Dictionary with benefit and risk metrics
            
        Returns:
            Plotly figure object
        """
        # Extract data
        benefits = benefit_risk_data.get("benefits", [])
        risks = benefit_risk_data.get("risks", [])
        
        # Calculate weighted totals
        benefit_total = sum(b.get("weight", b.get("importance", 1.0)) for b in benefits)
        risk_total = sum(r.get("weight", r.get("importance", 1.0)) for r in risks)
        
        # Normalize to 0-100 scale
        total = benefit_total + risk_total
        if total > 0:
            benefit_pct = (benefit_total / total) * 100
            risk_pct = (risk_total / total) * 100
        else:
            benefit_pct = 50
            risk_pct = 50
        
        # Create balance chart
        fig = go.Figure()
        
        # Add benefit bar (green)
        fig.add_trace(go.Bar(
            x=["Benefit"],
            y=[benefit_pct],
            name="Benefits",
            marker_color="green",
            text=f"{benefit_pct:.1f}%",
            textposition="outside",
            showlegend=True
        ))
        
        # Add risk bar (red)
        fig.add_trace(go.Bar(
            x=["Risk"],
            y=[risk_pct],
            name="Risks",
            marker_color="red",
            text=f"{risk_pct:.1f}%",
            textposition="outside",
            showlegend=True
        ))
        
        # Add balance indicator line
        fig.add_hline(y=50, line_dash="dash", line_color="gray", annotation_text="Neutral Balance")
        
        # Update layout
        fig.update_layout(
            title="Benefit-Risk Balance",
            yaxis_title="Weighted Score (%)",
            xaxis_title="",
            barmode="group",
            height=400,
            template="plotly_white",
            yaxis=dict(range=[0, 100])
        )
        
        return fig

    def generate_probability_chart(self, benefit_risk_data: Dict[str, Any]) -> go.Figure:
        """
        Generate probability of benefit vs risk chart.
        
        Args:
            benefit_risk_data: Dictionary with probability estimates
            
        Returns:
            Plotly figure object
        """
        # Extract probabilities
        prob_benefit = benefit_risk_data.get("prob_benefit", benefit_risk_data.get("probability_benefit", 0.6))
        prob_risk = benefit_risk_data.get("prob_risk", benefit_risk_data.get("probability_risk", 0.4))
        prob_neutral = 1.0 - prob_benefit - prob_risk
        
        # Create pie chart
        fig = go.Figure(data=[go.Pie(
            labels=["Benefit", "Risk", "Neutral"],
            values=[prob_benefit, prob_risk, max(0, prob_neutral)],
            hole=0.4,
            marker_colors=["green", "red", "gray"],
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>Probability: %{percent}<extra></extra>"
        )])
        
        fig.update_layout(
            title="Probability of Benefit vs Risk",
            height=500,
            template="plotly_white",
            annotations=[dict(
                text=f"B/R Ratio<br>{prob_benefit/prob_risk:.2f}" if prob_risk > 0 else "B/R Ratio<br>∞",
                x=0.5, y=0.5, font_size=16, showarrow=False
            )]
        )
        
        return fig

    def generate_comprehensive_br_dashboard(self, benefit_risk_data: Dict[str, Any]) -> List[go.Figure]:
        """
        Generate all benefit-risk visualizations as a dashboard.
        
        Args:
            benefit_risk_data: Complete benefit-risk assessment data
            
        Returns:
            List of Plotly figure objects
        """
        figures = []
        
        # 1. Forest plot
        figures.append(("Forest Plot", self.generate_forest_plot(benefit_risk_data)))
        
        # 2. Tornado chart (if sensitivity data available)
        if "sensitivity" in benefit_risk_data or "sensitivity_data" in benefit_risk_data:
            sensitivity_data = benefit_risk_data.get("sensitivity", benefit_risk_data.get("sensitivity_data", {}))
            figures.append(("Tornado Sensitivity", self.generate_tornado_chart(sensitivity_data)))
        
        # 3. LLR map
        figures.append(("LLR Map", self.generate_llr_map(benefit_risk_data)))
        
        # 4. Balance chart
        figures.append(("Balance Chart", self.generate_benefit_risk_balance_chart(benefit_risk_data)))
        
        # 5. Probability chart
        figures.append(("Probability Chart", self.generate_probability_chart(benefit_risk_data)))
        
        return figures

