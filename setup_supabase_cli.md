# Supabase CLI Setup Guide

## Install Supabase CLI

If not installed, run:

**Windows (PowerShell):**
```powershell
# Using Scoop (recommended)
scoop bucket add supabase https://github.com/supabase/scoop-bucket.git
scoop install supabase

# Or using npm
npm install -g supabase
```

**Or download directly:**
- Go to: https://github.com/supabase/cli/releases
- Download Windows binary
- Add to PATH

**Verify installation:**
```bash
supabase --version
```

---

## Initialize Supabase in Project

Once CLI is installed, run:

```bash
supabase init
```

This creates:
- `supabase/` folder
- `supabase/config.toml` - Configuration
- `supabase/migrations/` - Migration files

---

## Link to Your Project

```bash
supabase link --project-ref scrksfxnkxmvvdzwmqnc
```

You'll need to provide:
- Database password (from when you created the project)
- Or use access token

---

## Create Migration from schema.sql

```bash
supabase migration new initial_schema
```

This creates a file like: `supabase/migrations/20250127123456_initial_schema.sql`

Copy contents of `database/schema.sql` into this migration file.

---

## Apply Migration

```bash
supabase db push
```

This will apply all migrations to your Supabase project!

---

## Future Schema Changes

1. **Make changes locally:**
   ```bash
   supabase db diff -f new_feature
   ```
   This creates a new migration file with your changes.

2. **Apply changes:**
   ```bash
   supabase db push
   ```

3. **Or generate from local database:**
   ```bash
   supabase db diff --schema public -f add_new_table
   ```

---

## Benefits

✅ **Automated migrations** - No manual SQL Editor  
✅ **Version control** - All migrations in git  
✅ **Rollback support** - Can revert changes  
✅ **Team collaboration** - Everyone uses same migrations  
✅ **CI/CD ready** - Can automate in pipelines  

---

## Quick Start Commands

```bash
# 1. Install CLI (if not installed)
npm install -g supabase

# 2. Initialize project
supabase init

# 3. Link to your project
supabase link --project-ref scrksfxnkxmvvdzwmqnc

# 4. Create initial migration
supabase migration new initial_schema

# 5. Copy database/schema.sql content to the new migration file

# 6. Apply migration
supabase db push
```

---

## Migration Workflow

**For future changes:**

1. Make changes in Supabase Studio (or locally)
2. Generate migration:
   ```bash
   supabase db diff -f descriptive_name
   ```
3. Review the generated migration file
4. Apply:
   ```bash
   supabase db push
   ```

**Or make changes locally:**

1. Edit schema in `supabase/migrations/`
2. Test locally:
   ```bash
   supabase start  # Starts local Supabase
   ```
3. Apply to production:
   ```bash
   supabase db push
   ```

