"""
Executive Dashboard Visual Components - Phase 3J
Modular visual components for executive dashboard.
"""

from .tiles import render_kpi_tiles
from .trends import render_multi_source_trends
from .tables import render_signal_ranking_table
from .risk_matrix import render_severity_matrix
from .novelty import render_novelty_panel
from .geo import render_geographic_heatmap

__all__ = [
    "render_kpi_tiles",
    "render_multi_source_trends",
    "render_signal_ranking_table",
    "render_severity_matrix",
    "render_novelty_panel",
    "render_geographic_heatmap"
]

