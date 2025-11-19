"""
PDF Report Generation for AetherSignal
Creates one-page PDF summaries using fpdf2.
"""

from fpdf import FPDF
from typing import Dict, List, Optional
from datetime import datetime
import io


def build_pdf_report(summary_dict: Dict) -> bytes:
    """
    Build a one-page PDF summary report.
    
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
    
    # Colors: Blue/white pharma style
    blue_color = (0, 51, 102)  # Dark blue
    light_blue = (173, 216, 230)  # Light blue
    gray_color = (128, 128, 128)
    
    # Header
    pdf.set_fill_color(*blue_color)
    pdf.rect(0, 0, 210, 30, 'F')
    
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Arial', 'B', 24)
    pdf.set_xy(10, 10)
    pdf.cell(0, 10, 'AetherSignal - Quantum PV Explorer', 0, 1, 'L')
    
    pdf.set_font('Arial', '', 10)
    pdf.set_xy(10, 20)
    generated_at = summary_dict.get('generated_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    pdf.cell(0, 5, f'Report Generated: {generated_at}', 0, 1, 'L')
    
    # Disclaimer
    pdf.set_text_color(200, 0, 0)
    pdf.set_font('Arial', 'I', 8)
    pdf.set_xy(10, 35)
    pdf.multi_cell(190, 4, 
                   'DISCLAIMER: Exploratory tool only - not for regulatory decision-making. '
                   'Spontaneous report data are subject to under-reporting and bias; '
                   'no incidence or causality implied.', 0, 'L')
    
    # Reset text color
    pdf.set_text_color(0, 0, 0)
    
    y_pos = 50
    
    # Query Section
    pdf.set_font('Arial', 'B', 12)
    pdf.set_xy(10, y_pos)
    pdf.cell(0, 8, 'Query Summary', 0, 1, 'L')
    
    pdf.set_font('Arial', '', 10)
    pdf.set_xy(10, y_pos + 8)
    query = summary_dict.get('query', 'N/A')
    pdf.multi_cell(190, 5, f'Query: {query}', 0, 'L')
    
    y_pos += 20
    
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
    
    # PRR/ROR Section (if available)
    prr_ror = summary_dict.get('prr_ror')
    if prr_ror:
        pdf.set_font('Arial', 'B', 12)
        pdf.set_xy(10, y_pos)
        pdf.cell(0, 8, 'Signal Detection Metrics', 0, 1, 'L')
        
        pdf.set_font('Arial', '', 10)
        y_pos += 10
        
        drug = prr_ror.get('drug', 'N/A')
        reaction = prr_ror.get('reaction', 'N/A')
        pdf.set_xy(10, y_pos)
        pdf.cell(0, 5, f'Drug: {drug}', 0, 1, 'L')
        pdf.set_xy(10, y_pos + 5)
        pdf.cell(0, 5, f'Reaction: {reaction}', 0, 1, 'L')
        
        prr = prr_ror.get('prr', 0)
        prr_ci_lower = prr_ror.get('prr_ci_lower', 0)
        prr_ci_upper = prr_ror.get('prr_ci_upper', 0)
        pdf.set_xy(10, y_pos + 10)
        pdf.cell(0, 5, f'PRR: {prr:.2f} (95% CI: {prr_ci_lower:.2f} - {prr_ci_upper:.2f})', 0, 1, 'L')
        
        ror = prr_ror.get('ror', 0)
        ror_ci_lower = prr_ror.get('ror_ci_lower', 0)
        ror_ci_upper = prr_ror.get('ror_ci_upper', 0)
        pdf.set_xy(10, y_pos + 15)
        pdf.cell(0, 5, f'ROR: {ror:.2f} (95% CI: {ror_ci_lower:.2f} - {ror_ci_upper:.2f})', 0, 1, 'L')
        
        p_value = prr_ror.get('p_value')
        if p_value:
            pdf.set_xy(10, y_pos + 20)
            pdf.cell(0, 5, f'P-value: {p_value:.4f}', 0, 1, 'L')
        
        y_pos += 35
    
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
    
    # Footer
    pdf.set_text_color(*gray_color)
    pdf.set_font('Arial', 'I', 8)
    pdf.set_xy(10, 280)
    pdf.cell(0, 5, 'AetherSignal - Quantum PV Explorer | Exploratory Tool Only', 0, 1, 'C')
    
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

