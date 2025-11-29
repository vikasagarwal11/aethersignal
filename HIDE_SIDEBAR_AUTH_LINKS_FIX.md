# Hide Login/Register Links from Sidebar When Authenticated

## Issue
When logged in, Streamlit's automatic page navigation still shows "Login", "Profile", and "Register" links in the sidebar.

## Root Cause
Streamlit automatically creates navigation links for all pages in the `pages/` directory. These are separate from our custom authentication buttons and show up regardless of auth status.

## Solution
Added CSS and JavaScript to dynamically hide Login and Register page navigation links when the user is authenticated.

## Implementation

### CSS Rules Added (`src/styles.py`)
- Multiple CSS selectors to target Login/Register links
- Class-based hiding with `.sidebar-auth-authenticated`
- Direct href-based targeting

### JavaScript Added (`src/styles.py`)
- Detects authentication status by checking for:
  - "Signed in as" text in sidebar
  - Email address pattern
  - Profile button presence
- Hides Login/Register links when authenticated
- Uses MutationObserver to watch for sidebar changes
- Runs multiple times to catch different load states

## How It Works

1. **Detection**: JavaScript checks if user is authenticated
2. **Hiding**: Adds CSS class and directly hides matching links
3. **Monitoring**: MutationObserver watches for sidebar changes
4. **Periodic Check**: Also runs every 2 seconds as backup

## Expected Behavior

### When Authenticated:
- ✅ "Signed in as [email]" visible in sidebar
- ✅ Profile button visible in sidebar  
- ❌ Login link hidden
- ❌ Register link hidden
- ✅ Profile link may still show (but auto-redirects if needed)

### When NOT Authenticated:
- ✅ Login link visible
- ✅ Register link visible
- ❌ "Signed in as" not visible

## Files Modified
- `src/styles.py` - Added CSS and JavaScript to hide auth pages

## Testing
After restarting the app:
1. Login to your account
2. Check sidebar - Login/Register links should be hidden
3. Logout - Login/Register links should reappear

