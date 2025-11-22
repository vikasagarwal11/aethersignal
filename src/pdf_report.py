"""
PDF Report Generation for AetherSignal
Creates one-page PDF summaries using fpdf2 with enhanced visualizations.
"""

from fpdf import FPDF
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import io
import math


def _draw_signal_strength_bar(pdf: FPDF, x: float, y: float, width: float, height: float, 
                               value: float, max_value: float = 10.0) -> None:
    """
    Draw a signal strength meter bar with traffic light colors.
    
    Args:
        pdf: FPDF instance
        x, y: Position
        width: Bar width
        height: Bar height
        value: Signal strength value
        max_value: Maximum value for scaling
    """
    # Normalize value to 0-1 range
    normalized = min(value / max_value, 1.0)
    bar_width = width * normalized
    
    # Traffic light colors: green (low) -> yellow -> orange -> red (high)
    if value < 2.0:
        color = (34, 197, 94)  # Green
    elif value < 4.0:
        color = (234, 179, 8)  # Yellow
    elif value < 6.0:
        color = (249, 115, 22)  # Orange
    else:
        color = (239, 68, 68)  # Red
    
    # Draw background (gray)
    pdf.set_fill_color(226, 232, 240)
    pdf.rect(x, y, width, height, 'F')
    
    # Draw filled portion
    pdf.set_fill_color(*color)
    pdf.rect(x, y, bar_width, height, 'F')
    
    # Draw border
    pdf.set_draw_color(203, 213, 225)
    pdf.rect(x, y, width, height, 'D')


def _draw_table_row(pdf: FPDF, x: float, y: float, width: float, height: float,
                    cells: List[Tuple[str, float]], header: bool = False) -> None:
    """
    Draw a table row with multiple cells.
    
    Args:
        pdf: FPDF instance
        x, y: Starting position
        width: Total row width
        height: Row height
        cells: List of (text, relative_width) tuples
        header: Whether this is a header row
    """
    if header:
        pdf.set_fill_color(241, 245, 249)
        pdf.set_text_color(15, 23, 42)
        pdf.set_font('Arial', 'B', 9)
    else:
        pdf.set_fill_color(255, 255, 255)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Arial', '', 9)
    
    # Draw row background
    pdf.rect(x, y, width, height, 'F')
    
    # Draw cells
    current_x = x
    for text, rel_width in cells:
        cell_width = width * rel_width
        pdf.set_xy(current_x + 2, y + height / 2 - 2)
        pdf.cell(cell_width - 4, height, text, 0, 0, 'L')
        current_x += cell_width
    
    # Draw borders
    pdf.set_draw_color(226, 232, 240)
    pdf.rect(x, y, width, height, 'D')
    # Vertical dividers
    current_x = x
    for i, (_, rel_width) in enumerate(cells):
        if i > 0:
            pdf.line(current_x, y, current_x, y + height)
        current_x += width * rel_width


