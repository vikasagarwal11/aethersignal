"""
Execute schema using browser automation to access Supabase SQL Editor.
This bypasses the DNS/connection issues.
"""

import sys
from pathlib import Path

def read_schema():
    """Read the schema SQL file."""
    schema_path = Path("database/schema.sql")
    if not schema_path.exists():
        print(f"[ERROR] {schema_path} not found!")
        return None
    return schema_path.read_text()

def main():
    """Main function."""
    print("=" * 70)
    print("Browser-Based Schema Execution")
    print("=" * 70)
    print()
    
    schema_sql = read_schema()
    if not schema_sql:
        return False
    
    print(f"[OK] Schema file loaded ({len(schema_sql):,} bytes)")
    print()
    print("=" * 70)
    print("INSTRUCTIONS")
    print("=" * 70)
    print()
    print("I'll open the Supabase SQL Editor in your browser.")
    print("Then you can paste the schema and run it.")
    print()
    print("Steps:")
    print("  1. SQL Editor will open in your browser")
    print("  2. Click 'New query'")
    print("  3. Copy the SQL below (or from database/schema.sql)")
    print("  4. Paste into SQL Editor")
    print("  5. Click 'Run' (or Ctrl+Enter)")
    print()
    print("=" * 70)
    print("SQL TO EXECUTE (First 500 chars):")
    print("=" * 70)
    print()
    print(schema_sql[:500])
    print("...")
    print()
    print("(Full SQL in: database/schema.sql)")
    print()
    
    # Open browser
    import webbrowser
    url = "https://supabase.com/dashboard/project/scrksfxnkxmvvdzwmqnc/sql"
    print(f"[INFO] Opening SQL Editor in browser...")
    webbrowser.open(url)
    
    print()
    print("[SUCCESS] Browser opened!")
    print()
    print("After executing the SQL in the browser, verify with:")
    print("  python final_setup_check.py")
    print()
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

