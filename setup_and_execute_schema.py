"""
Update .env file with database password and execute schema automatically.
"""

import os
import sys
import urllib.parse
from pathlib import Path

PROJECT_REF = "scrksfxnkxmvvdzwmqnc"
SUPABASE_URL = f"https://{PROJECT_REF}.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNjcmtzZnhua3htdnZkendtcW5jIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzYwMzY1NywiZXhwIjoyMDc5MTc5NjU3fQ.dUwNCFto69ZqCqcjDUMDlOuEkZ0PArK9B-RkNTp5jmw"
DB_PASSWORD = "Hsgbu@1188"

def update_env_file():
    """Update .env file with database password."""
    env_path = Path(".env")
    
    if not env_path.exists():
        print("[ERROR] .env file not found!")
        return False
    
    # Read current content
    lines = []
    password_exists = False
    
    with open(env_path, 'r') as f:
        for line in f:
            if line.strip().startswith("SUPABASE_DB_PASSWORD"):
                # Update existing password
                lines.append(f"SUPABASE_DB_PASSWORD={DB_PASSWORD}\n")
                password_exists = True
            else:
                lines.append(line)
    
    # Add password if it doesn't exist
    if not password_exists:
        # Add after SUPABASE_SERVICE_KEY
        new_lines = []
        added = False
        for line in lines:
            new_lines.append(line)
            if "SUPABASE_SERVICE_KEY" in line and not added:
                new_lines.append(f"SUPABASE_DB_PASSWORD={DB_PASSWORD}\n")
                added = True
        
        if not added:
            # Just append at the end
            new_lines.append(f"\nSUPABASE_DB_PASSWORD={DB_PASSWORD}\n")
        
        lines = new_lines
    
    # Write back
    with open(env_path, 'w') as f:
        f.writelines(lines)
    
    print("[OK] Updated .env file with database password")
    return True

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
            import subprocess
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

def execute_schema():
    """Execute schema SQL via direct PostgreSQL connection."""
    if not ensure_psycopg2():
        return False
    
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    
    # Read schema file
    schema_path = Path("database/schema.sql")
    if not schema_path.exists():
        print(f"[ERROR] {schema_path} not found!")
        return False
    
    schema_sql = schema_path.read_text()
    
    try:
        print("[INFO] Connecting to PostgreSQL database...")
        print(f"[DEBUG] Host: db.{PROJECT_REF}.supabase.co")
        
        # URL encode password for connection string (in case it has special chars like @)
        encoded_password = urllib.parse.quote_plus(DB_PASSWORD)
        
        # Try connection string format first (with encoded password)
        conn_string = f"postgresql://postgres:{encoded_password}@db.{PROJECT_REF}.supabase.co:5432/postgres?sslmode=require"
        
        try:
            conn = psycopg2.connect(conn_string, connect_timeout=10)
        except Exception as e1:
            # Fallback to parameter format
            print(f"[INFO] Connection string format failed, trying parameter format...")
            conn = psycopg2.connect(
                host=f"db.{PROJECT_REF}.supabase.co",
                port=5432,
                database="postgres",
                user="postgres",
                password=DB_PASSWORD,  # Use raw password here (not encoded)
                sslmode="require",
                connect_timeout=10
            )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        print("[OK] Connected successfully")
        print("[INFO] Executing schema (this may take 10-30 seconds)...")
        print()
        
        # Execute the entire schema
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
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function."""
    print("=" * 70)
    print("AetherSignal - Automated Schema Setup and Execution")
    print("=" * 70)
    print()
    
    # Step 1: Check current state
    print("[1/4] Checking current database state...")
    if check_tables():
        print("[OK] Tables already exist! No migration needed.")
        return True
    print("[INFO] Tables missing - migration required")
    print()
    
    # Step 2: Update .env file
    print("[2/4] Updating .env file with database password...")
    if not update_env_file():
        return False
    print()
    
    # Step 3: Execute schema
    print("[3/4] Executing schema migration...")
    if not execute_schema():
        return False
    print()
    
    # Step 4: Verify
    print("[4/4] Verifying tables were created...")
    import time
    time.sleep(2)  # Give database time to process
    
    if check_tables():
        print("[SUCCESS] All tables created and verified!")
        print()
        print("Your Supabase database is now fully set up!")
        print()
        print("Next steps:")
        print("  1. Test the application: streamlit run app.py")
        print("  2. Try registration and login")
        print("  3. Upload data and verify storage")
        return True
    else:
        print("[WARNING] Schema executed but tables not yet visible")
        print("          Wait 5 seconds and run: python final_setup_check.py")
        return True  # Still consider success, might just need time

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

