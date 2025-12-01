"""
Dictionary Management Panel - SuperAdmin UI for managing reaction dictionary.
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Optional
import logging

from src.normalization.dictionary_manager import DictionaryManager
from src.normalization.reaction_dictionary import REACTION_DICTIONARY, get_all_pts
from src.social_ae.reaction_discovery import ReactionDiscoveryEngine
from src.normalization.reaction_normalizer import ReactionNormalizer

logger = logging.getLogger(__name__)


def render_dictionary_management_panel(
    df: Optional[pd.DataFrame] = None,
    supabase_client=None
):
    """
    Render dictionary management panel for SuperAdmin.
    
    Args:
        df: Optional DataFrame with reactions (for discovery)
        supabase_client: Optional Supabase client
    """
    st.header("📚 Reaction Dictionary Management")
    st.caption("Manage Preferred Terms (PTs), synonyms, patterns, and emoji mappings")
    
    # Initialize managers
    dict_manager = DictionaryManager(supabase_client)
    normalizer = ReactionNormalizer(use_llm=False)
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Overview",
        "🔍 Emerging Reactions",
        "➕ Add/Edit PT",
        "🔗 Merge PTs"
    ])
    
    with tab1:
        render_overview_tab(dict_manager)
    
    with tab2:
        render_emerging_tab(df, dict_manager, normalizer)
    
    with tab3:
        render_add_edit_tab(dict_manager)
    
    with tab4:
        render_merge_tab(dict_manager)


def render_overview_tab(dict_manager: DictionaryManager):
    """Render overview tab with dictionary statistics."""
    st.subheader("📊 Dictionary Overview")
    
    stats = dict_manager.get_dictionary_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total PTs", stats["total_pts"])
    
    with col2:
        st.metric("Total Synonyms", stats["total_synonyms"])
    
    with col3:
        st.metric("Total Patterns", stats["total_patterns"])
    
    with col4:
        st.metric("Total Emoji", stats["total_emoji"])
    
    st.markdown("---")
    
    # Category breakdown
    st.subheader("📂 By Category")
    category_df = pd.DataFrame([
        {"Category": cat, "Count": count}
        for cat, count in stats["categories"].items()
    ])
    
    if not category_df.empty:
        st.dataframe(category_df, use_container_width=True, hide_index=True)
    
    # Current dictionary table
    st.markdown("---")
    st.subheader("📋 Current Dictionary")
    
    pts = get_all_pts()
    if pts:
        dict_rows = []
        for pt in sorted(pts)[:100]:  # Show first 100
            info = REACTION_DICTIONARY.get(pt, {})
            dict_rows.append({
                "PT": pt,
                "Category": info.get("category", "Other"),
                "Synonyms": len(info.get("synonyms", [])),
                "Patterns": len(info.get("patterns", [])),
                "Emoji": len(info.get("emoji", []))
            })
        
        dict_df = pd.DataFrame(dict_rows)
        st.dataframe(dict_df, use_container_width=True, hide_index=True)
    else:
        st.info("No PTs in dictionary yet")


def render_emerging_tab(
    df: Optional[pd.DataFrame],
    dict_manager: DictionaryManager,
    normalizer: ReactionNormalizer
):
    """Render emerging reactions discovery tab."""
    st.subheader("🔍 Emerging Reactions (AI Discovered)")
    st.caption("Reactions that appear frequently but aren't in the dictionary")
    
    if df is None or df.empty:
        st.info("👆 Load reaction data first to discover emerging reactions")
        return
    
    # Discovery engine
    discovery_engine = ReactionDiscoveryEngine(normalizer)
    
    min_count = st.slider("Minimum Occurrence Count", 1, 50, 5)
    
    if st.button("🔍 Discover Emerging Reactions", type="primary"):
        with st.spinner("Analyzing reactions..."):
            emerging_df = discovery_engine.discover_emerging_reactions(
                df,
                min_count=min_count
            )
            
            if emerging_df.empty:
                st.success("✅ All reactions are in the dictionary!")
            else:
                st.success(f"🔍 Found {len(emerging_df)} emerging reactions")
                
                # Display with suggestions
                for idx, row in emerging_df.iterrows():
                    with st.expander(f"**{row['reaction_raw']}** (Count: {row['count']})"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Suggested PT:** {row['normalized_pt']}")
                            st.write(f"**Method:** {row['normalization_method']}")
                            st.write(f"**Confidence:** {row['confidence']:.2f}")
                        
                        with col2:
                            if st.button(f"➕ Add as New PT", key=f"add_{idx}"):
                                dict_manager.add_pt(
                                    pt=row['normalized_pt'],
                                    synonyms=[row['reaction_raw']],
                                    category="Other"
                                )
                                st.success(f"✅ Added {row['normalized_pt']} to dictionary")
                                st.rerun()
                            
                            if st.button(f"🔗 Merge with Existing", key=f"merge_{idx}"):
                                # Show merge options
                                existing_pts = get_all_pts()
                                selected_pt = st.selectbox(
                                    "Select PT to merge into",
                                    existing_pts,
                                    key=f"merge_select_{idx}"
                                )
                                if st.button("Confirm Merge", key=f"confirm_merge_{idx}"):
                                    dict_manager.merge_pt(row['normalized_pt'], selected_pt)
                                    st.success(f"✅ Merged into {selected_pt}")
                                    st.rerun()


def render_add_edit_tab(dict_manager: DictionaryManager):
    """Render add/edit PT tab."""
    st.subheader("➕ Add/Edit Preferred Term")
    
    pt = st.text_input("Preferred Term (PT)", placeholder="e.g., Nausea")
    
    col1, col2 = st.columns(2)
    
    with col1:
        synonyms_text = st.text_area(
            "Synonyms (one per line)",
            placeholder="nauseous\nfeeling sick\nqueasy",
            height=100
        )
        
        patterns_text = st.text_area(
            "Regex Patterns (one per line)",
            placeholder=r"\bnausea\b\n\bnauseous\b",
            height=100
        )
    
    with col2:
        emoji_text = st.text_input("Emoji", placeholder="🤢")
        
        category = st.selectbox(
            "Category",
            options=[
                "Gastrointestinal", "Neurological", "Cardiovascular",
                "Dermatological", "Musculoskeletal", "Respiratory",
                "Psychiatric", "General", "Endocrine", "Ocular", "Other"
            ]
        )
    
    if st.button("💾 Save PT", type="primary"):
        if not pt:
            st.error("Please enter a Preferred Term")
        else:
            synonyms = [s.strip() for s in synonyms_text.split("\n") if s.strip()]
            patterns = [p.strip() for p in patterns_text.split("\n") if p.strip()]
            emoji = [e.strip() for e in emoji_text.split() if e.strip()]
            
            success = dict_manager.add_pt(
                pt=pt,
                synonyms=synonyms,
                category=category,
                patterns=patterns,
                emoji=emoji
            )
            
            if success:
                st.success(f"✅ Added/Updated PT: {pt}")
                st.rerun()
            else:
                st.error("❌ Failed to save PT")


def render_merge_tab(dict_manager: DictionaryManager):
    """Render merge PTs tab."""
    st.subheader("🔗 Merge Preferred Terms")
    st.caption("Consolidate duplicate or similar PTs")
    
    pts = get_all_pts()
    
    if len(pts) < 2:
        st.info("Need at least 2 PTs to merge")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        source_pt = st.selectbox("Source PT (to merge from)", pts)
    
    with col2:
        target_pt = st.selectbox("Target PT (to merge into)", [p for p in pts if p != source_pt])
    
    if st.button("🔗 Merge PTs", type="primary"):
        if source_pt == target_pt:
            st.error("Source and target must be different")
        else:
            success = dict_manager.merge_pt(source_pt, target_pt)
            if success:
                st.success(f"✅ Merged {source_pt} into {target_pt}")
                st.rerun()
            else:
                st.error("❌ Failed to merge PTs")