def build_pdf_report(summary_dict: Dict) -> bytes:
    """
    Build a one-page PDF summary report with enhanced visualizations.
    
    Args:
        summary_dict: Dictionary containing:
            - query: Original query string
            - filters: Applied filters
            - total_cases: Total number of cases
            - matching_cases: Number of matching cases
            - percentage: Percentage of total
            - prr_ror: PRR/ROR statistics (if available)
            - top_drugs: Top drugs dictionary
            - top_reactions: Top reactions dictionary
            - age_stats: Age statistics
            - sex_distribution: Sex distribution
            - serious_count: Number of serious cases
            - time_trend: Time trend data (optional)
            - generated_at: Timestamp (optional)
    
    Returns:
        PDF file as bytes
    """
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Brand colors: Enterprise blue + slate
    primary_blue = (30, 64, 175)  # #1e40af
    secondary_blue = (37, 99, 235)  # #2563eb
    light_blue = (191, 219, 254)  # #bfdbfe
    slate_gray = (148, 163, 184)  # #94a3b8
    dark_slate = (15, 23, 42)  # #0f172a
    gray_color = (100, 116, 139)  # #64748b
    
    # Header with gradient effect
    pdf.set_fill_color(*primary_blue)
    pdf.rect(0, 0, 210, 32, 'F')
    
    # Subtle gradient overlay
    pdf.set_fill_color(*secondary_blue)
    pdf.rect(0, 0, 210, 8, 'F')
    
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Arial', 'B', 22)
    pdf.set_xy(10, 10)
    pdf.cell(0, 10, 'AetherSignal - Quantum PV Explorer', 0, 1, 'L')
    
    pdf.set_font('Arial', '', 9)
    pdf.set_xy(10, 22)
    generated_at = summary_dict.get('generated_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    pdf.cell(0, 5, f'Report Generated: {generated_at}', 0, 1, 'L')
    
    # Disclaimer box
    pdf.set_fill_color(255, 249, 230)  # Light yellow background
    pdf.set_draw_color(246, 173, 85)  # Orange border
    pdf.rect(10, 36, 190, 8, 'FD')
    pdf.set_text_color(116, 66, 16)  # Dark brown text
    pdf.set_font('Arial', 'I', 7)
    pdf.set_xy(12, 38)
    pdf.multi_cell(186, 3, 
                   'DISCLAIMER: Exploratory tool only - not for regulatory decision-making. '
                   'Spontaneous report data are subject to under-reporting and bias; '
                   'no incidence or causality implied.', 0, 'L')
    
    # Reset text color
    pdf.set_text_color(*dark_slate)
    
    y_pos = 48
    
    # Executive Summary Section (Enhanced)
    pdf.set_fill_color(241, 245, 249)
    pdf.rect(10, y_pos, 190, 25, 'F')
    pdf.set_draw_color(*slate_gray)
    pdf.rect(10, y_pos, 190, 25, 'D')
    
    pdf.set_text_color(*primary_blue)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_xy(12, y_pos + 3)
    pdf.cell(0, 6, 'Executive Summary', 0, 1, 'L')
    
    pdf.set_text_color(*dark_slate)
    pdf.set_font('Arial', '', 9)
    
    total_cases = summary_dict.get('total_cases', 0)
    matching_cases = summary_dict.get('matching_cases', 0)
    percentage = summary_dict.get('percentage', 0.0)
    serious_count = summary_dict.get('serious_count', 0)
    serious_pct = summary_dict.get('serious_percentage', 0.0)
    
    # Key metrics in summary box
    pdf.set_xy(12, y_pos + 10)
    pdf.cell(90, 4, f'Total Cases Analyzed: {total_cases:,}', 0, 0, 'L')
    pdf.set_xy(102, y_pos + 10)
    pdf.cell(90, 4, f'Matching Cases: {matching_cases:,} ({percentage:.1f}%)', 0, 1, 'L')
    
    pdf.set_xy(12, y_pos + 15)
    pdf.cell(90, 4, f'Serious Cases: {serious_count:,} ({serious_pct:.1f}%)', 0, 0, 'L')
    
    # Signal detection highlight
    prr_ror = summary_dict.get('prr_ror')
    if prr_ror:
        prr = prr_ror.get('prr', 0)
        pdf.set_xy(102, y_pos + 15)
        signal_level = "High" if prr >= 2.0 else "Moderate" if prr >= 1.5 else "Low"
        pdf.cell(90, 4, f'Signal Level: {signal_level} (PRR: {prr:.2f})', 0, 1, 'L')
    
    y_pos += 30
    
    # Query Section
    pdf.set_font('Arial', 'B', 11)
    pdf.set_xy(10, y_pos)
    pdf.cell(0, 6, 'Query Details', 0, 1, 'L')
    
    pdf.set_font('Arial', '', 9)
    pdf.set_xy(10, y_pos + 6)
    query = summary_dict.get('query', 'N/A')
    # Truncate long queries
    if len(query) > 120:
        query = query[:117] + "..."
    pdf.multi_cell(190, 4, f'Query: {query}', 0, 'L')
    
    y_pos += 15
    
    # Statistics Section
    pdf.set_font('Arial', 'B', 12)
    pdf.set_xy(10, y_pos)
    pdf.cell(0, 8, 'Statistics', 0, 1, 'L')
    
    pdf.set_font('Arial', '', 10)
    y_pos += 10
    
    total_cases = summary_dict.get('total_cases', 0)
    matching_cases = summary_dict.get('matching_cases', 0)
    percentage = summary_dict.get('percentage', 0.0)
    
    pdf.set_xy(10, y_pos)
    pdf.cell(0, 5, f'Total Cases: {total_cases:,}', 0, 1, 'L')
    
    pdf.set_xy(10, y_pos + 5)
    pdf.cell(0, 5, f'Matching Cases: {matching_cases:,} ({percentage:.2f}%)', 0, 1, 'L')
    
    serious_count = summary_dict.get('serious_count', 0)
    serious_pct = summary_dict.get('serious_percentage', 0.0)
    pdf.set_xy(10, y_pos + 10)
    pdf.cell(0, 5, f'Serious Cases: {serious_count:,} ({serious_pct:.2f}%)', 0, 1, 'L')
    
    y_pos += 25
    
    # PRR/ROR Section with Signal Strength Meter (if available)
    prr_ror = summary_dict.get('prr_ror')
    if prr_ror:
        # Section header with background
        pdf.set_fill_color(241, 245, 249)
        pdf.rect(10, y_pos, 190, 8, 'F')
        pdf.set_text_color(*primary_blue)
        pdf.set_font('Arial', 'B', 12)
        pdf.set_xy(12, y_pos + 2)
        pdf.cell(0, 6, 'Signal Detection Metrics', 0, 1, 'L')
        y_pos += 10
        
        drug = prr_ror.get('drug', 'N/A')
        reaction = prr_ror.get('reaction', 'N/A')
        pdf.set_text_color(*dark_slate)
        pdf.set_font('Arial', 'B', 9)
        pdf.set_xy(10, y_pos)
        pdf.cell(0, 5, f'Drug: {drug}', 0, 1, 'L')
        pdf.set_xy(10, y_pos + 5)
        pdf.cell(0, 5, f'Reaction: {reaction}', 0, 1, 'L')
        y_pos += 12
        
        # PRR/ROR Table
        table_y = y_pos
        _draw_table_row(pdf, 10, table_y, 190, 7, [
            ('Metric', 0.25),
            ('Value', 0.25),
            ('95% CI Lower', 0.25),
            ('95% CI Upper', 0.25)
        ], header=True)
        
        prr = prr_ror.get('prr', 0)
        prr_ci_lower = prr_ror.get('prr_ci_lower', 0)
        prr_ci_upper = prr_ror.get('prr_ci_upper', 0)
        _draw_table_row(pdf, 10, table_y + 7, 190, 6, [
            ('PRR', 0.25),
            (f'{prr:.2f}', 0.25),
            (f'{prr_ci_lower:.2f}', 0.25),
            (f'{prr_ci_upper:.2f}', 0.25)
        ], header=False)
        
        ror = prr_ror.get('ror', 0)
        ror_ci_lower = prr_ror.get('ror_ci_lower', 0)
        ror_ci_upper = prr_ror.get('ror_ci_upper', 0)
        _draw_table_row(pdf, 10, table_y + 13, 190, 6, [
            ('ROR', 0.25),
            (f'{ror:.2f}', 0.25),
            (f'{ror_ci_lower:.2f}', 0.25),
            (f'{ror_ci_upper:.2f}', 0.25)
        ], header=False)
        
        y_pos = table_y + 22
        
        # Signal Strength Meters
        pdf.set_font('Arial', 'B', 9)
        pdf.set_text_color(*dark_slate)
        pdf.set_xy(10, y_pos)
        pdf.cell(0, 5, 'Signal Strength:', 0, 1, 'L')
        y_pos += 7
        
        # PRR Signal Strength
        pdf.set_font('Arial', '', 8)
        pdf.set_xy(10, y_pos)
        pdf.cell(40, 4, 'PRR Signal:', 0, 0, 'L')
        _draw_signal_strength_bar(pdf, 50, y_pos, 60, 4, prr, max_value=10.0)
        pdf.set_xy(112, y_pos)
        pdf.set_font('Arial', 'B', 8)
        pdf.cell(0, 4, f'{prr:.2f}', 0, 1, 'L')
        y_pos += 7
        
        # ROR Signal Strength
        pdf.set_font('Arial', '', 8)
        pdf.set_xy(10, y_pos)
        pdf.cell(40, 4, 'ROR Signal:', 0, 0, 'L')
        _draw_signal_strength_bar(pdf, 50, y_pos, 60, 4, ror, max_value=10.0)
        pdf.set_xy(112, y_pos)
        pdf.set_font('Arial', 'B', 8)
        pdf.cell(0, 4, f'{ror:.2f}', 0, 1, 'L')
        y_pos += 5
        
        p_value = prr_ror.get('p_value')
        if p_value:
            pdf.set_font('Arial', '', 8)
            pdf.set_xy(10, y_pos)
            significance = "***" if p_value < 0.001 else "**" if p_value < 0.01 else "*" if p_value < 0.05 else "ns"
            pdf.cell(0, 4, f'P-value: {p_value:.4f} ({significance})', 0, 1, 'L')
            y_pos += 5
        
        y_pos += 3
    
    # Top Drugs Section
    top_drugs = summary_dict.get('top_drugs', {})
    if top_drugs:
        pdf.set_font('Arial', 'B', 12)
        pdf.set_xy(10, y_pos)
        pdf.cell(0, 8, 'Top Drugs', 0, 1, 'L')
        
        pdf.set_font('Arial', '', 9)
        y_pos += 10
        
        for i, (drug, count) in enumerate(list(top_drugs.items())[:5]):
            if y_pos > 250:  # Prevent overflow
                break
            pdf.set_xy(15, y_pos)
            pdf.cell(0, 5, f'{i+1}. {drug}: {count:,}', 0, 1, 'L')
            y_pos += 6
        
        y_pos += 5
    
    # Top Reactions Section
    top_reactions = summary_dict.get('top_reactions', {})
    if top_reactions:
        pdf.set_font('Arial', 'B', 12)
        pdf.set_xy(110, y_pos - (len(list(top_drugs.items())[:5]) * 6 + 15) if top_drugs else 0)
        pdf.cell(0, 8, 'Top Reactions', 0, 1, 'L')
        
        pdf.set_font('Arial', '', 9)
        y_start = y_pos - (len(list(top_drugs.items())[:5]) * 6) if top_drugs else y_pos
        y_pos = y_start + 10
        
        for i, (reaction, count) in enumerate(list(top_reactions.items())[:5]):
            if y_pos > 250:
                break
            pdf.set_xy(115, y_pos)
            pdf.cell(0, 5, f'{i+1}. {reaction}: {count:,}', 0, 1, 'L')
            y_pos += 6
    
    # Age Statistics
    age_stats = summary_dict.get('age_stats', {})
    if age_stats and any(age_stats.values()):
        y_pos = max(y_pos, 180)
        pdf.set_font('Arial', 'B', 12)
        pdf.set_xy(10, y_pos)
        pdf.cell(0, 8, 'Age Statistics', 0, 1, 'L')
        
        pdf.set_font('Arial', '', 10)
        y_pos += 10
        
        if age_stats.get('mean'):
            pdf.set_xy(10, y_pos)
            pdf.cell(0, 5, f'Mean Age: {age_stats["mean"]:.1f} years', 0, 1, 'L')
        if age_stats.get('median'):
            pdf.set_xy(10, y_pos + 5)
            pdf.cell(0, 5, f'Median Age: {age_stats["median"]:.1f} years', 0, 1, 'L')
        if age_stats.get('min') and age_stats.get('max'):
            pdf.set_xy(10, y_pos + 10)
            pdf.cell(0, 5, f'Age Range: {age_stats["min"]:.0f} - {age_stats["max"]:.0f} years', 0, 1, 'L')
    
    # Footer with brand colors
    pdf.set_fill_color(241, 245, 249)
    pdf.rect(0, 280, 210, 17, 'F')
    pdf.set_draw_color(*slate_gray)
    pdf.line(10, 280, 200, 280)
    
    pdf.set_text_color(*gray_color)
    pdf.set_font('Arial', 'I', 7)
    pdf.set_xy(10, 285)
    pdf.cell(0, 4, 'AetherSignal - Quantum PV Explorer | Exploratory Tool Only | Not for Regulatory Decision-Making', 0, 1, 'C')
    
    # Convert to bytes
    return pdf.output(dest='S').encode('latin-1')


def create_summary_dict(
    query: str,
    filters: Dict,
    total_cases: int,
    matching_cases: int,
    percentage: float,
    prr_ror: Optional[Dict] = None,
    top_drugs: Optional[Dict] = None,
    top_reactions: Optional[Dict] = None,
    age_stats: Optional[Dict] = None,
    sex_distribution: Optional[Dict] = None,
    serious_count: int = 0,
    serious_percentage: float = 0.0,
    time_trend: Optional[Dict] = None,
    query_source: Optional[str] = None,
) -> Dict:
    """
    Create a summary dictionary for PDF generation.
    
    Args:
        query: Original query string
        filters: Applied filters
        total_cases: Total cases
        matching_cases: Matching cases
        percentage: Percentage
        prr_ror: PRR/ROR statistics
        top_drugs: Top drugs
        top_reactions: Top reactions
        age_stats: Age statistics
        sex_distribution: Sex distribution
        serious_count: Serious case count
        serious_percentage: Serious case percentage
        time_trend: Time trend data
        
    Returns:
        Summary dictionary
    """
    return {
        'query': query,
        'filters': filters,
        'total_cases': total_cases,
        'matching_cases': matching_cases,
        'percentage': percentage,
        'prr_ror': prr_ror,
        'top_drugs': top_drugs or {},
        'top_reactions': top_reactions or {},
        'age_stats': age_stats or {},
        'sex_distribution': sex_distribution or {},
        'serious_count': serious_count,
        'serious_percentage': serious_percentage,
        'time_trend': time_trend,
        'query_source': query_source,
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }

