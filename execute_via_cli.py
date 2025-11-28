"""Execute schema using Supabase CLI - this bypasses DNS issues."""

import sys
import os
import subprocess
from pathlib import Path

PROJECT_REF = "scrksfxnkxmvvdzwmqnc"
DB_PASSWORD = "Hsgbu@118811"

print("=" * 70)
print("Executing Schema via Supabase CLI")
print("=" * 70)
print()

# Check if CLI is available
print("[1/4] Checking Supabase CLI...")
import os
# Add Scoop shims to PATH
if os.environ.get("PATH"):
    scoop_path = os.path.join(os.environ.get("USERPROFILE", ""), "scoop", "shims")
    if os.path.exists(scoop_path) and scoop_path not in os.environ["PATH"]:
        os.environ["PATH"] = os.environ["PATH"] + os.pathsep + scoop_path

cli_path = "supabase"
# Try to find CLI
possible_paths = [
    "supabase",
    os.path.join(os.environ.get("USERPROFILE", ""), "scoop", "shims", "supabase.exe"),
    "C:\\Users\\vikas\\scoop\\shims\\supabase.exe"
]

for path in possible_paths:
    try:
        result = subprocess.run(
            [path, "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            cli_path = path
            break
    except:
        continue

try:
    result = subprocess.run(
        [cli_path, "--version"],
        capture_output=True,
        text=True,
        timeout=5
    )
    if result.returncode == 0:
        print(f"  [OK] Supabase CLI found: {result.stdout.strip()}")
    else:
        print("  [ERROR] Supabase CLI not working")
        sys.exit(1)
except FileNotFoundError:
    print("  [ERROR] Supabase CLI not found in PATH")
    print("  Install it first or use SQL Editor approach")
    sys.exit(1)
except Exception as e:
    print(f"  [ERROR] {str(e)}")
    sys.exit(1)

# Check if project is linked
print()
print("[2/4] Checking if project is linked...")
config_path = Path("supabase/.temp/project-ref")
if config_path.exists():
    linked_ref = config_path.read_text().strip()
    print(f"  [OK] Project is linked: {linked_ref}")
    if linked_ref != PROJECT_REF:
        print(f"  [WARNING] Linked to different project: {linked_ref}")
        print("  Will try to use current project anyway...")
else:
    print("  [INFO] Project not linked yet")
    print("  Attempting to link...")
    
    # Try to link (non-interactive with password)
    try:
        # Create a temporary script to pipe password
        link_cmd = f'echo {DB_PASSWORD} | supabase link --project-ref {PROJECT_REF}'
        result = subprocess.run(
            link_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print("  [OK] Project linked successfully!")
        else:
            print(f"  [WARNING] Linking failed: {result.stderr[:200]}")
            print("  Will try to push anyway...")
    except Exception as e:
        print(f"  [WARNING] Could not link automatically: {str(e)}")
        print("  You may need to link manually:")
        print(f"    supabase link --project-ref {PROJECT_REF}")

# Check migration file
print()
print("[3/4] Checking migration file...")
migration_dir = Path("supabase/migrations")
migrations = list(migration_dir.glob("*.sql")) if migration_dir.exists() else []

if migrations:
    latest = max(migrations, key=lambda p: p.stat().st_mtime)
    print(f"  [OK] Migration file ready: {latest.name}")
    
    # Verify it has content
    content = latest.read_text()
    if "user_profiles" in content and "pv_cases" in content:
        print("  [OK] Migration file contains schema")
    else:
        print("  [WARNING] Migration file might be incomplete")
else:
    print("  [ERROR] No migration files found!")
    print("  Creating migration file...")
    
    migration_dir.mkdir(parents=True, exist_ok=True)
    schema_path = Path("database/schema.sql")
    if not schema_path.exists():
        print("  [ERROR] database/schema.sql not found!")
        sys.exit(1)
    
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    migration_file = migration_dir / f"{timestamp}_initial_schema.sql"
    migration_file.write_text(schema_path.read_text())
    print(f"  [OK] Created: {migration_file.name}")

# Push migration
print()
print("[4/4] Pushing migration to Supabase...")
print("  This will execute the schema on your database...")
print()

try:
    # Set password in environment for non-interactive use
    env = os.environ.copy()
    # Note: CLI will prompt for password if needed
    
    result = subprocess.run(
        [cli_path, "db", "push"],
        capture_output=True,
        text=True,
        timeout=120,
        input=f"{DB_PASSWORD}\n"  # Try to provide password
    )
    
    print(result.stdout)
    
    if result.returncode == 0:
        print()
        print("=" * 70)
        print("[SUCCESS] Migration pushed successfully!")
        print("=" * 70)
        print()
        print("Verifying tables...")
        
        # Verify via REST API
        import time
        time.sleep(2)
        
        try:
            from supabase import create_client
            SUPABASE_URL = f"https://{PROJECT_REF}.supabase.co"
            SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNjcmtzZnhua3htdnZkendtcW5jIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzYwMzY1NywiZXhwIjoyMDc5MTc5NjU3fQ.dUwNCFto69ZqCqcjDUMDlOuEkZ0PArK9B-RkNTp5jmw"
            sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
            
            try:
                sb.table("user_profiles").select("id").limit(1).execute()
                print("  [OK] user_profiles table exists")
                user_ok = True
            except:
                print("  [WARNING] user_profiles table not found")
                user_ok = False
            
            try:
                sb.table("pv_cases").select("id").limit(1).execute()
                print("  [OK] pv_cases table exists")
                pv_ok = True
            except:
                print("  [WARNING] pv_cases table not found")
                pv_ok = False
            
            if user_ok and pv_ok:
                print()
                print("[SUCCESS] All tables verified! Database is ready!")
                sys.exit(0)
            
        except Exception as e:
            print(f"  [INFO] Could not verify: {str(e)[:100]}")
        
        print()
        print("Run verification: python final_setup_check.py")
        sys.exit(0)
    else:
        print()
        print("=" * 70)
        print("[ERROR] Migration push failed")
        print("=" * 70)
        print()
        print("Error output:")
        print(result.stderr)
        print()
        print("This might require manual linking first:")
        print(f"  supabase link --project-ref {PROJECT_REF}")
        print("  (Enter password when prompted: {DB_PASSWORD})")
        print()
        print("Or use SQL Editor approach (2 minutes):")
        print(f"  https://supabase.com/dashboard/project/{PROJECT_REF}/sql")
        sys.exit(1)
        
except subprocess.TimeoutExpired:
    print("  [ERROR] Command timed out")
    sys.exit(1)
except Exception as e:
    print(f"  [ERROR] {str(e)}")
    sys.exit(1)

