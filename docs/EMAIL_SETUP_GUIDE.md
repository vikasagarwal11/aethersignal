# Email Service Setup Guide for AetherSignal

## Overview

AetherSignal uses Supabase's built-in email service for user authentication (registration, password reset, email verification). You can use Supabase's free email service for development, or configure custom SMTP for production.

---

## Option 1: Use Supabase Built-in Email (Free - Development)

**Status:** Already enabled by default in your Supabase project

### What's Included:
- ✅ Email verification (confirm signup)
- ✅ Password reset emails
- ✅ Magic link authentication
- ✅ Email change verification

### Limitations:
- Rate limits (not suitable for high-volume production)
- Uses Supabase's email service
- Limited customization

### Setup:
1. Go to: https://supabase.com/dashboard/project/scrksfxnkxmvvdzwmqnc/auth/templates
2. Email provider is already enabled (default)
3. You can customize email templates if needed:
   - Click on any template (e.g., "Confirm sign up")
   - Edit the email subject and body
   - Save changes

**✅ This is already working for you!** No additional setup needed for development/testing.

---

## Option 2: Custom SMTP (Recommended for Production)

For production use, configure your own SMTP server for better reliability and higher rate limits.

### Supported SMTP Providers:
- Gmail (with App Password)
- SendGrid
- Mailgun
- Amazon SES
- Microsoft 365
- Any SMTP server

### Setup Steps:

1. **Get SMTP Credentials:**
   - Choose your email provider
   - Get SMTP server, port, username, password
   - Example for Gmail:
     - Server: `smtp.gmail.com`
     - Port: `587` (TLS) or `465` (SSL)
     - Username: Your Gmail address
     - Password: App Password (not your regular password)

2. **Configure in Supabase:**
   - Go to: https://supabase.com/dashboard/project/scrksfxnkxmvvdzwmqnc/auth/templates
   - Click **"SMTP Settings"** tab
   - Click **"Set up SMTP"** button
   - Fill in:
     - **Sender email:** Your email address
     - **Sender name:** "AetherSignal" (or your company name)
     - **Host:** SMTP server (e.g., `smtp.gmail.com`)
     - **Port:** SMTP port (e.g., `587`)
     - **Username:** SMTP username
     - **Password:** SMTP password
     - **Secure:** Enable TLS/SSL (usually required)
   - Click **"Save"**

3. **Test Email:**
   - After saving, Supabase will send a test email
   - Check your inbox to verify it works

### Gmail Setup Example:

1. **Enable 2-Factor Authentication** on your Google account
2. **Create App Password:**
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Enter "AetherSignal"
   - Copy the 16-character password
3. **Configure in Supabase:**
   - Host: `smtp.gmail.com`
   - Port: `587`
   - Username: Your Gmail address
   - Password: The 16-character app password
   - Secure: Enable TLS

---

## Email Templates Configuration

You can customize email templates in Supabase:

1. Go to: https://supabase.com/dashboard/project/scrksfxnkxmvvdzwmqnc/auth/templates
2. Click on any template to edit:
   - **Confirm sign up** - Sent when user registers
   - **Reset password** - Sent when user requests password reset
   - **Magic link** - Sent for passwordless login
   - **Change email address** - Sent when user changes email
   - **Invite user** - Sent when admin invites a user

3. **Customize:**
   - Subject line
   - Email body (HTML supported)
   - Use variables like `{{ .ConfirmationURL }}`, `{{ .Email }}`, etc.

---

## Current Status

Based on your Supabase dashboard:
- ✅ Email provider is enabled
- ✅ Email templates are configured
- ⚠️ Using built-in email service (has rate limits)
- 💡 For production: Set up custom SMTP

---

## Testing Email Functionality

1. **Test Registration:**
   - Register a new user in AetherSignal
   - Check email inbox for verification email
   - Click verification link

2. **Test Password Reset:**
   - Click "Forgot Password" on login page
   - Enter email address
   - Check inbox for reset link

3. **Check Supabase Logs:**
   - Go to: https://supabase.com/dashboard/project/scrksfxnkxmvvdzwmqnc/logs/explorer
   - Filter by "auth" to see email sending logs

---

## Troubleshooting

### Emails Not Sending:

1. **Check Supabase Logs:**
   - Dashboard → Logs → API Logs
   - Look for email-related errors

2. **Verify Email Provider:**
   - Check if email provider is enabled
   - Go to: Authentication → Providers → Email

3. **Check SMTP Settings:**
   - Verify SMTP credentials are correct
   - Test connection in Supabase dashboard

4. **Check Spam Folder:**
   - Emails might be going to spam
   - Add Supabase email to whitelist

### Rate Limits:

If you hit rate limits with built-in email:
- Set up custom SMTP (Option 2 above)
- Or upgrade Supabase plan for higher limits

---

## Summary

**For Development/Testing:**
- ✅ Use built-in email (already enabled)
- ✅ No additional setup needed
- ⚠️ Be aware of rate limits

**For Production:**
- 💡 Set up custom SMTP
- 💡 Configure email templates
- 💡 Test email delivery
- 💡 Monitor email logs

**Current Setup:**
- Email provider: ✅ Enabled
- SMTP: ⚠️ Not configured (using built-in)
- Templates: ✅ Default templates active

You're ready to test user registration and password reset! 🎉

