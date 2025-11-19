# Negation Detection Implementation Specification

## Overview
Add negation detection to AetherSignal's natural language query parser to handle queries like "no suicidal ideation" or "excluding injection site reactions".

## Files to Modify

1. `src/nl_query_parser.py` - Add negation detection logic
2. `src/signal_stats.py` - Add exclusion filtering logic
3. `app.py` - Add UI display for excluded reactions (optional, can be done later)

---

## Implementation Details

### 1. Add Negation Detection to `nl_query_parser.py`

**Location**: Inside `parse_query_to_filters()` function, after reaction extraction (around line 58-59)

**Add this function BEFORE `parse_query_to_filters()`:**

```python
def detect_negations(query: str) -> List[str]:
    """
    Detect negated reactions in natural language query.
    
    Args:
        query: Natural language query string
        
    Returns:
        List of negated reaction terms to exclude
    """
    query_lower = query.lower()
    negated_reactions = []
    
    # Negation patterns - look for "no X", "not X", "without X", "excluding X"
    negation_patterns = [
        # "no X" or "no reaction X"
        r'(?:no|not)[\s]+(?:reaction|adverse event|ae|event|adr|side effect)[\s:]+([a-z0-9\s\-]+?)(?:\.|,|$|\s+and|\s+or)',
        r'(?:no|not)[\s]+([a-z0-9\s\-]+?)(?:\s+reaction|\s+event|\s+ae|\.|,|$)',
        # "without X" or "excluding X"
        r'(?:without|excluding|except|exclude)[\s]+([a-z0-9\s\-]+?)(?:\.|,|$|\s+and|\s+or)',
        r'(?:without|excluding)[\s]+(?:reaction|adverse event|ae|event)[\s:]+([a-z0-9\s\-]+?)(?:\.|,|$|\s+and|\s+or)',
        # "but no X" or "but not X"
        r'but[\s]+(?:no|not)[\s]+([a-z0-9\s\-]+?)(?:\.|,|$|\s+and|\s+or)',
    ]
    
    for pattern in negation_patterns:
        matches = re.findall(pattern, query_lower, re.IGNORECASE)
        for match in matches:
            reaction = match.strip()
            # Filter out common stop words and short terms
            if len(reaction) > 2 and reaction not in ['the', 'all', 'any', 'for', 'with', 'but', 'and', 'or']:
                # Clean up trailing location words (e.g., "in Japan")
                reaction = re.sub(r'\s+in\s+[a-z\s]+$', '', reaction).strip()
                if reaction and reaction not in negated_reactions:
                    negated_reactions.append(reaction)
    
    return negated_reactions
```

**Then modify `parse_query_to_filters()` function:**

**After line 59 (after reactions are extracted), add:**

```python
    # Extract negated reactions (exclusions)
    negated_reactions = detect_negations(query)
    if negated_reactions:
        filters['exclude_reaction'] = negated_reactions
```

**Update the docstring** (line 19-21) to include:
```python
    Returns:
        Dictionary with filter keys: drug, reaction, age_min, age_max, 
        sex, country, seriousness, date_from, date_to, exclude_reaction
```

---

### 2. Add Exclusion Logic to `signal_stats.py`

**Location**: Inside `apply_filters()` function, after reaction filter (around line 50)

**Add this code block AFTER the reaction filter section:**

```python
    # Exclude negated reactions
    if 'exclude_reaction' in filters and 'reaction' in filtered_df.columns:
        exclude_list = filters['exclude_reaction']
        if isinstance(exclude_list, list):
            # Exclude any reaction that contains any of the excluded terms
            exclude_mask = filtered_df['reaction'].apply(
                lambda x: not any(
                    normalize_text(ex) in normalize_text(str(x)) 
                    for ex in exclude_list
                )
            )
        else:
            # Single exclusion term
            exclude_mask = filtered_df['reaction'].apply(
                lambda x: normalize_text(exclude_list) not in normalize_text(str(x))
            )
        filtered_df = filtered_df[exclude_mask]
```

