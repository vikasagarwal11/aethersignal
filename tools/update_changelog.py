"""
Changelog Updater - Auto-update changelog
"""

import os
from datetime import datetime
from typing import Optional


def update_changelog(message: str, version: Optional[str] = None):
    """
    Update CHANGELOG.md with new entry.
    
    Args:
        message: Change description
        version: Optional version string
    """
    changelog_path = "CHANGELOG.md"
    
    # Create changelog if it doesn't exist
    if not os.path.exists(changelog_path):
        with open(changelog_path, "w", encoding="utf-8") as f:
            f.write("# Changelog\n\n")
            f.write("All notable changes to AetherSignal will be documented in this file.\n\n")
            f.write("---\n\n")
    
    # Read existing content
    with open(changelog_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Prepare new entry
    date_str = datetime.now().strftime("%Y-%m-%d")
    version_str = f" ({version})" if version else ""
    
    new_entry = f"\n### {date_str}{version_str}\n\n- {message}\n\n"
    
    # Insert after header
    if "---" in content:
        parts = content.split("---", 1)
        new_content = parts[0] + "---\n" + new_entry + parts[1]
    else:
        new_content = content + new_entry
    
    # Write back
    with open(changelog_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    print(f"✅ Changelog updated: {message}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        message = " ".join(sys.argv[1:])
        version = sys.argv[2] if len(sys.argv) > 2 else None
        update_changelog(message, version)
    else:
        print("Usage: python update_changelog.py <message> [version]")

