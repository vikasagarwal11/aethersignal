"""
Persistent storage and fuzzy matching for schema mapping templates.

Templates are simple JSON objects stored on disk so that column mappings
can be reused across sessions and datasets with similar column layouts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import json


TEMPLATE_FILE = Path(__file__).resolve().parent.parent / "schema_templates.json"


def load_templates() -> Dict[str, Dict[str, Any]]:
    """
    Load mapping templates from disk.

    Returns:
        Dict keyed by template name with:
            - name: template name
            - columns: original column list
            - mapping: field->column mapping
    """
    try:
        if not TEMPLATE_FILE.exists():
            return {}
        with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Basic validation
        if not isinstance(data, dict):
            return {}
        return data
    except Exception:
        # Fail gracefully – templates are an optional enhancement
        return {}


def save_templates(templates: Dict[str, Dict[str, Any]]) -> None:
    """
    Persist mapping templates to disk.
    """
    try:
        TEMPLATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(TEMPLATE_FILE, "w", encoding="utf-8") as f:
            json.dump(templates, f, indent=2)
    except Exception:
        # On read-only or ephemeral environments, silently skip persistence.
        pass


def register_template(
    name: str,
    mapping: Dict[str, str],
    columns: List[str],
) -> None:
    """
    Register or update a named mapping template and persist it.

    Args:
        name: Human-readable name for the template (e.g., "Argus CSV v1").
        mapping: Standard-field to column-name mapping.
        columns: Column names from the dataset used to create the template.
    """
    if not name or not mapping or not columns:
        return

    templates = load_templates()
    templates[name] = {
        "name": name,
        "mapping": mapping,
        "columns": list(columns),
    }
    save_templates(templates)


def _column_set_similarity(cols_a: List[str], cols_b: List[str]) -> float:
    """
    Jaccard similarity between two column name sets.
    """
    set_a = {c.lower().strip() for c in cols_a}
    set_b = {c.lower().strip() for c in cols_b}
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    if union == 0:
        return 0.0
    return float(intersection) / float(union)


def find_best_template_for_columns(
    columns: List[str],
    templates: Optional[Dict[str, Dict[str, Any]]] = None,
    min_similarity: float = 0.6,
) -> Tuple[Optional[str], Optional[Dict[str, Any]], float]:
    """
    Find the best matching template for the given column list using
    Jaccard similarity on column names.

    Args:
        columns: Columns from the newly uploaded dataset.
        templates: Optional templates dict (if None, will be loaded from disk).
        min_similarity: Minimum similarity threshold for a suggestion.

    Returns:
        (template_name, template_dict, similarity_score) or (None, None, 0.0)
    """
    if templates is None:
        templates = load_templates()

    if not templates or not columns:
        return None, None, 0.0

    best_name: Optional[str] = None
    best_template: Optional[Dict[str, Any]] = None
    best_score: float = 0.0

    for name, tpl in templates.items():
        tpl_cols = tpl.get("columns") or []
        if not tpl_cols:
            continue
        score = _column_set_similarity(columns, tpl_cols)
        if score > best_score:
            best_name = name
            best_template = tpl
            best_score = score

    if best_score < min_similarity:
        return None, None, best_score

    # Sanity check: ensure mapped columns exist in current dataset
    current_cols = {c.lower().strip() for c in columns}
    mapping = (best_template or {}).get("mapping") or {}
    mapped_cols = {c.lower().strip() for c in mapping.values() if c}
    if not mapped_cols.issubset(current_cols):
        # Template isn't compatible with this dataset
        return None, None, 0.0

    return best_name, best_template, best_score

