"""
Helper script to format AI-generated MedDRA dictionary extensions.
Paste the AI output here and it will format it for insertion into utils.py
"""

import re
from typing import List, Tuple

def format_ai_output(ai_text: str) -> str:
    """
    Format AI-generated dictionary entries for insertion into utils.py
    
    Args:
        ai_text: Raw text from ChatGPT/Grok with dictionary entries
        
    Returns:
        Formatted Python dictionary entries
    """
    lines = ai_text.split('\n')
    formatted_lines = []
    current_category = None
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
        
        # Detect category comments
        if line.startswith('#') and ('category' in line.lower() or any(
            cat in line.lower() for cat in ['fever', 'pain', 'skin', 'cardiac', 'respiratory', 
                                           'gastro', 'neuro', 'mental', 'endocrine', 'blood',
                                           'liver', 'kidney', 'infection', 'allergy', 'swelling']
        )):
            current_category = line
            formatted_lines.append('')
            formatted_lines.append(line)
            continue
        
        # Extract dictionary entries (handle various formats)
        # Format 1: "key": "value",
        match1 = re.search(r'"([^"]+)":\s*"([^"]+)"', line)
        # Format 2: key: value
        match2 = re.search(r'([a-z\s\-]+):\s*([A-Z][a-zA-Z\s]+)', line)
        # Format 3: key -> value
        match3 = re.search(r'([a-z\s\-]+)\s*->\s*([A-Z][a-zA-Z\s]+)', line)
        
        if match1:
            key, value = match1.groups()
            formatted_lines.append(f'    "{key.lower()}": "{value}",')
        elif match2:
            key, value = match2.groups()
            formatted_lines.append(f'    "{key.lower().strip()}": "{value.strip()}",')
        elif match3:
            key, value = match3.groups()
            formatted_lines.append(f'    "{key.lower().strip()}": "{value.strip()}",')
        elif line.startswith('"') and ':' in line:
            # Try to parse as-is
            formatted_lines.append(f'    {line}')
    
    return '\n'.join(formatted_lines)


def validate_entries(formatted_text: str) -> List[str]:
    """
    Validate formatted entries and return any issues.
    
    Returns:
        List of validation warnings/errors
    """
    issues = []
    lines = formatted_text.split('\n')
    
    for i, line in enumerate(lines, 1):
        line = line.strip()
        
        # Skip comments and empty lines
        if not line or line.startswith('#'):
            continue
        
        # Check format
        if not re.match(r'\s*"[^"]+":\s*"[^"]+",?\s*$', line):
            issues.append(f"Line {i}: Invalid format - {line[:50]}")
            continue
        
        # Extract key and value
        match = re.search(r'"([^"]+)":\s*"([^"]+)"', line)
        if match:
            key, value = match.groups()
            
            # Check key is lowercase
            if key != key.lower():
                issues.append(f"Line {i}: Key should be lowercase - '{key}'")
            
            # Check value is title case (first letter uppercase)
            if value and value[0] != value[0].upper():
                issues.append(f"Line {i}: Value should be title case - '{value}'")
    
    return issues


if __name__ == "__main__":
    print("=" * 60)
    print("MedDRA Dictionary Formatter")
    print("=" * 60)
    print("\nPaste the AI-generated dictionary entries below.")
    print("Press Ctrl+D (Linux/Mac) or Ctrl+Z then Enter (Windows) when done.\n")
    
    try:
        ai_input = []
        while True:
            try:
                line = input()
                ai_input.append(line)
            except EOFError:
                break
        
        ai_text = '\n'.join(ai_input)
        
        print("\n" + "=" * 60)
        print("FORMATTED OUTPUT:")
        print("=" * 60 + "\n")
        
        formatted = format_ai_output(ai_text)
        print(formatted)
        
        print("\n" + "=" * 60)
        print("VALIDATION:")
        print("=" * 60 + "\n")
        
        issues = validate_entries(formatted)
        if issues:
            for issue in issues:
                print(f"⚠️  {issue}")
        else:
            print("✅ All entries are properly formatted!")
        
        print("\n" + "=" * 60)
        print("Copy the formatted output above and add it to src/utils.py")
        print("in the FREE_MEDDRA_LIKE dictionary.")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\nCancelled.")

