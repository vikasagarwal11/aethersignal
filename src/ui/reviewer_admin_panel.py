"""
Reviewer Admin Panel UI (PART 4)
Complete reviewer management interface with CRUD, browser storage, and Supabase sync.
"""
import streamlit as st
import pandas as pd
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid

try:
    from src.storage.reviewer_storage import ReviewerStorage
    from src.models.reviewer import Reviewer
    STORAGE_AVAILABLE = True
except ImportError:
    STORAGE_AVAILABLE = False

try:
    from src.ai.reviewer_expertise_engine import infer_signal_skills_required
    EXPERTISE_AVAILABLE = True
except ImportError:
    EXPERTISE_AVAILABLE = False


def render_reviewer_admin_panel() -> None:
    """
    Render complete Reviewer Administration Panel (PART 4).
    
    Features:
    - Add/Edit/Delete reviewers
    - Skill and TA management
    - Capacity configuration
    - Browser storage persistence
    - Supabase sync
    - CSV import/export
    - LLM skill suggestions
    """
    st.title("👥 Reviewer Administration Panel")
    st.caption("Manage reviewer profiles, skills, workloads, and storage sync. Supports unlimited reviewers with dynamic capacity and expertise matching.")
    
    if not STORAGE_AVAILABLE:
        st.error("Reviewer storage engine not available. Please install required dependencies.")
        return
    
    # Initialize storage
    storage = ReviewerStorage()
    
    # Tabs for different operations
    tab1, tab2, tab3, tab4 = st.tabs([
        "➕ Add/Edit Reviewers",
        "📋 Reviewer List",
        "💾 Storage & Sync",
        "🤖 AI Skill Suggestions"
    ])
    
    # ----------------------
    # TAB 1: Add/Edit Reviewers
    # ----------------------
    with tab1:
        st.markdown("### ➕ Add New Reviewer")
        
        with st.form("add_reviewer_form", clear_on_submit=False):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Reviewer Name *", placeholder="Dr. Jane Smith")
                email = st.text_input("Email", placeholder="jane.smith@company.com")
                title = st.text_input("Title", placeholder="Senior Safety Scientist")
            
            with col2:
                organization = st.text_input("Organization", placeholder="Optional")
                timezone = st.selectbox(
                    "Timezone",
                    options=["UTC", "America/New_York", "America/Chicago", "America/Los_Angeles", 
                             "Europe/London", "Europe/Paris", "Asia/Tokyo", "Asia/Shanghai"],
                    index=0
                )
            
            st.markdown("---")
            
            # Skills and Therapeutic Areas
            col3, col4 = st.columns(2)
            
            with col3:
                st.markdown("#### Skills")
                skills_input = st.text_area(
                    "Skills (comma-separated)",
                    placeholder="oncology, immunology, statistics, biologics",
                    help="Enter skills separated by commas"
                )
                skills = [s.strip() for s in skills_input.split(",") if s.strip()] if skills_input else []
            
            with col4:
                st.markdown("#### Therapeutic Areas")
                ta_input = st.text_area(
                    "Therapeutic Areas (comma-separated)",
                    placeholder="Oncology, Dermatology, Immunology",
                    help="Enter therapeutic areas separated by commas"
                )
                therapeutic_areas = [ta.strip() for ta in ta_input.split(",") if ta.strip()] if ta_input else []
            
            st.markdown("---")
            
            # Capacity Settings
            st.markdown("#### Capacity Settings")
            col5, col6, col7 = st.columns(3)
            
            with col5:
                max_cases_per_week = st.number_input(
                    "Max Cases Per Week",
                    min_value=1,
                    max_value=200,
                    value=25,
                    help="Maximum number of cases this reviewer can handle per week"
                )
            
            with col6:
                max_signals_per_week = st.number_input(
                    "Max Signals Per Week",
                    min_value=1,
                    max_value=50,
                    value=3,
                    help="Maximum number of signals this reviewer can handle per week"
                )
            
            with col7:
                avg_turnaround_days = st.number_input(
                    "Avg Turnaround (Days)",
                    min_value=1,
                    max_value=90,
                    value=5,
                    step=1
                )
            
            st.markdown("---")
            
            # Performance Metrics
            st.markdown("#### Performance Metrics")
            col8, col9 = st.columns(2)
            
            with col8:
                quality_score = st.slider(
                    "Quality Score (0.0 - 1.0)",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.90,
                    step=0.01,
                    help="Historical quality/accuracy score"
                )
            
            with col9:
                overdue_rate = st.slider(
                    "Overdue Rate (0.0 - 1.0)",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.05,
                    step=0.01,
                    help="Historical percentage of overdue reviews"
                )
            
            st.markdown("---")
            
            # Conflict of Interest
            st.markdown("#### Conflict of Interest")
            restricted_input = st.text_area(
                "Restricted Products (comma-separated)",
                placeholder="Product A, Product B",
                help="Products this reviewer cannot be assigned to due to COI"
            )
            restricted_products = [p.strip() for p in restricted_input.split(",") if p.strip()] if restricted_input else []
            
            # Notes
            notes = st.text_area("Notes", placeholder="Optional additional information")
            
            submitted = st.form_submit_button("💾 Save Reviewer", type="primary", use_container_width=True)
            
            if submitted:
                if not name:
                    st.error("❌ Reviewer Name is required.")
                else:
                    # Create reviewer
                    reviewer = Reviewer(
                        reviewer_id=str(uuid.uuid4()),
                        name=name,
                        email=email,
                        title=title,
                        organization=organization,
                        therapeutic_areas=therapeutic_areas,
                        skills=skills,
                        max_cases_per_week=max_cases_per_week,
                        max_signals_per_week=max_signals_per_week,
                        timezone=timezone,
                        avg_turnaround_days=float(avg_turnaround_days),
                        quality_score=quality_score,
                        overdue_rate=overdue_rate,
                        restricted_products=restricted_products,
                        notes=notes,
                        created_at=datetime.now().isoformat(),
                        updated_at=datetime.now().isoformat()
                    )
                    
                    if storage.add_reviewer(reviewer):
                        st.success(f"✅ Reviewer **{name}** added successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to add reviewer.")
        
        # Edit existing reviewers
        st.markdown("---")
        st.markdown("### ✏️ Edit Existing Reviewer")
        
        all_reviewers = storage.get_all_reviewers()
        if all_reviewers:
            reviewer_names = [r.name for r in all_reviewers]
            selected_name = st.selectbox("Select Reviewer to Edit", options=reviewer_names)
            
            if selected_name:
                reviewer = next((r for r in all_reviewers if r.name == selected_name), None)
                if reviewer:
                    st.info(f"Editing: **{reviewer.name}** (ID: {reviewer.reviewer_id[:8]}...)")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        new_capacity = st.number_input(
                            "Update Max Cases/Week",
                            min_value=1,
                            max_value=200,
                            value=reviewer.max_cases_per_week,
                            key="edit_capacity"
                        )
                    
                    with col2:
                        new_quality = st.slider(
                            "Update Quality Score",
                            min_value=0.0,
                            max_value=1.0,
                            value=reviewer.quality_score,
                            step=0.01,
                            key="edit_quality"
                        )
                    
                    if st.button("💾 Update Reviewer", key="update_reviewer"):
                        storage.update_reviewer(
                            reviewer.reviewer_id,
                            max_cases_per_week=new_capacity,
                            quality_score=new_quality
                        )
                        st.success(f"✅ Updated reviewer **{reviewer.name}**!")
                        st.rerun()
        else:
            st.info("No reviewers available to edit. Add reviewers first.")
    
    # ----------------------
    # TAB 2: Reviewer List + Search & Filters (PART 5)
    # ----------------------
    with tab2:
        st.markdown("### 📋 All Reviewers")
        
        all_reviewers = storage.get_all_reviewers()
        
        if not all_reviewers:
            st.info("No reviewers added yet. Use the 'Add/Edit Reviewers' tab to add reviewers.")
        else:
            st.metric("Total Reviewers", len(all_reviewers))
            
            # -------------------------------
            # PART 5: Search & Filter Section
            # -------------------------------
            st.markdown("---")
            st.markdown("#### 🔍 Search & Filter Reviewers")
            
            # Convert to dictionaries for easier filtering
            reviewers_dict = [reviewer.to_dict() for reviewer in all_reviewers]
            
            # 1. Quick Search Bar
            search_query = st.text_input(
                "🔍 Search reviewers (name, email, skills, TA, title)...",
                placeholder="Type to filter reviewers...",
                key="reviewer_search"
            )
            
            # 2. Filter Chips (Skills, TA, Performance)
            colA, colB, colC = st.columns(3)
            
            with colA:
                # Extract all unique skills
                all_skills = set()
                for r in reviewers_dict:
                    skills = r.get("skills", [])
                    if isinstance(skills, list):
                        all_skills.update(skills)
                    elif isinstance(skills, str):
                        all_skills.update([s.strip() for s in skills.split(",")])
                
                skill_filter = st.multiselect(
                    "Filter by Skills",
                    options=sorted(all_skills) if all_skills else [],
                    key="skill_filter"
                )
            
            with colB:
                # Extract all unique therapeutic areas
                all_tas = set()
                for r in reviewers_dict:
                    tas = r.get("therapeutic_areas", [])
                    if isinstance(tas, list):
                        all_tas.update(tas)
                    elif isinstance(tas, str):
                        all_tas.update([ta.strip() for ta in tas.split(",")])
                
                ta_filter = st.multiselect(
                    "Filter by Therapeutic Areas",
                    options=sorted(all_tas) if all_tas else [],
                    key="ta_filter"
                )
            
            with colC:
                performance_cutoff = st.slider(
                    "Quality Score ≥",
                    0.0, 1.0, 0.0,
                    step=0.05,
                    key="performance_filter"
                )
            
            # Apply filters
            filtered_reviewers = reviewers_dict.copy()
            
            # Apply search query
            if search_query:
                query_lower = search_query.lower()
                filtered_reviewers = [
                    r for r in filtered_reviewers
                    if (
                        query_lower in str(r.get("name", "")).lower() or
                        query_lower in str(r.get("email", "")).lower() or
                        query_lower in str(r.get("title", "")).lower() or
                        any(query_lower in str(s).lower() for s in r.get("skills", [])) or
                        any(query_lower in str(ta).lower() for ta in r.get("therapeutic_areas", []))
                    )
                ]
            
            # Apply skill filter
            if skill_filter:
                filtered_reviewers = [
                    r for r in filtered_reviewers
                    if any(s in (r.get("skills", []) if isinstance(r.get("skills"), list) else []) for s in skill_filter)
                ]
            
            # Apply TA filter
            if ta_filter:
                filtered_reviewers = [
                    r for r in filtered_reviewers
                    if any(ta in (r.get("therapeutic_areas", []) if isinstance(r.get("therapeutic_areas"), list) else []) for ta in ta_filter)
                ]
            
            # Apply performance threshold
            filtered_reviewers = [
                r for r in filtered_reviewers
                if r.get("quality_score", 0.0) >= performance_cutoff
            ]
            
            # Display filtered results
            st.write(f"**{len(filtered_reviewers)} reviewers match your criteria**")
            
            if not filtered_reviewers:
                st.info("No reviewers match the selected filters. Try adjusting your search criteria.")
            else:
                # Convert filtered reviewers back to Reviewer objects for display
                filtered_reviewer_objects = [
                    Reviewer.from_dict(r) for r in filtered_reviewers
                ]
                
                # Convert to DataFrame for display
                reviewers_data = []
                for reviewer in filtered_reviewer_objects:
                    reviewers_data.append({
                        "Name": reviewer.name,
                        "Title": reviewer.title or "N/A",
                        "Skills": ", ".join(reviewer.skills[:3]) + ("..." if len(reviewer.skills) > 3 else "") if reviewer.skills else "N/A",
                        "Therapeutic Areas": ", ".join(reviewer.therapeutic_areas[:2]) + ("..." if len(reviewer.therapeutic_areas) > 2 else "") if reviewer.therapeutic_areas else "N/A",
                        "Max Cases/Week": reviewer.max_cases_per_week,
                        "Quality Score": f"{reviewer.quality_score:.2f}",
                        "Current Queue": reviewer.current_queue,
                        "Email": reviewer.email or "N/A"
                    })
                
                df = pd.DataFrame(reviewers_data)
                
                # Add sorting capability
                st.markdown("---")
                sort_column = st.selectbox(
                    "Sort by",
                    options=["Name", "Quality Score", "Max Cases/Week", "Current Queue"],
                    key="sort_reviewers"
                )
                
                if sort_column == "Quality Score":
                    df["Quality Score Float"] = df["Quality Score"].astype(float)
                    df = df.sort_values("Quality Score Float", ascending=False)
                    df = df.drop(columns=["Quality Score Float"])
                elif sort_column == "Max Cases/Week":
                    df = df.sort_values("Max Cases/Week", ascending=False)
                elif sort_column == "Current Queue":
                    df = df.sort_values("Current Queue", ascending=False)
                else:
                    df = df.sort_values("Name", ascending=True)
                
                st.dataframe(df, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            
            # -------------------------------
            # PART 5: AI Reviewer Finder (Advanced)
            # -------------------------------
            st.markdown("#### 🤖 AI Reviewer Finder")
            st.info("Describe the reviewer you need, and AI will find the best matches based on skills, expertise, and availability.")
            
            if EXPERTISE_AVAILABLE:
                col1, col2 = st.columns(2)
                
                with col1:
                    drug_q = st.text_input("Drug (optional)", placeholder="Dupixent", key="ai_finder_drug")
                
                with col2:
                    reac_q = st.text_input("Reaction (optional)", placeholder="Conjunctivitis", key="ai_finder_reaction")
                
                custom_query = st.text_area(
                    "Describe the reviewer you need",
                    placeholder="e.g., Reviewer with oncology experience, labeling expertise, good performance, familiar with immunology",
                    key="ai_finder_query"
                )
                
                if st.button("🔍 Find Best Reviewers", type="primary", key="find_best_reviewers"):
                    with st.spinner("AI selecting best reviewers..."):
                        # Step 1: Infer required skills from drug+reaction
                        signal_dict = {
                            "drug": drug_q,
                            "reaction": reac_q
                        }
                        
                        inferred_skills = infer_signal_skills_required(signal_dict) if drug_q and reac_q else []
                        
                        # Step 2: Rank reviewers by expertise
                        from src.ai.reviewer_expertise_engine import rank_reviewers_by_expertise
                        
                        # Convert Reviewer objects back to dicts for ranking
                        reviewers_for_ranking = [r.to_dict() for r in all_reviewers]
                        
                        # Create signal dict for ranking
                        ranking_signal = {
                            "drug": drug_q,
                            "reaction": reac_q,
                            "skills_required": inferred_skills
                        }
                        
                        ranked_df = rank_reviewers_by_expertise(
                            signal=ranking_signal,
                            reviewers=reviewers_for_ranking
                        )
                        
                        if not ranked_df.empty:
                            st.success(f"✅ Found {len(ranked_df)} recommended reviewer(s):")
                            st.dataframe(ranked_df, use_container_width=True, hide_index=True)
                            
                            # Show top 3 recommendations with details
                            st.markdown("---")
                            st.markdown("#### 🏆 Top Recommendations")
                            
                            for idx, (_, row) in enumerate(ranked_df.head(3).iterrows(), 1):
                                reviewer_name = row.get("Reviewer", "Unknown")
                                reviewer = next((r for r in all_reviewers if r.name == reviewer_name), None)
                                
                                if reviewer:
                                    with st.expander(f"#{idx} - {reviewer_name} (Score: {row.get('Expertise Score', 0):.2f})"):
                                        col_a, col_b = st.columns(2)
                                        with col_a:
                                            st.write(f"**Skills:** {', '.join(reviewer.skills) if reviewer.skills else 'N/A'}")
                                            st.write(f"**Therapeutic Areas:** {', '.join(reviewer.therapeutic_areas) if reviewer.therapeutic_areas else 'N/A'}")
                                        with col_b:
                                            st.write(f"**Quality Score:** {reviewer.quality_score:.2f}")
                                            st.write(f"**Capacity:** {reviewer.max_cases_per_week} cases/week")
                                            st.write(f"**Current Queue:** {reviewer.current_queue}")
                        else:
                            st.info("No reviewers matched the criteria. Try adjusting your search parameters.")
            
            st.markdown("---")
            
            # Delete reviewer option
            st.markdown("---")
            st.markdown("### 🗑️ Delete Reviewer")
            delete_names = ["Select reviewer..."] + [r.name for r in all_reviewers]
            delete_selected = st.selectbox("Select Reviewer to Delete", options=delete_names)
            
            if delete_selected and delete_selected != "Select reviewer...":
                reviewer_to_delete = next((r for r in all_reviewers if r.name == delete_selected), None)
                if reviewer_to_delete:
                    if st.button("🗑️ Delete Reviewer", type="primary", key="delete_reviewer"):
                        if storage.delete_reviewer(reviewer_to_delete.reviewer_id):
                            st.success(f"✅ Deleted reviewer **{delete_selected}**")
                            st.rerun()
                        else:
                            st.error("❌ Failed to delete reviewer.")
    
    # ----------------------
    # TAB 3: Storage & Sync
    # ----------------------
    with tab3:
        st.markdown("### 💾 Storage & Sync")
        
        # Browser Storage
        st.markdown("#### 🌐 Browser Local Storage (IndexedDB)")
        st.info("Save reviewers to browser for offline access and persistence across sessions.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("⬆ Save to Browser Storage", use_container_width=True):
                if storage.save_to_browser_storage():
                    st.success("✅ Reviewers saved to browser storage!")
                else:
                    st.error("❌ Failed to save to browser storage.")
        
        with col2:
            if st.button("⬇ Load from Browser Storage", use_container_width=True):
                count = storage.load_from_browser_storage()
                if count > 0:
                    st.success(f"✅ Loaded {count} reviewer(s) from browser storage!")
                    st.rerun()
                else:
                    st.info("No reviewers found in browser storage or browser storage not available.")
        
        st.markdown("---")
        
        # Supabase Sync
        st.markdown("#### ☁️ Supabase Cloud Storage")
        st.info("Sync reviewers to Supabase for enterprise multi-user persistence and collaboration.")
        
        # Get organization ID from user profile if available
        organization_id = None
        try:
            # Try multiple ways to get organization ID
            if "user_profile" in st.session_state and st.session_state.user_profile:
                organization_id = st.session_state.user_profile.get("organization", "")
            elif "user_organization" in st.session_state:
                organization_id = st.session_state.user_organization
            else:
                # Try auth module
                try:
                    from src.auth.auth import get_current_user
                    user = get_current_user()
                    if user:
                        organization_id = user.get("organization", "")
                except Exception:
                    pass
        except Exception:
            pass
        
        org_input = st.text_input(
            "Organization ID",
            value=organization_id or "",
            help="Organization identifier for multi-tenant storage"
        )
        
        col3, col4 = st.columns(2)
        
        with col3:
            if st.button("⬆ Sync to Supabase", use_container_width=True):
                with st.spinner("Syncing reviewers to Supabase..."):
                    result = storage.sync_to_supabase(organization_id=org_input or None)
                    if result.get("status") == "ok":
                        st.success(f"✅ {result.get('message', 'Synced successfully')}")
                    else:
                        st.error(f"❌ {result.get('message', 'Sync failed')}")
        
        with col4:
            if st.button("⬇ Load from Supabase", use_container_width=True):
                with st.spinner("Loading reviewers from Supabase..."):
                    count = storage.pull_from_supabase(organization_id=org_input or None)
                    if count > 0:
                        st.success(f"✅ Loaded {count} reviewer(s) from Supabase!")
                        st.rerun()
                    else:
                        st.info("No reviewers found in Supabase or Supabase not available.")
        
        # Sync all sources
        st.markdown("---")
        if st.button("🔄 Sync All Sources (Merge Session + Browser + Supabase)", use_container_width=True):
            with st.spinner("Syncing all sources..."):
                result = storage.sync_all_sources(organization_id=org_input or None)
                if result.get("status") == "ok":
                    st.success(f"✅ {result.get('message', 'Sync completed')}")
                    st.rerun()
                else:
                    st.error(f"❌ Sync failed: {result.get('message', 'Unknown error')}")
        
        st.markdown("---")
        
        # CSV Import/Export
        st.markdown("#### 📊 CSV Import/Export")
        
        col5, col6 = st.columns(2)
        
        with col5:
            csv_data = storage.export_to_csv()
            if csv_data:
                st.download_button(
                    "📥 Download Reviewers as CSV",
                    csv_data,
                    file_name=f"reviewers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        with col6:
            uploaded_file = st.file_uploader("Upload CSV File", type=["csv"], key="csv_upload")
            if uploaded_file:
                csv_str = uploaded_file.read().decode("utf-8")
                count = storage.import_from_csv(csv_str)
                if count > 0:
                    st.success(f"✅ Imported {count} reviewer(s) from CSV!")
                    st.rerun()
                else:
                    st.error("❌ Failed to import reviewers from CSV.")
        
        # JSON Export
        st.markdown("---")
        st.markdown("#### 📄 JSON Export")
        json_data = storage.export_to_json()
        if json_data:
            st.download_button(
                "📥 Download Reviewers as JSON",
                json_data,
                file_name=f"reviewers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
    
    # ----------------------
    # TAB 4: AI Skill Suggestions
    # ----------------------
    with tab4:
        st.markdown("### 🤖 AI Skill Suggestions")
        st.info("Get AI-powered skill recommendations for reviewer assignment based on drug and reaction.")
        
        if EXPERTISE_AVAILABLE:
            col1, col2 = st.columns(2)
            
            with col1:
                drug_name = st.text_input("Drug Name", placeholder="Dupixent")
            
            with col2:
                reaction_name = st.text_input("Reaction/Event", placeholder="Conjunctivitis")
            
            if st.button("🔍 Suggest Required Skills", type="primary"):
                if drug_name and reaction_name:
                    # Create a mock signal dict for skill inference
                    signal_dict = {
                        "drug": drug_name,
                        "reaction": reaction_name
                    }
                    
                    suggested_skills = infer_signal_skills_required(signal_dict)
                    
                    if suggested_skills:
                        st.success("✅ **Suggested Skills for Reviewer Assignment:**")
                        for skill in suggested_skills:
                            st.markdown(f"- {skill}")
                        
                        # Show matching reviewers
                        st.markdown("---")
                        st.markdown("#### 👥 Matching Reviewers")
                        
                        matching_reviewers = storage.registry.find_by_skill(suggested_skills[0] if suggested_skills else "")
                        
                        if matching_reviewers:
                            match_data = []
                            for reviewer in matching_reviewers:
                                match_data.append({
                                    "Name": reviewer.name,
                                    "Skills": ", ".join(reviewer.skills),
                                    "Max Cases/Week": reviewer.max_cases_per_week,
                                    "Quality Score": f"{reviewer.quality_score:.2f}"
                                })
                            st.dataframe(pd.DataFrame(match_data), use_container_width=True, hide_index=True)
                        else:
                            st.info("No reviewers found with matching skills. Consider adding reviewers with these skills.")
                    else:
                        st.info("Could not infer skills. Please check drug and reaction names.")
                else:
                    st.warning("⚠️ Please provide both drug name and reaction to get skill suggestions.")
        else:
            st.info("AI skill suggestion engine not available. Install required dependencies.")

