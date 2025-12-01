"""
Executive Dashboard UI Components
"""

from .main import render_executive_dashboard
from .kpi_tiles import render_kpi_tiles
from .trends import render_trends
from .signal_tables import render_top_signals_table
from .heatmaps import render_severity_heatmap
from .novelty import render_novelty_panel
from .source_mix import render_source_mix
from .risk_matrix import render_risk_matrix
from .summaries import render_executive_summary

__all__ = [
    "render_executive_dashboard",
    "render_kpi_tiles",
    "render_trends",
    "render_top_signals_table",
    "render_severity_heatmap",
    "render_novelty_panel",
    "render_source_mix",
    "render_risk_matrix",
    "render_executive_summary"
]

