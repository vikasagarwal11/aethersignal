"""
Fully automated schema execution using direct PostgreSQL connection.
This script will attempt to execute the schema using psycopg2.
"""

import os
import sys
import subprocess
import requests
from pathlib import Path

PROJECT_REF = "scrksfxnkxmvvdzwmqnc"
SUPABASE_URL = f"https://{PROJECT_REF}.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNjcmtzZnhua3htdnZkendtcW5jIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzYwMzY1NywiZXhwIjoyMDc5MTc5NjU3fQ.dUwNCFto69ZqCqcjDUMDlOuEkZ0PArK9B-RkNTp5jmw"

def load_env():
    """Load environment variables."""
    env_path = Path(".env")
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

def ensure_psycopg2():
    """Ensure psycopg2 is installed."""
    try:
        import psycopg2
        return True
    except ImportError:
        try:
            import psycopg2_binary
            return True
        except ImportError:
            print("[INFO] Installing psycopg2-binary...")
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "psycopg2-binary", "--quiet"],
                    timeout=120
                )
                import psycopg2
                return True
            except Exception as e:
                print(f"[ERROR] Failed to install psycopg2: {e}")
                return False

def get_password_from_user():
    """Try to get password from user input or environment."""
    # Check environment first
    password = os.getenv("SUPABASE_DB_PASSWORD") or os.getenv("DATABASE_PASSWORD")
    if password:
        return password
    
    # Check if we can get it from Supabase API (unlikely but worth trying)
    # Actually, we can't get password via API for security reasons
    
    print("\n" + "=" * 70)
    print("DATABASE PASSWORD REQUIRED")
    print("=" * 70)
    print()
    print("To execute the schema automatically, I need the database password.")
    print()
    print("Get it from:")
    print(f"  https://supabase.com/dashboard/project/{PROJECT_REF}/settings/database")
    print()
    print("Then either:")
    print("  A) Add to .env file: SUPABASE_DB_PASSWORD=your-password")
    print("  B) Or enter it now (will not be saved)")
    print()
    
    try:
        import getpass
        password = getpass.getpass("Enter database password (or press Enter to skip): ")
        if password:
            return password
    except (EOFError, KeyboardInterrupt):
        pass
    
    return None

def execute_schema_postgres(schema_sql, password):
    """Execute schema using direct PostgreSQL connection."""
    if not ensure_psycopg2():
        return False
    
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    
    conn_string = f"postgresql://postgres:{password}@db.{PROJECT_REF}.supabase.co:5432/postgres"
    
    try:
        print("[INFO] Connecting to PostgreSQL database...")
        conn = psycopg2.connect(conn_string, connect_timeout=10)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        print("[OK] Connected successfully")
        print("[INFO] Executing schema (this may take 10-30 seconds)...")
        print()
        
        # Execute the entire schema
        # Note: psycopg2 execute() can handle multiple statements if we use
        # execute() with the full SQL string
        cur.execute(schema_sql)
        
        print("[OK] Schema SQL executed")
        
        cur.close()
        conn.close()
        
        print("[SUCCESS] Schema migration completed!")
        return True
        
    except psycopg2.OperationalError as e:
        error_msg = str(e).lower()
        if "password authentication failed" in error_msg:
            print("[ERROR] Incorrect database password")
        elif "could not translate host name" in error_msg:
            print("[ERROR] Network error - could not resolve database host")
        else:
            print(f"[ERROR] Connection failed: {str(e)[:150]}")
        return False
    except Exception as e:
        print(f"[ERROR] Execution failed: {str(e)[:150]}")
        # Print more details for debugging
        import traceback
        traceback.print_exc()
        return False

def check_tables():
    """Check if tables exist."""
    try:
        from supabase import create_client
        sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        
        try:
            sb.table("user_profiles").select("id").limit(1).execute()
            sb.table("pv_cases").select("id").limit(1).execute()
            return True
        except:
            return False
    except:
        return False

def main():
    """Main function."""
    print("=" * 70)
    print("AetherSignal - Automated Schema Execution")
    print("=" * 70)
    print()
    
    load_env()
    
    # Check current state
    print("[1/4] Checking database state...")
    if check_tables():
        print("[OK] Tables already exist! No migration needed.")
        return True
    print("[INFO] Tables missing - migration required")
    print()
    
    # Read schema
    print("[2/4] Loading schema file...")
    schema_path = Path("database/schema.sql")
    if not schema_path.exists():
        print(f"[ERROR] {schema_path} not found!")
        return False
    
    schema_sql = schema_path.read_text()
    print(f"[OK] Schema loaded ({len(schema_sql):,} bytes)")
    print()
    
    # Get password
    print("[3/4] Getting database credentials...")
    password = get_password_from_user()
    
    if not password:
        print()
        print("=" * 70)
        print("CANNOT PROCEED - Password Required")
        print("=" * 70)
        print()
        print("To automate this step:")
        print("  1. Get database password from Supabase dashboard")
        print(f"     https://supabase.com/dashboard/project/{PROJECT_REF}/settings/database")
        print("  2. Add to .env: SUPABASE_DB_PASSWORD=your-password")
        print("  3. Run this script again")
        print()
        print("Or run schema manually (2 minutes):")
        print(f"  https://supabase.com/dashboard/project/{PROJECT_REF}/sql")
        return False
    
    print("[OK] Password obtained")
    print()
    
    # Execute
    print("[4/4] Executing schema migration...")
    if execute_schema_postgres(schema_sql, password):
        # Verify
        print()
        print("[VERIFY] Checking tables were created...")
        if check_tables():
            print("[SUCCESS] All tables created and verified!")
            return True
        else:
            print("[WARNING] Execution completed but tables not found")
            print("          Wait 5 seconds and run: python final_setup_check.py")
            return False
    
    return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[Cancelled by user]")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

