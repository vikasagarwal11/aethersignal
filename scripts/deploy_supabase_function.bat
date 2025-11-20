@echo off
REM Deploy Supabase Edge Function (Windows)
echo Deploying Supabase Edge Function...

REM Check if Supabase CLI is installed
where supabase >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Supabase CLI not found. Install with: npm install -g supabase
    exit /b 1
)

echo Checking Supabase login...
supabase login

echo Linking to project...
supabase link --project-ref scrksfxnkxmvvdzwmqnc

echo Deploying social_ae_pull function...
supabase functions deploy social_ae_pull

echo.
echo Setting environment variables...
set /p API_ENDPOINT="Enter your API endpoint URL (e.g., https://your-app.onrender.com/social/daily): "
set /p API_SECRET="Enter API secret key: "

supabase secrets set SOCIAL_AE_API_ENDPOINT=%API_ENDPOINT%
supabase secrets set API_SECRET_KEY=%API_SECRET%

echo.
echo Edge Function deployed!
echo.
echo Next steps:
echo 1. Go to Supabase Dashboard - Database - Cron Jobs
echo 2. Create cron job: daily_social_ae_pull
echo 3. Schedule: 0 1 * * * (1 AM UTC daily)
echo 4. Function: social_ae_pull
echo 5. Enable the cron job

