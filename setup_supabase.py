"""
Helper script to verify Supabase setup.
Run this after completing manual setup steps to verify everything is configured correctly.
"""

import os
import sys
from pathlib import Path

def check_env_file():
    """Check if .env file exists and has required variables."""
    print("=" * 60)
    print("Checking .env file...")
    print("=" * 60)
    
    env_path = Path(".env")
    if not env_path.exists():
        print("[ERROR] .env file not found!")
        print("   Create .env file in project root with:")
        print("   SUPABASE_URL=https://your-project.supabase.co")
        print("   SUPABASE_ANON_KEY=your-anon-key")
        return False
    
    print("[OK] .env file exists")
    
    # Read .env file
    env_vars = {}
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    
    # Check required variables
    required = ['SUPABASE_URL', 'SUPABASE_ANON_KEY']
    missing = []
    placeholder = []
    
    for var in required:
        if var not in env_vars:
            missing.append(var)
        elif 'your-' in env_vars[var].lower() or 'xxxxx' in env_vars[var].lower():
            placeholder.append(var)
    
    if missing:
        print(f"[ERROR] Missing environment variables: {', '.join(missing)}")
        return False
    
    if placeholder:
        print(f"[WARNING] Placeholder values found: {', '.join(placeholder)}")
        print("   Please replace with actual Supabase credentials")
        return False
    
    print("[OK] All required environment variables are set")
    print(f"   SUPABASE_URL: {env_vars['SUPABASE_URL'][:30]}...")
    print(f"   SUPABASE_ANON_KEY: {env_vars['SUPABASE_ANON_KEY'][:30]}...")
    return True


def check_supabase_package():
    """Check if supabase package is installed."""
    print("\n" + "=" * 60)
    print("Checking Python packages...")
    print("=" * 60)
    
    try:
        import supabase
        print("[OK] supabase package is installed")
        return True
    except ImportError:
        print("[ERROR] supabase package NOT installed")
        print("   Run: pip install supabase")
        return False


def check_supabase_connection():
    """Check if we can connect to Supabase."""
    print("\n" + "=" * 60)
    print("Checking Supabase connection...")
    print("=" * 60)
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("[WARNING] python-dotenv not installed (optional)")
        print("   Environment variables will be read from system")
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        print("[ERROR] SUPABASE_URL or SUPABASE_ANON_KEY not found in environment")
        return False
    
    try:
        from supabase import create_client
        
        sb = create_client(url, key)
        
        # Try to query user_profiles table (should exist after schema setup)
        try:
            result = sb.table("user_profiles").select("id").limit(1).execute()
            print("[OK] Successfully connected to Supabase")
            print("[OK] user_profiles table exists")
            return True
        except Exception as e:
            if "relation" in str(e).lower() or "does not exist" in str(e).lower():
                print("[WARNING] Connected to Supabase, but user_profiles table not found")
                print("   Run database/schema.sql in Supabase SQL Editor")
                return False
            else:
                print(f"[WARNING] Connection test failed: {str(e)}")
                return False
                
    except Exception as e:
        print(f"[ERROR] Failed to connect to Supabase: {str(e)}")
        print("   Check your SUPABASE_URL and SUPABASE_ANON_KEY")
        return False


def check_schema_file():
    """Check if schema.sql file exists and is valid."""
    print("\n" + "=" * 60)
    print("Checking database schema file...")
    print("=" * 60)
    
    schema_path = Path("database/schema.sql")
    if not schema_path.exists():
        print("[ERROR] database/schema.sql not found!")
        return False
    
    print("[OK] database/schema.sql exists")
    
    # Check file size (should be substantial)
    size = schema_path.stat().st_size
    if size < 1000:
        print("[WARNING] Schema file seems too small (might be incomplete)")
        return False
    
    print(f"[OK] Schema file size: {size:,} bytes")
    
    # Check for key table definitions
    content = schema_path.read_text()
    if "CREATE TABLE" in content and "user_profiles" in content and "pv_cases" in content:
        print("[OK] Schema file contains required table definitions")
        return True
    else:
        print("[WARNING] Schema file might be missing required tables")
        return False


def main():
    """Run all checks."""
    print("\n" + "=" * 60)
    print("AetherSignal Supabase Setup Verification")
    print("=" * 60)
    print("\nThis script checks if your Supabase setup is complete.")
    print("Complete the manual setup steps first, then run this script.\n")
    
    checks = [
        ("Schema File", check_schema_file),
        ("Python Package", check_supabase_package),
        ("Environment Variables", check_env_file),
        ("Supabase Connection", check_supabase_connection),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"[ERROR] Error checking {name}: {str(e)}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    all_passed = True
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {name}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("[SUCCESS] All checks passed! Your Supabase setup is complete.")
        print("\nNext steps:")
        print("1. Start Streamlit: streamlit run app.py")
        print("2. Test registration and login")
        print("3. Upload data and verify it's stored in database")
    else:
        print("[FAILED] Some checks failed. Please complete the manual setup steps.")
        print("\nSee docs/MANUAL_SETUP_CHECKLIST.md for detailed instructions.")
    print("=" * 60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

