"""
Automated Supabase schema setup using HTTP requests to execute SQL.
Uses Supabase REST API to execute schema migration.
"""

import os
import sys
import json
import requests
from pathlib import Path

# Supabase credentials
SUPABASE_URL = "https://scrksfxnkxmvvdzwmqnc.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNjcmtzZnhua3htdnZkendtcW5jIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzYwMzY1NywiZXhwIjoyMDc5MTc5NjU3fQ.dUwNCFto69ZqCqcjDUMDlOuEkZ0PArK9B-RkNTp5jmw"

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

def get_credentials():
    """Get Supabase credentials from env or use defaults."""
    url = os.getenv("SUPABASE_URL", SUPABASE_URL)
    key = os.getenv("SUPABASE_SERVICE_KEY", SUPABASE_SERVICE_KEY)
    return url, key

def check_tables_exist(url, key):
    """Check if the required tables already exist."""
    try:
        from supabase import create_client
        sb = create_client(url, key)
        
        tables_exist = {"user_profiles": False, "pv_cases": False}
        
        for table in tables_exist.keys():
            try:
                sb.table(table).select("id").limit(1).execute()
                tables_exist[table] = True
                print(f"[OK] {table} table exists")
            except Exception as e:
                if "relation" in str(e).lower() or "does not exist" in str(e).lower():
                    print(f"[MISSING] {table} table does not exist")
                else:
                    print(f"[WARNING] Could not check {table}: {str(e)[:80]}")
        
        return all(tables_exist.values()), tables_exist
    except Exception as e:
        print(f"[WARNING] Could not check tables: {str(e)}")
        return False, {}

def execute_schema_via_rpc(url, key, schema_sql):
    """
    Try to execute schema using Supabase RPC function or Management API.
    Note: Supabase REST API doesn't support DDL directly, but we can try
    using the Management API endpoint.
    """
    # Extract project ref from URL
    project_ref = url.replace("https://", "").replace(".supabase.co", "")
    
    # Try Management API endpoint (requires access token, not service key)
    # This won't work with service key alone
    
    # Alternative: Use Supabase CLI approach or direct Postgres connection
    print("[INFO] Direct HTTP execution of DDL not supported by Supabase REST API")
    return False

def create_migration_file():
    """Create a Supabase migration file that can be applied via CLI."""
    schema_path = Path("database/schema.sql")
    if not schema_path.exists():
        print(f"[ERROR] {schema_path} not found!")
        return False
    
    # Check if supabase directory exists
    supabase_dir = Path("supabase")
    migrations_dir = supabase_dir / "migrations"
    
    # Create directories if needed
    migrations_dir.mkdir(parents=True, exist_ok=True)
    
    # Create migration file
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    migration_file = migrations_dir / f"{timestamp}_initial_schema.sql"
    
    # Read and copy schema
    schema_content = schema_path.read_text()
    migration_file.write_text(schema_content)
    
    print(f"[OK] Created migration file: {migration_file}")
    return True, migration_file

def execute_schema_via_cli_with_instructions():
    """Provide instructions and attempt CLI execution."""
    print("=" * 60)
    print("Attempting Automated Schema Setup")
    print("=" * 60)
    print()
    
    # Check if CLI is available
    import subprocess
    
    try:
        result = subprocess.run(
            ["supabase", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            cli_version = result.stdout.strip()
            print(f"[OK] Supabase CLI found: {cli_version}")
        else:
            print("[WARNING] Supabase CLI not working properly")
            return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("[WARNING] Supabase CLI not in PATH")
        print("         You may need to restart your terminal")
        print("         Or use: $env:Path += \";$HOME\\scoop\\shims\"")
        return False
    
    # Create migration file
    success, migration_file = create_migration_file()
    if not success:
        return False
    
    print()
    print("=" * 60)
    print("Next Steps (CLI Approach)")
    print("=" * 60)
    print()
    print("To apply the migration using CLI:")
    print()
    print("1. Link to your Supabase project:")
    print("   supabase link --project-ref scrksfxnkxmvvdzwmqnc")
    print("   (You'll need your database password)")
    print()
    print("2. Apply the migration:")
    print("   supabase db push")
    print()
    print("OR use the SQL Editor approach (see below)")
    print()
    
    return True

def main():
    """Main execution function."""
    print("=" * 60)
    print("AetherSignal - Automated Supabase Schema Setup")
    print("=" * 60)
    print()
    
    # Load environment
    load_env()
    url, key = get_credentials()
    
    print(f"Project: scrksfxnkxmvvdzwmqnc")
    print(f"URL: {url}")
    print()
    
    # Check current state
    print("=" * 60)
    print("Checking Current Database State")
    print("=" * 60)
    print()
    
    all_exist, table_status = check_tables_exist(url, key)
    
    if all_exist:
        print()
        print("=" * 60)
        print("[SUCCESS] All tables already exist!")
        print("=" * 60)
        print()
        print("Your database schema is already set up.")
        print("No migration needed.")
        return True
    
    print()
    print("=" * 60)
    print("Schema Migration Required")
    print("=" * 60)
    print()
    
    # Read schema file
    schema_path = Path("database/schema.sql")
    if not schema_path.exists():
        print(f"[ERROR] {schema_path} not found!")
        return False
    
    schema_sql = schema_path.read_text()
    print(f"[OK] Schema file ready: {len(schema_sql):,} bytes")
    print()
    
    # Since Supabase REST API doesn't support DDL, we have two options:
    # 1. Use SQL Editor (manual but reliable)
    # 2. Use Supabase CLI (automated but requires linking)
    
    print("=" * 60)
    print("OPTION 1: SQL Editor (Recommended - Fastest)")
    print("=" * 60)
    print()
    print("1. Open: https://supabase.com/dashboard/project/scrksfxnkxmvvdzwmqnc/sql")
    print("2. Click 'New query'")
    print("3. Copy the SQL below (or from database/schema.sql):")
    print()
    print("-" * 60)
    print("COPY THIS SQL:")
    print("-" * 60)
    print()
    # Print first 500 chars as preview
    print(schema_sql[:500] + "\n... (full SQL in database/schema.sql)")
    print()
    print("-" * 60)
    print("4. Paste into SQL Editor and click 'Run' (Ctrl+Enter)")
    print("5. Verify tables were created in 'Table Editor'")
    print()
    
    # Create migration file for CLI option
    print("=" * 60)
    print("OPTION 2: Supabase CLI (For Future Changes)")
    print("=" * 60)
    print()
    
    success, migration_file = create_migration_file()
    if success:
        print(f"[OK] Migration file created: {migration_file}")
        print()
        print("To use CLI in the future:")
        print("  1. Link: supabase link --project-ref scrksfxnkxmvvdzwmqnc")
        print("  2. Push: supabase db push")
        print()
    
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print()
    print("Since Supabase REST API doesn't support DDL statements,")
    print("please use OPTION 1 (SQL Editor) to run the schema.")
    print()
    print("After running the schema, verify with:")
    print("  python check_and_setup_database.py")
    print()
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

