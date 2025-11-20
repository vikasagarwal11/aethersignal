#!/usr/bin/env python
"""Quick test to see if app.py imports successfully."""
import sys
import traceback

try:
    print("Testing app.py imports...")
    import app
    print("✅ SUCCESS: app.py imported successfully!")
except Exception as e:
    print("❌ ERROR: Failed to import app.py")
    print(f"Error: {e}")
    print("\nFull traceback:")
    traceback.print_exc()

