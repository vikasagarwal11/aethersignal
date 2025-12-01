"""
Prompt Templates for AI Narrative Engine - Phase 3J Step 4
Reusable prompt templates for executive summaries.
"""

EXECUTIVE_SUMMARY_PROMPT = """
You are an expert pharmacovigilance analyst generating an executive-level safety summary.
Audience: VP of Drug Safety, Chief Medical Officer, Regulatory Leaders.

Write a concise, high-impact summary (140-220 words) covering:

1. Total AE volume + 30-day change.
2. Top emerging reactions (ranked by quantum score).
3. Severity trends.
4. Any novel signals (present in social/literature, absent in FAERS).
5. Multi-source divergence (FAERS vs Social vs Literature).
6. Any notable mechanism-of-action insights (if provided).
7. Recommendation or next step for executives.

Use professional, neutral, regulatory-safe language.
Do NOT guess or invent data. Base all statements ONLY on the provided metrics.
"""

RISK_ALERT_PROMPT = """
You are generating a short safety risk alert for internal review teams.
Summarize in 2–4 sentences:

- Any high-severity emerging reactions
- Fast-rising trends
- Novel/unexpected signals
- Recommended next action

Keep it compact and factual.
"""

TRENDING_RISKS_PROMPT = """
Analyze trending risks and provide a brief summary (3-5 sentences) of:
- Reactions showing acceleration
- Severity patterns
- Cross-source consistency
- Urgency level
"""

MECHANISM_INSIGHT_PROMPT = """
Provide a brief mechanistic insight (2-3 sentences) explaining:
- Biological pathway connections
- Organ system involvement
- Plausibility assessment
Based on the provided mechanism data.
"""

NOVELTY_ANALYSIS_PROMPT = """
Analyze novel signals and provide a summary (3-4 sentences) of:
- Reactions appearing in new sources
- Potential significance
- Recommended monitoring approach
"""

SOURCE_DIVERGENCE_PROMPT = """
Analyze multi-source divergence and explain (2-3 sentences):
- Differences between FAERS, Social, and Literature
- Potential reasons for divergence
- Implications for signal validation
"""

