"""
Final Supabase setup check - provides clear status and next steps.
This script checks everything and tells you exactly what to do next.
"""

import os
import sys
from pathlib import Path

PROJECT_REF = "scrksfxnkxmvvdzwmqnc"
SUPABASE_URL = f"https://{PROJECT_REF}.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNjcmtzZnhua3htdnZkendtcW5jIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzYwMzY1NywiZXhwIjoyMDc5MTc5NjU3fQ.dUwNCFto69ZqCqcjDUMDlOuEkZ0PArK9B-RkNTp5jmw"

def check_database_state():
    """Check if tables exist."""
    try:
        from supabase import create_client
        sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        
        user_profiles_exists = False
        pv_cases_exists = False
        
        try:
            sb.table("user_profiles").select("id").limit(1).execute()
            user_profiles_exists = True
        except:
            pass
        
        try:
            sb.table("pv_cases").select("id").limit(1).execute()
            pv_cases_exists = True
        except:
            pass
        
        return user_profiles_exists, pv_cases_exists
    except:
        return None, None

def main():
    print("=" * 70)
    print("AetherSignal - Final Setup Status Check")
    print("=" * 70)
    print()
    
    # Check 1: supabase package
    print("[1/5] Checking Python packages...")
    try:
        import supabase
        print("    OK - supabase package installed")
        package_ok = True
    except ImportError:
        print("    MISSING - supabase package not installed")
        print("    Run: pip install supabase")
        package_ok = False
    
    print()
    
    if not package_ok:
        print("=" * 70)
        print("SETUP INCOMPLETE - Install supabase package first")
        print("=" * 70)
        return False
    
    # Check 2: Database connection
    print("[2/5] Checking database connection...")
    user_exists, pv_exists = check_database_state()
    
    if user_exists is None:
        print("    ERROR - Could not connect to database")
        print("    Check your internet connection and credentials")
        return False
    
    print("    OK - Connected to Supabase")
    print()
    
    # Check 3: Tables
    print("[3/5] Checking database tables...")
    print(f"    user_profiles: {'EXISTS' if user_exists else 'MISSING'}")
    print(f"    pv_cases: {'EXISTS' if pv_exists else 'MISSING'}")
    print()
    
    if user_exists and pv_exists:
        print("=" * 70)
        print("SUCCESS - All tables exist! Database is ready.")
        print("=" * 70)
        print()
        print("Next steps:")
        print("  1. Ensure .env file has Supabase credentials")
        print("  2. Test the application: streamlit run app.py")
        print("  3. Try registration and login")
        return True
    
    # Check 4: Schema file
    print("[4/5] Checking schema file...")
    schema_path = Path("database/schema.sql")
    if schema_path.exists():
        size = schema_path.stat().st_size
        print(f"    OK - Schema file found ({size:,} bytes)")
    else:
        print("    ERROR - database/schema.sql not found!")
        return False
    print()
    
    # Check 5: Migration file
    print("[5/5] Checking migration files...")
    migration_dir = Path("supabase/migrations")
    migrations = list(migration_dir.glob("*.sql")) if migration_dir.exists() else []
    if migrations:
        latest = max(migrations, key=lambda p: p.stat().st_mtime)
        print(f"    OK - Migration file ready: {latest.name}")
    else:
        print("    INFO - No migration files found (will create if needed)")
    print()
    
    # Summary
    print("=" * 70)
    print("ACTION REQUIRED - Database Schema Migration")
    print("=" * 70)
    print()
    print("The database tables are missing. You need to run the schema.")
    print()
    print("Since Supabase REST API doesn't support DDL statements,")
    print("you must run the schema in the Supabase SQL Editor.")
    print()
    print("QUICK STEPS (2 minutes):")
    print("-" * 70)
    print("1. Open this URL in your browser:")
    print("   https://supabase.com/dashboard/project/scrksfxnkxmvvdzwmqnc/sql")
    print()
    print("2. Click the 'New query' button")
    print()
    print("3. Open the file: database/schema.sql")
    print("   (In VS Code or any text editor)")
    print()
    print("4. Select ALL text (Ctrl+A) and copy (Ctrl+C)")
    print()
    print("5. Paste into the SQL Editor (Ctrl+V)")
    print()
    print("6. Click the 'Run' button (or press Ctrl+Enter)")
    print()
    print("7. Wait for 'Success' message - should take 5-10 seconds")
    print()
    print("8. Verify tables were created:")
    print("   - Go to 'Table Editor' in left sidebar")
    print("   - You should see 'user_profiles' and 'pv_cases'")
    print()
    print("9. Run this script again to verify:")
    print("   python final_setup_check.py")
    print()
    print("=" * 70)
    
    return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[Cancelled]")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] {str(e)}")
        sys.exit(1)

