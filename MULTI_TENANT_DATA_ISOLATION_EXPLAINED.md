# Multi-Tenant Data Isolation - How It Works

## Your Question

**If there are 2 users from ABC company and 2 users from XYZ company, is data maintained per company or per user?**

## Answer: **PER COMPANY** (with user tracking)

The data is **shared within each company**, but each record tracks which user uploaded it.

---

## How It Works

### Example Scenario

```
Company ABC (Organization: "ABC")
  ├── User 1 (user_id: uuid-1)
  │   └── Uploads: 100 cases
  └── User 2 (user_id: uuid-2)
      └── Uploads: 50 cases
      
Company XYZ (Organization: "XYZ")
  ├── User 3 (user_id: uuid-3)
  │   └── Uploads: 75 cases
  └── User 4 (user_id: uuid-4)
      └── Uploads: 25 cases
```

### What Each User Sees

**User 1 (ABC):**
- ✅ Sees: 150 cases total (100 from User 1 + 50 from User 2)
- ❌ Cannot see: Any data from XYZ company

**User 2 (ABC):**
- ✅ Sees: 150 cases total (100 from User 1 + 50 from User 2)
- ❌ Cannot see: Any data from XYZ company

**User 3 (XYZ):**
- ✅ Sees: 100 cases total (75 from User 3 + 25 from User 4)
- ❌ Cannot see: Any data from ABC company

**User 4 (XYZ):**
- ✅ Sees: 100 cases total (75 from User 3 + 25 from User 4)
- ❌ Cannot see: Any data from ABC company

---

## Database Structure

### Each Record Has:

1. **`user_id`** - Which user uploaded this record
2. **`organization`** - Which company owns this record

### Example Data in `pv_cases` Table:

| id | user_id | organization | drug_name | reaction | ... |
|----|---------|--------------|-----------|----------|-----|
| 1  | uuid-1  | ABC          | Aspirin   | Headache | ... |
| 2  | uuid-1  | ABC          | Ibuprofen | Nausea   | ... |
| 3  | uuid-2  | ABC          | Aspirin   | Dizziness| ... |
| 4  | uuid-3  | XYZ          | Aspirin   | Headache | ... |
| 5  | uuid-4  | XYZ          | Ibuprofen | Rash     | ... |

---

## Row-Level Security (RLS) Policy

Looking at the schema (lines 97-106), the RLS policy allows users to see data if:

```sql
auth.uid() = user_id OR  -- Their own data
EXISTS (
    SELECT 1 FROM user_profiles
    WHERE user_profiles.id = auth.uid()
    AND user_profiles.organization = pv_cases.organization
)  -- OR same organization
```

**Translation:**
- Users can see their **own records** (`user_id` matches)
- Users can see **all records from their company** (same `organization`)

---

## Key Points

### ✅ **Data Sharing Within Company**
- All users from ABC can see all ABC data
- All users from XYZ can see all XYZ data
- This allows collaboration within a company

### ✅ **Data Isolation Between Companies**
- ABC users **CANNOT** see XYZ data
- XYZ users **CANNOT** see ABC data
- Complete isolation at database level

### ✅ **User Tracking**
- Each record still has `user_id` field
- You know **who uploaded** each record
- Useful for audit trails and analytics

### ✅ **Automatic Enforcement**
- RLS policies enforce this automatically
- No code changes needed
- Prevents accidental data leakage

---

## Real-World Example

**Scenario:**
- ABC Pharma has 2 scientists: Dr. Smith and Dr. Jones
- XYZ Biotech has 1 scientist: Dr. Brown

**What Happens:**

1. **Dr. Smith (ABC)** uploads 100 FAERS cases
   - Data stored with: `user_id = smith-uuid`, `organization = "ABC"`

2. **Dr. Jones (ABC)** logs in
   - ✅ Can see all 100 cases from Dr. Smith
   - ✅ Can upload his own cases (which Dr. Smith will also see)
   - ❌ Cannot see any XYZ data

3. **Dr. Brown (XYZ)** logs in
   - ✅ Can see only XYZ data
   - ❌ Cannot see any ABC data (not even metadata)

---

## If You Want User-Level Isolation Instead

**Current setup:** Company-wide data sharing

**If you want:** User-only data (no sharing within company)

You would need to change the RLS policy to:

```sql
CREATE POLICY "Users can view own data only"
    ON pv_cases FOR SELECT
    USING (auth.uid() = user_id);  -- Only own data
```

This would make it so:
- User 1 (ABC) only sees their own 100 cases
- User 2 (ABC) only sees their own 50 cases
- They cannot see each other's data

**Current design assumes company-wide collaboration**, which is typical for pharma companies where multiple scientists work together.

---

## Summary

**Answer:** Data is maintained **PER COMPANY**, but each record tracks which user created it.

- ✅ **Company-level sharing** (all ABC users see all ABC data)
- ✅ **Company-level isolation** (ABC cannot see XYZ data)
- ✅ **User-level tracking** (know who uploaded each record)
- ✅ **Automatic security** (RLS enforces everything)

This is the standard multi-tenant SaaS model!

