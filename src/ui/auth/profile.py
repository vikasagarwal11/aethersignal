"""
User profile page UI component for AetherSignal.
"""

import streamlit as st
from src.auth.auth import get_current_user, logout_user, is_authenticated
from src.auth.user_management import update_user_profile, get_user_profile


def render_profile_page() -> None:
    """Render user profile page."""
    
    if not is_authenticated():
        st.warning("⚠️ Please login to view your profile.")
        st.session_state.show_login = True
        return
    
    user = get_current_user()
    if not user:
        st.error("Failed to load user information.")
        return
    
    st.markdown("## 👤 User Profile")
    
    # Display current user info
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"**Email:** {user.get('email', 'N/A')}")
        st.markdown(f"**Full Name:** {user.get('full_name', 'Not set')}")
        st.markdown(f"**Organization:** {user.get('organization', 'Not set')}")
        st.markdown(f"**Role:** {user.get('role', 'scientist').title()}")
        st.markdown(f"**Subscription:** {user.get('subscription_tier', 'free').title()}")
    
    with col2:
        if st.button("🚪 Logout", use_container_width=True, type="secondary"):
            result = logout_user()
            if result.get("success"):
                st.success("Logged out successfully!")
                st.rerun()
    
    st.markdown("---")
    
    # Edit profile form
    with st.expander("✏️ Edit Profile", expanded=False):
        with st.form("edit_profile_form"):
            new_full_name = st.text_input(
                "Full Name",
                value=user.get('full_name', ''),
                key="edit_full_name"
            )
            
            new_organization = st.text_input(
                "Organization",
                value=user.get('organization', ''),
                key="edit_organization",
                help="Changing organization will move your data to the new company"
            )
            
            if st.form_submit_button("Save Changes", use_container_width=True):
                update_data = {}
                if new_full_name != user.get('full_name'):
                    update_data['full_name'] = new_full_name
                if new_organization != user.get('organization'):
                    update_data['organization'] = new_organization
                
                if update_data:
                    result = update_user_profile(user['user_id'], update_data)
                    if result.get("success"):
                        st.success("Profile updated successfully!")
                        st.rerun()
                    else:
                        st.error(result.get("error", "Failed to update profile."))
                else:
                    st.info("No changes to save.")
    
    # Change password form
    with st.expander("🔑 Change Password", expanded=False):
        with st.form("change_password_form"):
            current_password = st.text_input(
                "Current Password",
                type="password",
                key="change_password_current"
            )
            
            new_password = st.text_input(
                "New Password",
                type="password",
                key="change_password_new",
                help="Minimum 8 characters"
            )
            
            confirm_password = st.text_input(
                "Confirm New Password",
                type="password",
                key="change_password_confirm"
            )
            
            if st.form_submit_button("Change Password", use_container_width=True):
                if not current_password or not new_password or not confirm_password:
                    st.warning("Please fill in all password fields.")
                elif len(new_password) < 8:
                    st.warning("New password must be at least 8 characters long.")
                elif new_password != confirm_password:
                    st.warning("New passwords do not match.")
                else:
                    # Password change would be handled by Supabase Auth
                    st.info("Password change functionality will be implemented with Supabase Auth API.")
    
    # Usage statistics (placeholder)
    st.markdown("---")
    st.markdown("### 📊 Usage Statistics")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Data Sets", "0", help="Number of data sets you've uploaded")
    with col2:
        st.metric("Queries Run", "0", help="Number of queries you've executed")
    with col3:
        st.metric("Signals Detected", "0", help="Number of signals you've detected")

