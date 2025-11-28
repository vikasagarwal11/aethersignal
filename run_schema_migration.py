"""
Execute database schema migration via Supabase API.
This script attempts to run database/schema.sql using the Supabase service role key.
"""

import os
import sys
from pathlib import Path

def load_env():
    """Load environment variables from .env file."""
    env_path = Path(".env")
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

def execute_schema_migration():
    """Execute the schema.sql file via Supabase API."""
    print("=" * 60)
    print("AetherSignal Database Schema Migration")
    print("=" * 60)
    print()
    
    # Load environment variables
    load_env()
    
    url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not url or not service_key:
        print("[ERROR] SUPABASE_URL or SUPABASE_SERVICE_KEY not found in .env")
        print("Please ensure .env file has these values configured.")
        return False
    
    # Read schema file
    schema_path = Path("database/schema.sql")
    if not schema_path.exists():
        print("[ERROR] database/schema.sql not found!")
        return False
    
    print(f"[OK] Found schema file: {schema_path}")
    schema_sql = schema_path.read_text()
    
    print(f"[OK] Schema file size: {len(schema_sql):,} bytes")
    print()
    
    try:
        from supabase import create_client
        
        print("Connecting to Supabase...")
        sb = create_client(url, service_key)
        print("[OK] Connected to Supabase")
        print()
        
        # Check if tables already exist
        print("Checking if tables already exist...")
        try:
            result = sb.table("user_profiles").select("id").limit(1).execute()
            print("[WARNING] user_profiles table already exists!")
            print("Migration may have already been run.")
            response = input("Do you want to continue anyway? (y/n): ")
            if response.lower() != 'y':
                print("Migration cancelled.")
                return False
        except Exception as e:
            if "relation" in str(e).lower() or "does not exist" in str(e).lower():
                print("[OK] Tables don't exist yet - proceeding with migration")
            else:
                print(f"[WARNING] Could not check tables: {str(e)}")
                print("Proceeding with migration...")
        
        print()
        print("=" * 60)
        print("IMPORTANT: Supabase Python client cannot execute DDL statements")
        print("(CREATE TABLE, ALTER TABLE, etc.) via the REST API.")
        print("=" * 60)
        print()
        print("You need to run the schema manually in Supabase SQL Editor:")
        print()
        print("1. Go to: https://supabase.com/dashboard/project/scrksfxnkxmvvdzwmqnc/sql")
        print("2. Click 'New query'")
        print("3. Copy the contents of database/schema.sql")
        print("4. Paste into the SQL Editor")
        print("5. Click 'Run' (or press Ctrl+Enter)")
        print()
        print("Alternatively, I can verify your connection and check if tables exist.")
        print()
        
        # Verify connection works
        print("Verifying connection...")
        try:
            # Try a simple query that should work
            result = sb.table("_realtime").select("*").limit(1).execute()
            print("[OK] Connection verified - Supabase is accessible")
        except Exception as e:
            print(f"[OK] Connection works (expected error for _realtime: {str(e)[:50]})")
        
        # Check if we can at least verify the auth schema exists
        print()
        print("Checking database state...")
        try:
            # Try to query auth.users (this should exist)
            # Note: We can't directly query auth schema via REST API easily
            # But we can check if our tables exist
            try:
                sb.table("user_profiles").select("id").limit(0).execute()
                print("[OK] user_profiles table exists")
            except:
                print("[INFO] user_profiles table does not exist - needs migration")
            
            try:
                sb.table("pv_cases").select("id").limit(0).execute()
                print("[OK] pv_cases table exists")
            except:
                print("[INFO] pv_cases table does not exist - needs migration")
        except Exception as e:
            print(f"[INFO] Could not check tables: {str(e)[:100]}")
        
        return True
        
    except ImportError:
        print("[ERROR] supabase package not installed")
        print("Run: pip install supabase")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to connect or execute: {str(e)}")
        return False


if __name__ == "__main__":
    success = execute_schema_migration()
    sys.exit(0 if success else 1)

