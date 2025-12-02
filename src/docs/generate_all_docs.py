"""
Generate All Documentation - CLI script to generate all docs
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.docs.doc_generator import generate_docs


if __name__ == "__main__":
    print("Generating AetherSignal documentation...")
    files = generate_docs()
    
    print("\n✅ Documentation generated:")
    for doc_type, file_path in files.items():
        if file_path:
            print(f"  - {doc_type}: {file_path}")
        else:
            print(f"  - {doc_type}: Failed")
    
    print("\nDocumentation generation complete!")

