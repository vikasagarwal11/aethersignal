-- ============================================================================
-- Migration: Add super_admin role to existing database
-- EXECUTION ORDER: 02 (Run this AFTER 00_schema.sql if database already exists)
-- ============================================================================
-- This script updates the role constraint to include 'super_admin'
-- Run this ONCE in Supabase SQL Editor for existing databases

-- Drop existing constraint
ALTER TABLE user_profiles 
DROP CONSTRAINT IF EXISTS user_profiles_role_check;

-- Add new constraint with super_admin
ALTER TABLE user_profiles 
ADD CONSTRAINT user_profiles_role_check 
CHECK (role IN ('super_admin', 'admin', 'scientist', 'viewer'));

-- ============================================================================
-- Optional: Promote your account to super_admin
-- ============================================================================
-- Uncomment and replace YOUR_EMAIL_HERE with your actual email:
-- 
-- UPDATE user_profiles
-- SET role = 'super_admin'
-- WHERE email = 'YOUR_EMAIL_HERE';
--
-- Verify the update:
-- SELECT email, role FROM user_profiles WHERE role = 'super_admin';

-- ============================================================================
-- NOTES:
-- ============================================================================
-- 1. This is safe to run multiple times (uses IF EXISTS)
-- 2. Existing 'admin' users will continue to work (is_super_admin() checks both)
-- 3. After running, manually promote your account using the UPDATE statement above
-- 4. For new databases, use 00_schema.sql which already includes super_admin