**Update the docstring** (line 19) to mention:
```python
    Args:
        df: Normalized DataFrame with standard column names
        filters: Filter dictionary from nl_query_parser (may include 'exclude_reaction')
```

---

### 3. Update UI Display in `app.py` (Optional - can be done later)

**Location**: In `display_query_results()` function, in the "Interpreted Filters" section (around line 275-280)

**Find the section that displays interpreted filters and add:**

```python
    # Show excluded reactions if present
    if filters.get('exclude_reaction'):
        excluded_terms = ', '.join(filters['exclude_reaction'])
        st.caption(f"❌ **Excluding:** {excluded_terms}")
```

---

## Test Cases

The implementation should handle these queries:

1. **Basic negation:**
   - Query: `"Show cases with drug aspirin but no headache"`
   - Expected: `filters['exclude_reaction'] = ['headache']`

2. **Multiple exclusions:**
   - Query: `"Find cases excluding nausea and vomiting"`
   - Expected: `filters['exclude_reaction'] = ['nausea', 'vomiting']`

3. **Without keyword:**
   - Query: `"Show serious cases without injection site reactions"`
   - Expected: `filters['exclude_reaction'] = ['injection site reactions']`

4. **Backward compatibility:**
   - Query: `"Show cases with drug aspirin"`
   - Expected: `'exclude_reaction'` key should NOT exist in filters

5. **Complex query:**
   - Query: `"Find cases for drug semaglutide with reaction pancreatitis but no nausea in women"`
   - Expected: 
     - `filters['drug'] = 'semaglutide'`
     - `filters['reaction'] = 'pancreatitis'`
     - `filters['exclude_reaction'] = ['nausea']`
     - `filters['sex'] = 'F'`

---

## Edge Cases to Handle

1. **Stop words**: Don't extract "no the" or "not for" as reactions
2. **Trailing location words**: "no headache in Japan" → exclude "headache" not "headache in japan"
3. **Multiple negations**: "no X and no Y" → both should be excluded
4. **Case insensitivity**: "No HEADACHE" should work
5. **Partial matches**: If reaction is "severe headache", excluding "headache" should exclude it

---

## Validation

After implementation, verify:

1. ✅ Existing queries still work (backward compatibility)
2. ✅ Negation queries correctly exclude reactions
3. ✅ Multiple exclusions work
4. ✅ No false positives (common words not extracted)
5. ✅ Filtering actually excludes the reactions from results

---

## Integration Notes

- **Backward compatible**: If `exclude_reaction` key doesn't exist, code should work as before
- **Optional UI**: UI display can be added later if needed
- **No breaking changes**: All existing functionality should continue to work

---

## Example Implementation Flow

```
User Query: "Show cases with drug aspirin but no headache"

1. nl_query_parser.parse_query_to_filters(query)
   → Returns: {
       'drug': 'aspirin',
       'exclude_reaction': ['headache']
     }

2. signal_stats.apply_filters(df, filters)
   → Filters for drug='aspirin'
   → Then excludes any cases where reaction contains 'headache'
   → Returns filtered DataFrame

3. Results show only aspirin cases without headache
```

---

## Files Summary

| File | Changes | Lines to Add |
|------|---------|--------------|
| `src/nl_query_parser.py` | Add `detect_negations()` function + call in `parse_query_to_filters()` | ~40 lines |
| `src/signal_stats.py` | Add exclusion logic in `apply_filters()` | ~15 lines |
| `app.py` | Add UI display (optional) | ~3 lines |

**Total**: ~55-60 lines of code

---

## Ready for Implementation

This specification provides everything needed to implement negation detection. The implementation is:
- ✅ Modular (can be added without breaking existing code)
- ✅ Testable (clear test cases provided)
- ✅ Backward compatible (existing queries still work)
- ✅ Well-defined (exact locations and code patterns specified)

