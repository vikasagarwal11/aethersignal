"""
Check database state and provide setup instructions.
Uses provided credentials to check if schema needs to be run.
"""

import os
import sys

# Your Supabase credentials
SUPABASE_URL = "https://scrksfxnkxmvvdzwmqnc.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNjcmtzZnhua3htdnZkendtcW5jIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM2MDM2NTcsImV4cCI6MjA3OTE3OTY1N30.tumWvHiXv7VsX0QTm-iyc5L0dwGFDTtgEkHAUieMcIY"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNjcmtzZnhua3htdnZkendtcW5jIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzYwMzY1NywiZXhwIjoyMDc5MTc5NjU3fQ.dUwNCFto69ZqCqcjDUMDlOuEkZ0PArK9B-RkNTp5jmw"

def check_database_state():
    """Check if tables exist in the database."""
    print("=" * 60)
    print("Checking AetherSignal Database State")
    print("=" * 60)
    print()
    print(f"Project: scrksfxnkxmvvdzwmqnc")
    print(f"URL: {SUPABASE_URL}")
    print()
    
    try:
        from supabase import create_client
        
        # Use service key for admin operations
        sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        
        print("Connecting to Supabase...")
        print("[OK] Connected successfully")
        print()
        
        # Check if user_profiles table exists
        print("Checking user_profiles table...")
        try:
            result = sb.table("user_profiles").select("id").limit(1).execute()
            print("[OK] user_profiles table EXISTS")
            print(f"     Found {len(result.data) if result.data else 0} records")
        except Exception as e:
            error_msg = str(e).lower()
            if "relation" in error_msg or "does not exist" in error_msg or "not found" in error_msg:
                print("[MISSING] user_profiles table does NOT exist")
                print("         Schema migration needed!")
            else:
                print(f"[ERROR] Could not check table: {str(e)[:100]}")
        
        print()
        
        # Check if pv_cases table exists
        print("Checking pv_cases table...")
        try:
            result = sb.table("pv_cases").select("id").limit(1).execute()
            print("[OK] pv_cases table EXISTS")
            print(f"     Found {len(result.data) if result.data else 0} records")
        except Exception as e:
            error_msg = str(e).lower()
            if "relation" in error_msg or "does not exist" in error_msg or "not found" in error_msg:
                print("[MISSING] pv_cases table does NOT exist")
                print("         Schema migration needed!")
            else:
                print(f"[ERROR] Could not check table: {str(e)[:100]}")
        
        print()
        print("=" * 60)
        print("Summary")
        print("=" * 60)
        
        # Try both tables again to determine status
        tables_exist = True
        try:
            sb.table("user_profiles").select("id").limit(0).execute()
            sb.table("pv_cases").select("id").limit(0).execute()
            print("[SUCCESS] Both tables exist - Database is ready!")
            print()
            print("Next steps:")
            print("1. Update .env file with Supabase credentials (see below)")
            print("2. Test registration and login")
            print("3. Upload data and verify storage")
        except:
            print("[ACTION REQUIRED] Tables are missing - Schema migration needed!")
            print()
            print("To run the migration:")
            print("1. Go to: https://supabase.com/dashboard/project/scrksfxnkxmvvdzwmqnc/sql")
            print("2. Click 'New query'")
            print("3. Open database/schema.sql from this project")
            print("4. Copy ALL contents")
            print("5. Paste into SQL Editor")
            print("6. Click 'Run' (or Ctrl+Enter)")
            print()
            print("After migration, run this script again to verify.")
        
        return True
        
    except ImportError:
        print("[ERROR] supabase package not installed")
        print("Run: pip install supabase")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to connect: {str(e)}")
        return False


def print_env_instructions():
    """Print instructions for updating .env file."""
    print()
    print("=" * 60)
    print("Update .env File")
    print("=" * 60)
    print()
    print("Add these lines to your .env file:")
    print()
    print("# Supabase Configuration (Multi-Tenant System)")
    print(f"SUPABASE_URL={SUPABASE_URL}")
    print(f"SUPABASE_ANON_KEY={SUPABASE_ANON_KEY}")
    print(f"SUPABASE_SERVICE_KEY={SUPABASE_SERVICE_KEY}")
    print()
    print("The .env file should be in: C:\\Vikas\\Projects\\aethersignal\\.env")
    print()


if __name__ == "__main__":
    print()
    success = check_database_state()
    print_env_instructions()
    sys.exit(0 if success else 1)

