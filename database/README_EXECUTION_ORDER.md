# Database Scripts Execution Order

This document lists all database scripts in the order they should be executed.

## 📋 Execution Order

### **00_schema.sql** - Base Schema (MUST RUN FIRST)
- Creates `user_profiles` table with roles (including `super_admin`)
- Creates `pv_cases` table
- Sets up RLS policies
- Creates functions and triggers
- **Dependencies:** None (base schema)

### **01_migration_add_super_admin_role.sql** - Migration for Existing Databases
- Updates role constraint to include `super_admin`
- **Dependencies:** Requires `user_profiles` table to exist
- **Note:** Only run this if you have an existing database. For new databases, `00_schema.sql` already includes `super_admin`

### **02_schema_extensions.sql** - Schema Extensions
- Creates `saved_queries` table
- Creates `query_history` table
- Creates `activity_logs` table
- Sets up RLS policies for new tables
- **Dependencies:** Requires `00_schema.sql` (uses `user_profiles`)

### **03_schema_tenant_upgrade.sql** - Tenant Support
- Creates `tenants` table
- Creates `user_tenants` table
- Adds `tenant_id` columns to existing tables
- Sets up tenant-aware RLS policies
- **Dependencies:** Requires `00_schema.sql` (modifies `user_profiles` and `pv_cases`)

### **04_org_profile_config_schema.sql** - Organization Profile Config
- Creates `org_profile_config` table for PSUR/DSUR configuration
- Sets up RLS policies
- **Dependencies:** Requires `00_schema.sql` (references `user_profiles.organization`)

### **05_unified_ae_schema.sql** - Unified AE Events
- Creates `ae_events` table for unified adverse event storage
- Sets up indexes and RLS
- **Dependencies:** Can run independently, but uses extensions (pgvector)

### **06_public_ae_data_schema.sql** - Public AE Data
- Creates `public_ae_data` table for public data platform
- **Dependencies:** None (independent table)

### **07_performance_indexes.sql** - Performance Indexes
- Creates critical performance indexes (10-20x faster queries)
- Includes: user_drug_reaction, created_at_org, event_date, serious_outcome
- **Dependencies:** Requires `00_schema.sql` (indexes `pv_cases` table)

### **08_file_upload_history.sql** - File Upload Tracking
- Creates `file_upload_history` table
- Tracks file uploads, processing status, and metadata
- **Dependencies:** Requires `00_schema.sql` (references `user_profiles`)

### **09_additional_performance_indexes.sql** - Additional Production Indexes
- Documents indexes created in production but not yet in migration scripts
- Includes: org_date_range, serious_drug_reaction (enhanced versions)
- **Dependencies:** Requires `07_performance_indexes.sql`

## 🚀 Quick Start

### For New Databases:
```sql
-- Run in this order:
1. 00_schema.sql (REQUIRED - base schema)
2. 07_performance_indexes.sql (RECOMMENDED - 10-20x faster queries)
3. 09_additional_performance_indexes.sql (RECOMMENDED - additional indexes)
4. 02_schema_extensions.sql (optional)
5. 03_schema_tenant_upgrade.sql (optional)
6. 04_org_profile_config_schema.sql (optional)
7. 05_unified_ae_schema.sql (optional)
8. 06_public_ae_data_schema.sql (optional)
9. 08_file_upload_history.sql (optional)
```

### For Existing Databases:
```sql
-- Run in this order:
1. 01_migration_add_super_admin_role.sql (to add super_admin role)
2. Then run any of 02-06 if you need those features
```

## ⚠️ Important Notes

1. **Always run `00_schema.sql` first** - It's the foundation
2. **Migration script (`01_`) is only for existing databases** - Skip for new setups
3. **Scripts 02-06 are optional** - Only run if you need those features
4. **Scripts are idempotent** - Safe to run multiple times (uses `IF NOT EXISTS`)
5. **Check dependencies** - Some scripts modify existing tables from `00_schema.sql`

## 📝 After Running Scripts

After running `00_schema.sql` or `01_migration_add_super_admin_role.sql`, promote your account to super_admin:

```sql
UPDATE user_profiles
SET role = 'super_admin'
WHERE email = 'YOUR_EMAIL_HERE';
```

Verify:
```sql
SELECT email, role FROM user_profiles WHERE role = 'super_admin';
```

