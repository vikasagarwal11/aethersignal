"""
Release Package Script - Creates release-ready package
"""

import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


def create_release_package(version: str = "v1.0.0"):
    """
    Create release package.
    
    Args:
        version: Version string
    """
    release_dir = f"release/aethersignal-{version}"
    
    # Create release directory
    os.makedirs(release_dir, exist_ok=True)
    
    # Files and directories to include
    include_items = [
        "src/",
        "pages/",
        "app.py",
        "requirements.txt",
        "Dockerfile",
        "docker-compose.yml",
        "install.sh",
        "install.bat",
        ".env.example",
        "README_PRODUCTION.md",
        "CHANGELOG.md",
        "src/version.py",
        "tools/",
        "demo_data/"
    ]
    
    # Copy items
    print(f"📦 Creating release package: {release_dir}")
    for item in include_items:
        if os.path.exists(item):
            dest = os.path.join(release_dir, item)
            if os.path.isdir(item):
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copy2(item, dest)
            print(f"  ✅ Copied {item}")
    
    # Create README from production README
    if os.path.exists("README_PRODUCTION.md"):
        shutil.copy2("README_PRODUCTION.md", os.path.join(release_dir, "README.md"))
    
    # Create .gitignore
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*.so
.Python
venv/
env/

# Logs
logs/
*.log

# Data
data/
storage/
*.db
*.sqlite

# Environment
.env

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db
"""
    with open(os.path.join(release_dir, ".gitignore"), "w") as f:
        f.write(gitignore_content)
    
    print(f"\n✨ Release package created: {release_dir}")
    print(f"\nTo create archive:")
    print(f"  cd release && tar -czf aethersignal-{version}.tar.gz aethersignal-{version}/")
    print(f"  or")
    print(f"  cd release && zip -r aethersignal-{version}.zip aethersignal-{version}/")


if __name__ == "__main__":
    import sys
    version = sys.argv[1] if len(sys.argv) > 1 else "v1.0.0"
    create_release_package(version)

