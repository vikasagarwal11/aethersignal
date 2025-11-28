"""
Complete automated Supabase schema setup.
This script handles all steps: checking, installing dependencies, and executing schema.
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

def check_package(package_name):
    """Check if a Python package is installed."""
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False

def install_package(package_name):
    """Install a Python package using pip."""
    print(f"[INFO] Installing {package_name}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name, "--quiet"])
        print(f"[OK] {package_name} installed")
        return True
    except subprocess.CalledProcessError:
        print(f"[ERROR] Failed to install {package_name}")
        return False

def check_tables_exist():
    """Check if required tables exist using Supabase REST API."""
    try:
        from supabase import create_client
        sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        
        tables = {"user_profiles": False, "pv_cases": False}
        
        for table in tables.keys():
            try:
                sb.table(table).select("id").limit(1).execute()
                tables[table] = True
                print(f"[OK] {table} table exists")
            except Exception as e:
                error_msg = str(e).lower()
                if "relation" in error_msg or "does not exist" in error_msg:
                    print(f"[MISSING] {table} table does not exist")
                else:
                    print(f"[WARNING] Could not check {table}: {str(e)[:60]}")
        
        return all(tables.values()), tables
    except Exception as e:
        print(f"[WARNING] Could not check tables: {str(e)}")
        return False, {}

def execute_schema_via_postgres(schema_sql, db_password):
    """Execute schema SQL via direct PostgreSQL connection."""
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    except ImportError:
        print("[ERROR] psycopg2 not available")
        return False
    
    conn_string = f"postgresql://postgres:{db_password}@db.{PROJECT_REF}.supabase.co:5432/postgres"
    
    try:
        print("[INFO] Connecting to Postgres database...")
        conn = psycopg2.connect(conn_string, connect_timeout=10)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        print("[OK] Connected successfully")
        print("[INFO] Executing schema SQL...")
        print()
        
        # Execute the entire schema SQL
        # Split by semicolon, but preserve multi-line statements
        statements = []
        current_statement = []
        for line in schema_sql.split('\n'):
            stripped = line.strip()
            # Skip empty lines and comments at start
            if not stripped or stripped.startswith('--'):
                continue
            
            current_statement.append(line)
            
            # Check if line ends with semicolon (end of statement)
            if stripped.endswith(';'):
                full_statement = '\n'.join(current_statement)
                if full_statement.strip():
                    statements.append(full_statement)
                current_statement = []
        
        # Add any remaining statement
        if current_statement:
            full_statement = '\n'.join(current_statement)
            if full_statement.strip():
                statements.append(full_statement)
        
        executed = 0
        errors = 0
        
        for i, statement in enumerate(statements, 1):
            if not statement.strip():
                continue
                
            try:
                cur.execute(statement)
                executed += 1
                if i % 5 == 0:  # Print progress every 5 statements
                    print(f"[PROGRESS] Executed {executed} statements...")
            except Exception as e:
                error_msg = str(e).lower()
                # Ignore "already exists" errors (IF NOT EXISTS clauses)
                if "already exists" in error_msg or "duplicate" in error_msg:
                    executed += 1
                    continue
                else:
                    errors += 1
                    print(f"[WARNING] Statement {i} error: {str(e)[:100]}")
        
        cur.close()
        conn.close()
        
        print()
        print(f"[SUCCESS] Executed {executed} statements")
        if errors > 0:
            print(f"[WARNING] {errors} statements had errors (may be expected)")
        
        return True
        
    except psycopg2.OperationalError as e:
        print(f"[ERROR] Connection failed: {str(e)}")
        if "password authentication failed" in str(e).lower():
            print("        Incorrect database password")
        elif "could not translate host name" in str(e).lower():
            print("        Could not resolve database host")
        else:
            print("        Check your database connection settings")
        return False
    except Exception as e:
        print(f"[ERROR] Execution failed: {str(e)}")
        return False

def main():
    """Main execution function."""
    print("=" * 70)
    print("AetherSignal - Complete Supabase Schema Setup")
    print("=" * 70)
    print()
    
    # Load environment
    load_env()
    
    # Override with env vars if available
    global SUPABASE_URL, SUPABASE_SERVICE_KEY
    SUPABASE_URL = os.getenv("SUPABASE_URL", SUPABASE_URL)
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", SUPABASE_SERVICE_KEY)
    
    print(f"Project: {PROJECT_REF}")
    print(f"URL: {SUPABASE_URL}")
    print()
    
    # Step 1: Check if supabase package is installed
    print("=" * 70)
    print("Step 1: Checking Dependencies")
    print("=" * 70)
    print()
    
    if not check_package("supabase"):
        print("[INFO] Installing supabase package...")
        if not install_package("supabase"):
            print("[ERROR] Failed to install supabase package")
            return False
    else:
        print("[OK] supabase package is installed")
    
    print()
    
    # Step 2: Check current database state
    print("=" * 70)
    print("Step 2: Checking Current Database State")
    print("=" * 70)
    print()
    
    all_exist, table_status = check_tables_exist()
    
    if all_exist:
        print()
        print("=" * 70)
        print("[SUCCESS] All tables already exist!")
        print("=" * 70)
        print()
        print("Your database schema is already set up.")
        print("No migration needed.")
        return True
    
    print()
    print("[INFO] Tables are missing - migration required")
    print()
    
    # Step 3: Read schema file
    print("=" * 70)
    print("Step 3: Preparing Schema Migration")
    print("=" * 70)
    print()
    
    schema_path = Path("database/schema.sql")
    if not schema_path.exists():
        print(f"[ERROR] {schema_path} not found!")
        return False
    
    schema_sql = schema_path.read_text()
    print(f"[OK] Schema file loaded: {len(schema_sql):,} bytes")
    print(f"[OK] Found {schema_sql.count('CREATE TABLE')} table definitions")
    print()
    
    # Step 4: Get database password
    print("=" * 70)
    print("Step 4: Database Connection Setup")
    print("=" * 70)
    print()
    
    db_password = os.getenv("SUPABASE_DB_PASSWORD") or os.getenv("DATABASE_PASSWORD")
    
    if not db_password:
        print("[INFO] Database password not found in environment")
        print()
        print("To execute the schema automatically, we need the database password.")
        print()
        print("Get it from:")
        print(f"  https://supabase.com/dashboard/project/{PROJECT_REF}/settings/database")
        print()
        print("You can:")
        print("  1. Add to .env file: SUPABASE_DB_PASSWORD=your-password")
        print("  2. Or enter it now (won't be saved)")
        print()
        
        try:
            import getpass
            password = getpass.getpass("Enter database password (or press Enter to skip): ")
            if password:
                db_password = password
            else:
                print()
                print("[SKIP] No password provided - cannot execute schema automatically")
                print()
                print("Please run the schema manually:")
                print(f"  1. Go to: https://supabase.com/dashboard/project/{PROJECT_REF}/sql")
                print("  2. Copy contents of database/schema.sql")
                print("  3. Paste and run")
                return False
        except (EOFError, KeyboardInterrupt):
            print("\n[SKIP] Password input cancelled")
            return False
    else:
        print("[OK] Database password found in environment")
    
    # Step 5: Install psycopg2 if needed
    print()
    print("=" * 70)
    print("Step 5: Installing Database Driver")
    print("=" * 70)
    print()
    
    if not check_package("psycopg2") and not check_package("psycopg2_binary"):
        print("[INFO] Installing psycopg2-binary (PostgreSQL driver)...")
        if not install_package("psycopg2-binary"):
            print("[ERROR] Failed to install psycopg2-binary")
            print("        Install manually: pip install psycopg2-binary")
            return False
    else:
        print("[OK] psycopg2 is installed")
    
    # Step 6: Execute schema
    print()
    print("=" * 70)
    print("Step 6: Executing Schema Migration")
    print("=" * 70)
    print()
    
    if execute_schema_via_postgres(schema_sql, db_password):
        # Step 7: Verify
        print()
        print("=" * 70)
        print("Step 7: Verifying Schema Creation")
        print("=" * 70)
        print()
        
        all_exist_after, table_status_after = check_tables_exist()
        
        if all_exist_after:
            print()
            print("=" * 70)
            print("[SUCCESS] Schema migration completed successfully!")
            print("=" * 70)
            print()
            print("All tables have been created:")
            for table in table_status_after.keys():
                if table_status_after[table]:
                    print(f"  ✓ {table}")
            print()
            print("Next steps:")
            print("  1. Update .env file with Supabase credentials (if not already done)")
            print("  2. Test registration and login")
            print("  3. Upload data and verify storage")
            return True
        else:
            print()
            print("[WARNING] Migration executed, but some tables may be missing")
            print("          Please verify manually in Supabase dashboard")
            return False
    else:
        print()
        print("[ERROR] Schema migration failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

