"""
Automated Supabase schema execution using direct PostgreSQL connection.
This script executes the schema.sql file directly via psycopg2.
"""

import os
import sys
import subprocess
from pathlib import Path

PROJECT_REF = "scrksfxnkxmvvdzwmqnc"
SUPABASE_URL = f"https://{PROJECT_REF}.supabase.co"
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

def install_package(package):
    """Install a Python package."""
    print(f"[INFO] Installing {package}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--quiet"], 
                            timeout=120)
        print(f"[OK] {package} installed")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to install {package}: {str(e)}")
        return False

def check_package(package_name):
    """Check if package is installed."""
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False

def get_database_password():
    """Try to get database password from various sources."""
    # Check environment variables
    password = os.getenv("SUPABASE_DB_PASSWORD") or os.getenv("DATABASE_PASSWORD")
    if password:
        return password
    
    # Check .env file
    load_env()
    password = os.getenv("SUPABASE_DB_PASSWORD") or os.getenv("DATABASE_PASSWORD")
    if password:
        return password
    
    return None

def execute_via_postgres(schema_sql, db_password):
    """Execute schema SQL via direct PostgreSQL connection using psycopg2."""
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    except ImportError:
        print("[ERROR] psycopg2 not installed")
        return False
    
    conn_string = f"postgresql://postgres:{db_password}@db.{PROJECT_REF}.supabase.co:5432/postgres"
    
    try:
        print("[INFO] Connecting to PostgreSQL database...")
        conn = psycopg2.connect(conn_string, connect_timeout=10)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        print("[OK] Connected successfully")
        print("[INFO] Executing schema SQL...")
        
        # Execute the entire schema as one block
        # psycopg2 can handle multiple statements
        cur.execute(schema_sql)
        
        cur.close()
        conn.close()
        
        print("[SUCCESS] Schema executed successfully!")
        return True
        
    except psycopg2.OperationalError as e:
        error_msg = str(e).lower()
        if "password authentication failed" in error_msg:
            print("[ERROR] Incorrect database password")
        elif "could not translate host name" in error_msg:
            print("[ERROR] Could not resolve database host")
        else:
            print(f"[ERROR] Connection failed: {str(e)}")
        return False
    except Exception as e:
        print(f"[ERROR] Execution failed: {str(e)}")
        return False

def execute_via_cli():
    """Try to execute schema using Supabase CLI."""
    # Check if CLI is available
    try:
        result = subprocess.run(["supabase", "--version"], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
    
    # Check if project is linked
    config_path = Path("supabase/.temp/project-ref")
    if not config_path.exists():
        print("[INFO] Project not linked to CLI yet")
        print("[INFO] To link, run: supabase link --project-ref scrksfxnkxmvvdzwmqnc")
        return False
    
    # Try to push migrations
    try:
        print("[INFO] Attempting to push migration via CLI...")
        result = subprocess.run(["supabase", "db", "push"], 
                              capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("[SUCCESS] Migration pushed successfully via CLI!")
            return True
        else:
            print(f"[WARNING] CLI push failed: {result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print("[ERROR] CLI push timed out")
        return False
    except Exception as e:
        print(f"[ERROR] CLI push failed: {str(e)}")
        return False

def check_tables_exist():
    """Check if tables exist."""
    try:
        from supabase import create_client
        sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        
        user_exists = False
        pv_exists = False
        
        try:
            sb.table("user_profiles").select("id").limit(1).execute()
            user_exists = True
        except:
            pass
        
        try:
            sb.table("pv_cases").select("id").limit(1).execute()
            pv_exists = True
        except:
            pass
        
        return user_exists and pv_exists
    except:
        return False

def main():
    """Main execution function."""
    print("=" * 70)
    print("AetherSignal - Automated Schema Execution")
    print("=" * 70)
    print()
    
    load_env()
    
    # Check if tables already exist
    print("[1/5] Checking if tables already exist...")
    if check_tables_exist():
        print("[OK] Tables already exist! No migration needed.")
        return True
    print("[INFO] Tables missing - migration required")
    print()
    
    # Read schema file
    print("[2/5] Reading schema file...")
    schema_path = Path("database/schema.sql")
    if not schema_path.exists():
        print(f"[ERROR] {schema_path} not found!")
        return False
    
    schema_sql = schema_path.read_text()
    print(f"[OK] Schema file loaded ({len(schema_sql):,} bytes)")
    print()
    
    # Try method 1: Direct PostgreSQL connection
    print("[3/5] Trying direct PostgreSQL connection...")
    db_password = get_database_password()
    
    if db_password:
        print("[INFO] Database password found in environment")
        
        # Install psycopg2 if needed
        if not check_package("psycopg2") and not check_package("psycopg2_binary"):
            if not install_package("psycopg2-binary"):
                print("[ERROR] Could not install psycopg2-binary")
                db_password = None  # Try other method
        
        if db_password and (check_package("psycopg2") or check_package("psycopg2_binary")):
            if execute_via_postgres(schema_sql, db_password):
                # Verify
                print()
                print("[4/5] Verifying tables were created...")
                if check_tables_exist():
                    print("[SUCCESS] All tables created successfully!")
                    return True
                else:
                    print("[WARNING] Tables may not have been created correctly")
    
    print("[INFO] Direct connection method not available")
    print()
    
    # Try method 2: Supabase CLI
    print("[4/5] Trying Supabase CLI method...")
    if execute_via_cli():
        print()
        print("[5/5] Verifying tables were created...")
        if check_tables_exist():
            print("[SUCCESS] All tables created successfully!")
            return True
    
    print("[INFO] CLI method not available")
    print()
    
    # Final instructions
    print("=" * 70)
    print("AUTOMATED EXECUTION NOT POSSIBLE")
    print("=" * 70)
    print()
    print("To execute the schema automatically, you need:")
    print()
    print("OPTION A: Database Password")
    print("  1. Get password from:")
    print(f"     https://supabase.com/dashboard/project/{PROJECT_REF}/settings/database")
    print("  2. Add to .env file:")
    print("     SUPABASE_DB_PASSWORD=your-password")
    print("  3. Run this script again")
    print()
    print("OPTION B: Supabase CLI")
    print("  1. Link project:")
    print("     supabase link --project-ref scrksfxnkxmvvdzwmqnc")
    print("  2. Run this script again")
    print()
    print("OPTION C: Manual (2 minutes)")
    print("  1. Go to: https://supabase.com/dashboard/project/scrksfxnkxmvvdzwmqnc/sql")
    print("  2. Copy contents of database/schema.sql")
    print("  3. Paste and run")
    print()
    
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
        import traceback
        traceback.print_exc()
        sys.exit(1)

