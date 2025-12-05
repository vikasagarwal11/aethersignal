"""
Upload section component for AetherSignal.
Handles file upload, loading, and schema display.
"""

import pandas as pd
import streamlit as st

from src import analytics
from src import faers_loader
from src import pv_schema
from src import signal_stats
from src import mapping_templates
from src.app_helpers import cached_detect_and_normalize, load_all_files
from src.app_processing_mode import (
    ProcessingMode,
    recommend_mode_based_on_file_size,
    set_processing_mode,
    browser_supports_local_processing,
    get_processing_mode,
    get_processing_mode_reason
)
from src.ui.schema_mapper import render_schema_mapper


def render_upload_section():
    """Render file upload UI and handle loading."""
    # Initialize in-session schema templates from disk (persistent across runs if filesystem allows)
    if "schema_templates" not in st.session_state:
        st.session_state.schema_templates = mapping_templates.load_templates()
    
    # DATASET SELECTOR: Show available datasets from database and let user choose which to load
    data_loaded = st.session_state.data is not None and st.session_state.normalized_data is not None
    
    # Show the database loader section if authenticated (even if data is already loaded - allows combining)
    if True:  # Always show if authenticated
        try:
            from src.auth.auth import is_authenticated, get_current_user
            from src.pv_storage import load_pv_data, list_available_datasets
            
            if is_authenticated():
                user = get_current_user()
                if user:
                    user_id = user.get('user_id')
                    organization = user.get('organization', '')
                    
                    # List available datasets
                    available_datasets = list_available_datasets(user_id, organization)
                    
                    # Show the expander even if no datasets (so user knows the feature exists)
                    if available_datasets:
                        # Show dataset selector
                        expander_title = "💾 Load Data from Database" if not data_loaded else "💾 Load Additional Data from Database (Combine)"
                        expanded_state = not data_loaded  # Only expand if no data loaded yet
                        
                        with st.expander(expander_title, expanded=expanded_state):
                            if data_loaded:
                                st.info("ℹ️ **Data already loaded.** Select datasets below to combine with existing data, or upload new files to merge.")
                                st.markdown(f"**Currently loaded:** {len(st.session_state.normalized_data):,} cases")
                            else:
                                st.markdown("**You have data saved in the database. Choose which dataset to load:**")
                            
                            # Group datasets by date for display
                            # Use a list to preserve order and handle potential duplicates
                            dataset_options_list = []
                            seen_keys = set()
                            
                            for ds in available_datasets:
                                # Create a unique key to prevent duplicates
                                unique_key = (ds['upload_date'], ds['source'])
                                if unique_key not in seen_keys:
                                    seen_keys.add(unique_key)
                                    # Create a more descriptive label with time info if available
                                    time_info = ""
                                    if ds.get('first_record') and ds.get('last_record'):
                                        try:
                                            from datetime import datetime
                                            # Handle different datetime formats
                                            first_str = str(ds['first_record'])
                                            last_str = str(ds['last_record'])
                                            
                                            # Try parsing with different formats
                                            first = None
                                            last = None
                                            
                                            # Try ISO format first
                                            try:
                                                first = datetime.fromisoformat(first_str.replace('Z', '+00:00'))
                                                last = datetime.fromisoformat(last_str.replace('Z', '+00:00'))
                                            except (ValueError, AttributeError):
                                                # Fallback to other common formats
                                                try:
                                                    from dateutil import parser
                                                    first = parser.parse(first_str)
                                                    last = parser.parse(last_str)
                                                except:
                                                    pass
                                            
                                            if first and last:
                                                if first.date() == last.date():
                                                    time_info = f" @ {first.strftime('%H:%M')}"
                                                else:
                                                    time_info = f" ({first.strftime('%H:%M')} - {last.strftime('%H:%M')})"
                                        except Exception:
                                            # Silently ignore datetime parsing errors
                                            pass
                                    
                                    label = f"{ds['date_label']}{time_info} - {ds['source']} ({ds['case_count']:,} cases)"
                                    dataset_options_list.append((label, ds))
                            
                            # Add "Load All" option at the top
                            all_data_label = "🔄 Load All Data (All uploads combined)"
                            dataset_options_list.insert(0, (all_data_label, None))
                            
                            # Extract labels and create mapping
                            dataset_labels = [opt[0] for opt in dataset_options_list]
                            dataset_options = {opt[0]: opt[1] for opt in dataset_options_list}
                            
                            # Allow multi-select for datasets (excluding "Load All" option)
                            dataset_labels_for_multiselect = [opt[0] for opt in dataset_options_list if opt[1] is not None]
                            
                            # Selection mode toggle
                            selection_mode = st.radio(
                                "Selection mode:",
                                ["Single dataset", "Multiple datasets"],
                                horizontal=True,
                                key="dataset_selection_mode"
                            )
                            
                            if selection_mode == "Single dataset":
                                selected_option = st.selectbox(
                                    "Select dataset to load:",
                                    options=dataset_labels,
                                    index=0,
                                    key="dataset_selector_single"
                                )
                                selected_datasets = [selected_option] if selected_option != all_data_label else []
                            else:
                                selected_options = st.multiselect(
                                    "Select datasets to combine (hold Ctrl/Cmd to select multiple):",
                                    options=dataset_labels_for_multiselect,
                                    default=[],
                                    key="dataset_selector_multi"
                                )
                                selected_datasets = selected_options
                                selected_option = None  # Not used in multi-select mode
                            
                            # Add combine option if data is already loaded
                            combine_mode = False
                            if data_loaded:
                                combine_mode = st.checkbox(
                                    "🔗 Combine with existing data (don't replace)",
                                    value=False,
                                    key="combine_with_existing"
                                )
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if combine_mode:
                                    button_label = f"✅ Add Selected Dataset to Existing" if selection_mode == "Single dataset" else f"✅ Add {len(selected_datasets)} Datasets to Existing"
                                else:
                                    button_label = "✅ Load Selected Dataset" if selection_mode == "Single dataset" else f"✅ Load {len(selected_datasets)} Selected Datasets"
                                    
                                if st.button(button_label, use_container_width=True, key="load_dataset", disabled=(selection_mode == "Multiple datasets" and len(selected_datasets) == 0)):
                                    if selection_mode == "Single dataset":
                                        # Single dataset loading (existing logic)
                                        if selected_option == all_data_label or selected_option.startswith("🔄 Load All"):
                                            # Load all data
                                            with st.spinner("Loading all data from database..."):
                                                df_from_db = load_pv_data(user_id, organization)
                                        else:
                                            # Load specific dataset
                                            selected_ds = dataset_options.get(selected_option)
                                            if selected_ds is None:
                                                st.error("Invalid dataset selection. Please refresh and try again.")
                                                st.stop()
                                            
                                            from datetime import datetime, timedelta
                                            
                                            # Create date range for this dataset
                                            upload_date = selected_ds['upload_date']
                                            date_from = datetime.combine(upload_date, datetime.min.time())
                                            date_to = datetime.combine(upload_date, datetime.max.time())
                                            
                                            with st.spinner(f"Loading dataset from {selected_ds['date_label']}..."):
                                                df_from_db = load_pv_data(
                                                    user_id, 
                                                    organization,
                                                    date_from=date_from,
                                                    date_to=date_to,
                                                    source=selected_ds['source']
                                                )
                                        
                                        if df_from_db is not None and not df_from_db.empty:
                                            if combine_mode and data_loaded:
                                                # Combine with existing data
                                                import pandas as pd
                                                existing_df = st.session_state.normalized_data
                                                combined_df = pd.concat([existing_df, df_from_db], ignore_index=True)
                                                
                                                # Remove duplicates based on case_id if available
                                                if 'case_id' in combined_df.columns:
                                                    before_dedup = len(combined_df)
                                                    combined_df = combined_df.drop_duplicates(subset=['case_id'], keep='first')
                                                    duplicates_removed = before_dedup - len(combined_df)
                                                    if duplicates_removed > 0:
                                                        st.info(f"ℹ️ Removed {duplicates_removed:,} duplicate cases when combining.")
                                                
                                                st.session_state.normalized_data = combined_df
                                                st.session_state.data = combined_df
                                                st.session_state.data_reloaded_from_db = True
                                                st.success(f"✅ Combined: {len(existing_df):,} existing + {len(df_from_db):,} new = {len(combined_df):,} total cases")
                                            else:
                                                # Replace existing data
                                                st.session_state.normalized_data = df_from_db
                                                st.session_state.data = df_from_db
                                                st.session_state.data_reloaded_from_db = True
                                                st.session_state.data_loaded_successfully = True
                                                st.success(f"✅ Loaded {len(df_from_db):,} cases")
                                            st.rerun()
                                    else:
                                        # Multi-dataset loading
                                        if len(selected_datasets) == 0:
                                            st.warning("Please select at least one dataset to load.")
                                            st.stop()
                                        
                                        from datetime import datetime
                                        import pandas as pd
                                        
                                        all_dfs = []
                                        total_cases = 0
                                        
                                        with st.spinner(f"Loading {len(selected_datasets)} dataset(s)..."):
                                            progress_bar = st.progress(0)
                                            for i, selected_label in enumerate(selected_datasets):
                                                selected_ds = dataset_options.get(selected_label)
                                                if selected_ds is None:
                                                    continue
                                                
                                                # Create date range for this dataset
                                                upload_date = selected_ds['upload_date']
                                                date_from = datetime.combine(upload_date, datetime.min.time())
                                                date_to = datetime.combine(upload_date, datetime.max.time())
                                                
                                                # Load this dataset
                                                df = load_pv_data(
                                                    user_id, 
                                                    organization,
                                                    date_from=date_from,
                                                    date_to=date_to,
                                                    source=selected_ds['source']
                                                )
                                                
                                                if df is not None and not df.empty:
                                                    all_dfs.append(df)
                                                    total_cases += len(df)
                                                
                                                progress_bar.progress((i + 1) / len(selected_datasets))
                                        
                                        if all_dfs:
                                            # Combine all datasets
                                            df_from_db = pd.concat(all_dfs, ignore_index=True)
                                            
                                            # Remove duplicates based on case_id if available
                                            if 'case_id' in df_from_db.columns:
                                                before_dedup = len(df_from_db)
                                                df_from_db = df_from_db.drop_duplicates(subset=['case_id'], keep='first')
                                                duplicates_removed = before_dedup - len(df_from_db)
                                                if duplicates_removed > 0:
                                                    st.info(f"ℹ️ Removed {duplicates_removed:,} duplicate cases when combining datasets.")
                                            
                                            if combine_mode and data_loaded:
                                                # Combine with existing data
                                                existing_df = st.session_state.normalized_data
                                                combined_df = pd.concat([existing_df, df_from_db], ignore_index=True)
                                                
                                                # Remove duplicates again
                                                if 'case_id' in combined_df.columns:
                                                    before_dedup = len(combined_df)
                                                    combined_df = combined_df.drop_duplicates(subset=['case_id'], keep='first')
                                                    duplicates_removed = before_dedup - len(combined_df)
                                                    if duplicates_removed > 0:
                                                        st.info(f"ℹ️ Removed {duplicates_removed:,} duplicate cases when combining with existing data.")
                                                
                                                st.session_state.normalized_data = combined_df
                                                st.session_state.data = combined_df
                                                st.session_state.data_reloaded_from_db = True
                                                st.success(f"✅ Combined: {len(existing_df):,} existing + {len(df_from_db):,} new = {len(combined_df):,} total cases")
                                            else:
                                                # Replace existing data
                                                st.session_state.normalized_data = df_from_db
                                                st.session_state.data = df_from_db
                                                st.session_state.data_reloaded_from_db = True
                                                st.session_state.data_loaded_successfully = True
                                                st.success(f"✅ Loaded and combined {len(selected_datasets)} dataset(s): {len(df_from_db):,} total cases")
                                            st.rerun()
                                        else:
                                            st.error("Failed to load any datasets. Please try again.")
                                    
                            with col2:
                                if st.button("🔄 Refresh Dataset List", use_container_width=True, key="refresh_datasets"):
                                    st.rerun()
                            
                            # Show dataset summary
                            st.markdown("---")
                            st.markdown("**Available Datasets:**")
                            
                            # Remove duplicates from display (same logic as dropdown)
                            seen_display = set()
                            unique_datasets = []
                            for ds in available_datasets:
                                unique_key = (ds['upload_date'], ds['source'])
                                if unique_key not in seen_display:
                                    seen_display.add(unique_key)
                                    unique_datasets.append(ds)
                            
                            for ds in unique_datasets[:5]:  # Show first 5
                                st.caption(f"📅 **{ds['date_label']}** - {ds['source']}: {ds['case_count']:,} cases")
                            if len(unique_datasets) > 5:
                                st.caption(f"... and {len(unique_datasets) - 5} more")
                            
                            # Show total count if multiple datasets
                            if len(unique_datasets) > 1:
                                total_cases = sum(ds['case_count'] for ds in unique_datasets)
                                st.info(f"📊 **Total across all datasets:** {total_cases:,} cases")
                    else:
                        # No datasets found - show empty state
                        with st.expander("💾 Load Data from Database", expanded=False):
                            st.info("📭 No datasets found in database. Upload data first to save it for future sessions.")
                else:
                    # User object is None - authentication issue
                    with st.expander("💾 Load Data from Database", expanded=False):
                        st.warning("⚠️ Unable to retrieve user profile. Please try logging in again.")
            else:
                # Not authenticated - this is normal, user can still upload files
                pass
        except Exception as e:
            # Show error for debugging, but don't break the upload functionality
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error loading datasets from database: {e}", exc_info=True)
            # Optionally show a non-intrusive error message
            # st.error(f"⚠️ Could not load datasets from database: {str(e)[:100]}")
            pass

    st.markdown(
        """
        <div class="session-chip-row" style="margin-bottom: 16px !important;">
            <div class="session-chip">🗂 Session-based, no login</div>
            <div class="session-chip">📄 Works with FAERS / CSV / Excel / PDF exports</div>
            <div class="session-chip">⚛️ Quantum-inspired ranking (demo)</div>
        </div>
        <div class='block-card' style="margin-top: 0 !important;">
        """,
        unsafe_allow_html=True,
    )

    uploaded_files = st.file_uploader(
        "Drop any safety data format: FAERS, E2B XML, Argus, Veeva, CSV, Excel, text, ZIP or PDF",
        type=["csv", "xlsx", "xls", "txt", "zip", "pdf", "xml"],
        accept_multiple_files=True,
        help=(
            "**Flexible format support for multi-vendor data:**\n\n"
            "✅ **Accepted formats:**\n"
            "- FAERS ASCII files (DEMO/DRUG/REAC/OUTC/THER/INDI/RPSR)\n"
            "- **E2B(R3) XML files** (Argus exports, EudraVigilance, VigiBase)\n"
            "- Argus/Veeva exports (CSV/Excel)\n"
            "- Custom CSV/Excel files (any column names)\n"
            "- PDF files with tables\n"
            "- ZIP archives containing multiple files\n\n"
            "**Column mapping:** Auto-detected, with manual override available if needed.\n"
            "No standard format required - we adapt to your data structure.\n\n"
            "📦 Large files (>200MB) are supported."
        ),
    )
    
    # --------------------------
    # Processing Mode Selection (CHUNK 7.1)
    # --------------------------
    if uploaded_files:
        # Calculate total file size
        total_size_bytes = sum(f.size for f in uploaded_files)
        total_size_mb = total_size_bytes / (1024 * 1024)
        
        # Get recommended mode based on file size
        recommended_mode, reason = recommend_mode_based_on_file_size(total_size_mb)
        
        # Check browser capability
        if not browser_supports_local_processing() and recommended_mode != ProcessingMode.SERVER:
            recommended_mode = ProcessingMode.SERVER
            reason = "Local processing not supported in this browser. Using server mode."
        
        # Set recommended mode if not already set or if user hasn't overridden
        if not st.session_state.get("processing_mode_override", False):
            set_processing_mode(recommended_mode, reason)
        
        # Display recommended mode info
        mode_icon = "🖥️" if recommended_mode == ProcessingMode.SERVER else "💻" if recommended_mode == ProcessingMode.LOCAL else "🔄"
        st.info(f"{mode_icon} **Recommended Processing Mode: {recommended_mode.upper()}**\n\n_{reason}_")
        
        # Manual override toggle
        with st.expander("⚙️ Advanced: Choose Processing Mode", expanded=False):
            current_mode = get_processing_mode()
            mode_index = ["server", "local", "hybrid"].index(current_mode) if current_mode in ["server", "local", "hybrid"] else 0
            
            chosen = st.radio(
                "Choose processing mode:",
                (
                    ProcessingMode.SERVER,
                    ProcessingMode.LOCAL,
                    ProcessingMode.HYBRID
                ),
                index=mode_index,
                help="Server = safest. Local = fastest for large files. Hybrid = best for medium files."
            )
            
            if chosen != current_mode:
                set_processing_mode(chosen, "User override")
                st.session_state.processing_mode_override = True
                st.success(f"Processing mode set to: **{chosen.upper()}**")
        
        st.caption("ℹ️ Server = safest. Local = fastest for large files. Hybrid = best for medium files. (Local/Hybrid modes require Pyodide - coming in CHUNK 7.2+)")
    
    # Add upload progress tracking JavaScript only when data is not fully loaded
    if not st.session_state.get("data_loaded_successfully", False):
        # This injects a client-side progress display near the uploader
        st.markdown("""
    <script>
    (function() {
        let progressInterval = null;
        
        function initUploadProgress() {
            // Try multiple selectors to find file input
            const fileInput = document.querySelector('input[type="file"]') || 
                             document.querySelector('[data-testid="stFileUploader"] input[type="file"]') ||
                             document.querySelector('input[type="file"][accept]');
            if (!fileInput) {
                setTimeout(initUploadProgress, 200);
                return;
            }
            
            // Find the file uploader container to insert progress display after it
            const uploaderContainer = fileInput.closest('[data-testid="stFileUploader"]');
            if (!uploaderContainer) return;
            
            // Create progress container if it doesn't exist
            let progressContainer = document.getElementById('upload-progress-container');
            if (!progressContainer) {
                progressContainer = document.createElement('div');
                progressContainer.id = 'upload-progress-container';
                progressContainer.style.cssText = 'display: none; margin: 1.5rem 0; padding: 1.25rem; background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border: 2px solid #3b82f6; border-radius: 12px; box-shadow: 0 4px 12px rgba(59,130,246,0.2); z-index: 999;';
                
                // Insert after the uploader container
                if (uploaderContainer.parentNode) {
                    uploaderContainer.parentNode.insertBefore(progressContainer, uploaderContainer.nextSibling);
                }
            }
            
            // Monitor file input changes
            fileInput.addEventListener('change', function(e) {
                const files = e.target.files;
                if (!files || files.length === 0) {
                    if (progressContainer) {
                        progressContainer.style.display = 'none';
                    }
                    if (progressInterval) {
                        clearInterval(progressInterval);
                        progressInterval = null;
                    }
                    return;
                }
                
                // Calculate total size
                let totalSize = 0;
                const fileArray = Array.from(files);
                fileArray.forEach(file => {
                    totalSize += file.size;
                });
                
                // Build progress container HTML
                progressContainer.innerHTML = `
                    <div style="margin-bottom: 1rem;">
                        <div style="font-size: 1.2rem; font-weight: 600; color: #1e40af; margin-bottom: 0.5rem;">📤 Uploading Files...</div>
                        <div style="display: flex; align-items: baseline; gap: 0.5rem; flex-wrap: wrap;">
                            <div style="font-size: 1rem; color: #475569; font-weight: 600;">Overall Progress: <span id="overall-progress-text" style="color: #ea580c; font-size: 1.2rem; font-weight: 700;">0%</span></div>
                            <div style="font-size: 0.9rem; color: #64748b;" id="overall-progress-size">0 MB / 0 MB</div>
                        </div>
                    </div>
                    <div id="file-progress-list" style="max-height: 400px; overflow-y: auto;"></div>
                `;
                
                // Show progress container
                progressContainer.style.display = 'block';
                
                // Create progress bars for each file
                const fileList = document.getElementById('file-progress-list');
                fileList.innerHTML = '';
                
                const fileData = fileArray.map((file, index) => ({
                    name: file.name,
                    size: file.size,
                    index: index
                }));
                
                fileData.forEach((file, idx) => {
                    const fileSizeMB = (file.size / (1024 * 1024)).toFixed(2);
                    const filePercent = totalSize > 0 ? ((file.size / totalSize) * 100).toFixed(1) : 0;
                    
                    const fileDiv = document.createElement('div');
                    fileDiv.style.cssText = 'margin-bottom: 1rem; padding: 0.75rem; background: white; border-radius: 8px; border-left: 3px solid #3b82f6; box-shadow: 0 2px 4px rgba(0,0,0,0.05);';
                    
                    fileDiv.innerHTML = `
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                            <div style="font-weight: 600; color: #1e293b; font-size: 0.9rem; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${file.name}">${file.name}</div>
                        </div>
                        <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem;">
                            <div style="flex: 1; position: relative; height: 12px; background: #e2e8f0; border-radius: 999px; overflow: hidden; box-shadow: inset 0 1px 2px rgba(0,0,0,0.1);">
                                <div id="progress-bar-${idx}" style="height: 100%; background: linear-gradient(90deg, #f97316 0%, #ea580c 100%); border-radius: 999px; transition: width 0.3s ease; width: 0%; box-shadow: 0 1px 3px rgba(249,115,22,0.4);"></div>
                            </div>
                            <div style="display: flex; flex-direction: column; align-items: flex-end; min-width: 120px;">
                                <div id="progress-text-${idx}" style="font-size: 0.95rem; font-weight: 700; color: #ea580c; line-height: 1.2;">0% (0 MB / ${fileSizeMB} MB)</div>
                                <div id="progress-size-${idx}" style="font-size: 0.8rem; color: #64748b; line-height: 1.2;">Remaining: ${fileSizeMB} MB</div>
                            </div>
                        </div>
                    `;
                    
                    fileList.appendChild(fileDiv);
                });
                
                // Simulate/update progress
                if (progressInterval) {
                    clearInterval(progressInterval);
                }
                
                let progress = 0;
                let uploadedBytes = 0;
                
                // Track individual file progress
                const fileProgress = fileArray.map(() => ({ bytes: 0, percent: 0 }));
                
                progressInterval = setInterval(() => {
                    // Check if files are actually uploaded (Streamlit shows file tags)
                    const uploadedTags = document.querySelectorAll('[data-testid="stFileUploader"] [data-baseweb="tag"]');
                    const uploadedCount = uploadedTags.length;
                    
                    // Check for Streamlit's internal upload progress
                    const streamlitProgressBars = document.querySelectorAll('[data-testid="stFileUploader"] [role="progressbar"]');
                    
                    if (uploadedCount === files.length && progress < 100) {
                        // All files uploaded, complete progress
                        progress = 100;
                        uploadedBytes = totalSize;
                        fileProgress.forEach((fp, idx) => {
                            fp.percent = 100;
                            fp.bytes = fileArray[idx].size;
                        });
                        clearInterval(progressInterval);
                        progressInterval = null;
                    } else if (uploadedCount > 0 || streamlitProgressBars.length > 0) {
                        // Files are uploading, estimate progress based on Streamlit's progress
                        if (streamlitProgressBars.length > 0) {
                            // Try to read progress from Streamlit's progress bar
                            streamlitProgressBars.forEach((pb, idx) => {
                                const ariaValueNow = pb.getAttribute('aria-valuenow');
                                const ariaValueMax = pb.getAttribute('aria-valuemax');
                                if (ariaValueNow && ariaValueMax) {
                                    const fileProgressPercent = (parseFloat(ariaValueNow) / parseFloat(ariaValueMax)) * 100;
                                    if (idx < fileProgress.length) {
                                        fileProgress[idx].percent = fileProgressPercent;
                                        fileProgress[idx].bytes = (fileArray[idx].size * fileProgressPercent / 100);
                                    }
                                }
                            });
                            // Calculate overall progress
                            const totalProgressBytes = fileProgress.reduce((sum, fp) => sum + fp.bytes, 0);
                            progress = (totalProgressBytes / totalSize) * 100;
                            uploadedBytes = totalProgressBytes;
                        } else {
                            // Estimate based on uploaded count
                            progress = Math.min(90, (uploadedCount / files.length) * 100);
                            uploadedBytes = (totalSize * progress / 100);
                            fileProgress.forEach((fp, idx) => {
                                fp.percent = progress;
                                fp.bytes = (fileArray[idx].size * progress / 100);
                            });
                        }
                    } else {
                        // Still uploading, simulate progress with acceleration
                        const increment = progress < 30 ? 3 : progress < 70 ? 2 : 1;
                        progress = Math.min(progress + increment, 85);
                        uploadedBytes = (totalSize * progress / 100);
                        fileProgress.forEach((fp, idx) => {
                            fp.percent = progress;
                            fp.bytes = (fileArray[idx].size * progress / 100);
                        });
                    }
                    
                    // Update overall progress
                    const overallText = document.getElementById('overall-progress-text');
                    if (overallText) {
                        overallText.textContent = Math.round(progress) + '%';
                    }
                    
                    // Update individual file progress with size tracking
                    fileArray.forEach((file, index) => {
                        const bar = document.getElementById(`progress-bar-${index}`);
                        const text = document.getElementById(`progress-text-${index}`);
                        const sizeText = document.getElementById(`progress-size-${index}`);
                        const fileProg = fileProgress[index];
                        const fileProgressPercent = fileProg ? fileProg.percent : progress;
                        const fileUploadedBytes = fileProg ? fileProg.bytes : (file.size * progress / 100);
                        const fileSizeMB = (file.size / (1024 * 1024));
                        const uploadedMB = (fileUploadedBytes / (1024 * 1024));
                        
                        if (bar) {
                            bar.style.width = Math.min(100, Math.max(0, fileProgressPercent)) + '%';
                        }
                        if (text) {
                            text.textContent = `${fileProgressPercent.toFixed(1)}% (${uploadedMB.toFixed(1)} MB / ${fileSizeMB.toFixed(1)} MB)`;
                        }
                        if (sizeText) {
                            const remainingBytes = Math.max(file.size - fileUploadedBytes, 0);
                            sizeText.textContent = `Remaining: ${formatBytes(remainingBytes)}`;
                        }
                    });
                    
                    // Update overall progress with total size
                    const overallSizeText = document.getElementById('overall-progress-size');
                    if (overallSizeText) {
                        const totalSizeMB = totalSize / (1024 * 1024);
                        const totalUploadedMB = (totalSizeMB * progress / 100).toFixed(1);
                        overallSizeText.textContent = `${totalUploadedMB} MB / ${totalSizeMB.toFixed(1)} MB`;
                    }
                    
                    if (progress >= 100) {
                        clearInterval(progressInterval);
                        progressInterval = null;
                    }
                }, 300);
            });
        }
        
        // Start monitoring
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initUploadProgress);
        } else {
            setTimeout(initUploadProgress, 500);
        }
        
        // Re-initialize after Streamlit reruns
        const observer = new MutationObserver((mutations) => {
            // Check if file uploader was added/modified
            const hasFileUploader = document.querySelector('[data-testid="stFileUploader"]');
            if (hasFileUploader && !document.getElementById('upload-progress-container')) {
                setTimeout(initUploadProgress, 500);
            }
            
            // Monitor Streamlit's progress bars and update our display
            const streamlitBars = document.querySelectorAll('[data-testid="stFileUploader"] [role="progressbar"]');
            if (streamlitBars.length > 0 && progressInterval === null) {
                // Files are uploading, show our progress display
                const fileInput = document.querySelector('input[type="file"]');
                if (fileInput && fileInput.files && fileInput.files.length > 0) {
                    fileInput.dispatchEvent(new Event('change', { bubbles: true }));
                }
            }
        });
        observer.observe(document.body, { childList: true, subtree: true });
        
        // Also try to monitor Streamlit's file upload progress directly
        setInterval(() => {
            const streamlitProgress = document.querySelector('[data-testid="stFileUploader"] [role="progressbar"]');
            if (streamlitProgress && document.getElementById('upload-progress-container')) {
                const ariaValueNow = streamlitProgress.getAttribute('aria-valuenow');
                const ariaValueMax = streamlitProgress.getAttribute('aria-valuemax');
                if (ariaValueNow && ariaValueMax) {
                    const percent = Math.round((parseFloat(ariaValueNow) / parseFloat(ariaValueMax)) * 100);
                    const progressText = document.getElementById('overall-progress-text');
                    if (progressText) progressText.textContent = percent + '%';
                    
                    // Update progress bars
                    document.querySelectorAll('[id^="progress-bar-"]').forEach(bar => {
                        const idx = bar.id.replace('progress-bar-', '');
                        bar.style.width = percent + '%';
                        const text = document.getElementById('progress-text-' + idx);
                        if (text) text.textContent = percent + '%';
                    });
                }
            }
        }, 200);
    })();
    </script>
    """, unsafe_allow_html=True)

    # Show upload status and file info if files are uploaded OR data is already loaded
    data_loaded = st.session_state.data is not None and st.session_state.normalized_data is not None
    
    if uploaded_files or data_loaded:
        # Use uploaded file info if available, otherwise use session state stored info
        if uploaded_files:
            total_size = sum(f.size for f in uploaded_files)
            size_mb = total_size / (1024 * 1024)
            total_files = len(uploaded_files)
        elif data_loaded:
            # Data is loaded but files are not in session (e.g., after rerun from quantum toggle)
            # Use stored info from session state
            total_size = st.session_state.get('uploaded_file_size', 0)
            size_mb = total_size / (1024 * 1024) if total_size > 0 else 0
            total_files = st.session_state.get('uploaded_file_count', 1)
            # If no stored size, estimate from data
            if total_size == 0 and st.session_state.data is not None:
                size_mb = len(st.session_state.data) * 0.001  # Rough estimate
                total_files = 1
        else:
            total_size = 0
            size_mb = 0
            total_files = 0
        
        # Show upload completion status card
        st.markdown(f"""
        <div class='block-card' style='background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); border: 2px solid #22c55e; padding: 1rem; margin: 0.75rem 0; box-shadow: 0 2px 8px rgba(34,197,94,0.2);'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div>
                    <div style='font-size: 1.1rem; font-weight: 600; color: #15803d; margin-bottom: 0.25rem;'>✅ Upload Complete</div>
                    <div style='font-size: 0.9rem; color: #16a34a;'>📁 {total_files} file(s) • {size_mb:.1f} MB total</div>
                </div>
                <div style='text-align: right;'>
                    <div style='font-size: 1.5rem; font-weight: 700; color: #15803d;'>100%</div>
                    <div style='font-size: 0.75rem; color: #16a34a;'>Complete</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Show individual files with progress indicators
        if uploaded_files:
            with st.expander(f"📋 View {total_files} uploaded file(s) (100% uploaded)", expanded=False):
                for i, f in enumerate(uploaded_files, 1):
                    file_size_mb = f.size / (1024 * 1024)
                    file_percent = (file_size_mb / size_mb * 100) if size_mb > 0 else 0
                    st.markdown(f"""
                    <div style='padding: 0.5rem; background: #f8fafc; border-radius: 6px; margin-bottom: 0.5rem; border-left: 3px solid #22c55e;'>
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <div>
                                <strong>#{i}. {f.name}</strong>
                                <div style='font-size: 0.85rem; color: #64748b;'>{file_size_mb:.1f} MB ({file_percent:.1f}% of total)</div>
                            </div>
                            <div style='background: #dcfce7; color: #15803d; padding: 0.25rem 0.75rem; border-radius: 999px; font-size: 0.85rem; font-weight: 600;'>✅ 100%</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        elif data_loaded and st.session_state.get('uploaded_file_names'):
            # Show stored file names if data is loaded but files are not in session
            with st.expander(f"📋 View {total_files} processed file(s) (100% complete)", expanded=False):
                for i, file_name in enumerate(st.session_state.get('uploaded_file_names', []), 1):
                    st.markdown(f"""
                    <div style='padding: 0.5rem; background: #f8fafc; border-radius: 6px; margin-bottom: 0.5rem; border-left: 3px solid #22c55e;'>
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <div>
                                <strong>#{i}. {file_name}</strong>
                                <div style='font-size: 0.85rem; color: #64748b;'>Processed successfully</div>
                            </div>
                            <div style='background: #dcfce7; color: #15803d; padding: 0.25rem 0.75rem; border-radius: 999px; font-size: 0.85rem; font-weight: 600;'>✅ 100%</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    # Show "Load & map data" button only if files are uploaded but not yet loaded
    # Also check if we've already processed these files (prevents reprocessing on rerun)
    loading_in_progress = st.session_state.get("loading_in_progress", False)
    show_load_button = uploaded_files and not loading_in_progress  # Allow even if data is already loaded (for combining)
    
    if show_load_button:
        # Add combine option if data is already loaded
        combine_with_existing = False
        if data_loaded:
            combine_with_existing = st.checkbox(
                f"🔗 Combine with existing data ({len(st.session_state.normalized_data):,} cases) - don't replace",
                value=False,
                key="combine_upload_with_existing"
            )
        
        button_label = "🔄 Load & map data" if not combine_with_existing else f"🔄 Add to existing data ({len(st.session_state.normalized_data):,} cases)"
        load_clicked = st.button(button_label, disabled=not uploaded_files)
    elif data_loaded:
        # Data is already loaded - show prominent status instead of button
        # Check database storage status
        db_status = st.session_state.get('db_storage_status', None)
        from src.auth.auth import is_authenticated
        
        # Build status message HTML
        status_html = """<div style='padding: 1rem; background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%); border: 2px solid #22c55e; border-radius: 8px; margin: 0.75rem 0;'>
<div style='font-size: 1.1rem; font-weight: 700; color: #15803d; margin-bottom: 0.5rem;'>✅ Data Already Loaded</div>
<div style='font-size: 0.95rem; color: #16a34a; margin-bottom: 0.75rem;'>
Your data is ready! Scroll down to <strong>Step 2: Query Your Data</strong> to start exploring.
</div>"""
        
        # Add database storage status if available
        if db_status:
            if db_status.get("success"):
                inserted = db_status.get('inserted', 0)
                duplicates = db_status.get('duplicates', 0)
                total = db_status.get('total', 0)
                
                duplicate_info = ""
                if duplicates > 0:
                    duplicate_info = f"<div style='font-size: 0.85rem; color: #f59e0b; margin-top: 0.25rem;'>⚠️ <strong>{duplicates:,}</strong> duplicate(s) skipped (already in database)</div>"
                
                status_html += f"""<div style='padding: 0.75rem; background: #f0fdf4; border-left: 4px solid #22c55e; border-radius: 6px; margin-top: 0.5rem;'>
<div style='font-size: 0.9rem; font-weight: 600; color: #15803d; margin-bottom: 0.25rem;'>💾 Database Storage</div>
<div style='font-size: 0.85rem; color: #16a34a;'>
✅ <strong>{inserted:,}</strong> new case(s) saved to database (out of {total:,} total)
</div>
{duplicate_info}
<div style='font-size: 0.8rem; color: #64748b; margin-top: 0.25rem;'>
Your data will persist across sessions and can be accessed from any device.
</div>
</div>"""
            else:
                # Failed storage
                inserted = db_status.get('inserted', 0)
                total = db_status.get('total', 0)
                error_msg = db_status.get('error') or db_status.get('message', 'Database storage unavailable')
                error_details = db_status.get('error_details', [])
                
                # Check if 0 cases were saved (critical error)
                if inserted == 0 and total > 0:
                    error_causes_html = "<div style='font-size: 0.8rem; color: #7f1d1d; margin-top: 0.5rem;'><strong>Possible causes:</strong><ul style='margin: 0.25rem 0; padding-left: 1.5rem;'><li>RLS (Row-Level Security) policy blocking inserts</li><li>Invalid user_id or user not authenticated properly</li><li>Database connection issue</li><li>Missing SUPABASE_SERVICE_KEY in environment</li></ul></div>" if error_details else ""
                    status_html += f"""<div style='padding: 0.75rem; background: #fef2f2; border-left: 4px solid #ef4444; border-radius: 6px; margin-top: 0.5rem;'>
<div style='font-size: 0.9rem; font-weight: 600; color: #dc2626; margin-bottom: 0.25rem;'>💾 Database Storage - CRITICAL ERROR</div>
<div style='font-size: 0.85rem; color: #dc2626; margin-bottom: 0.5rem;'>
❌ <strong>0 cases saved</strong> out of {total:,} total
</div>
<div style='font-size: 0.85rem; color: #991b1b; margin-bottom: 0.5rem; padding: 0.5rem; background: #fee2e2; border-radius: 4px;'>
<strong>Error:</strong> {error_msg[:300]}{'...' if len(error_msg) > 300 else ''}
</div>
{error_causes_html}
<div style='font-size: 0.8rem; color: #64748b; margin-top: 0.5rem;'>
⚠️ Data is loaded in session memory only. It will be lost if you refresh the page.
</div>
</div>"""
                else:
                    # Other error (partial failure or different issue)
                    status_html += f"""<div style='padding: 0.75rem; background: #fefce8; border-left: 4px solid #eab308; border-radius: 6px; margin-top: 0.5rem;'>
<div style='font-size: 0.9rem; font-weight: 600; color: #a16207; margin-bottom: 0.25rem;'>💾 Database Storage</div>
<div style='font-size: 0.85rem; color: #ca8a04;'>
⚠️ {error_msg}
</div>
<div style='font-size: 0.8rem; color: #64748b; margin-top: 0.25rem;'>
Data is loaded in session memory only. It will be lost if you refresh the page.
</div>
</div>"""
        elif is_authenticated():
            # Authenticated but no storage status yet - offer to save
            status_html += """<div style='padding: 0.75rem; background: #eff6ff; border-left: 4px solid #3b82f6; border-radius: 6px; margin-top: 0.5rem;'>
<div style='font-size: 0.9rem; font-weight: 600; color: #1e40af; margin-bottom: 0.25rem;'>💾 Database Storage</div>
<div style='font-size: 0.85rem; color: #2563eb;'>
ℹ️ Database storage status unavailable. Data may need to be re-uploaded to save to database.
</div>
</div>"""
        else:
            # Not authenticated
            status_html += """<div style='padding: 0.75rem; background: #f8fafc; border-left: 4px solid #94a3b8; border-radius: 6px; margin-top: 0.5rem;'>
<div style='font-size: 0.9rem; font-weight: 600; color: #475569; margin-bottom: 0.25rem;'>💾 Database Storage</div>
<div style='font-size: 0.85rem; color: #64748b;'>
ℹ️ Data is loaded in session memory only. <a href="/Login" style="color: #3b82f6; text-decoration: underline;">Login</a> to save data to database for persistence.
</div>
</div>"""
        
        status_html += "</div>"
        st.markdown(status_html, unsafe_allow_html=True)
        load_clicked = False
    elif loading_in_progress:
        # Loading is in progress - show status
        st.info("⏳ Processing your files... Please wait.")
        load_clicked = False
    else:
        load_clicked = False

    if load_clicked and uploaded_files:
        # Check for duplicate files (NEW - Phase 1: File Upload History)
        try:
            from src.auth.auth import is_authenticated, get_current_user
            from src.file_upload_history import check_duplicate_file
            
            if is_authenticated():
                user = get_current_user()
                if user:
                    user_id = user.get('user_id')
                    organization = user.get('organization', '')
                    
                    # Check each uploaded file for duplicates
                    duplicate_warnings = []
                    for file in uploaded_files:
                        duplicate = check_duplicate_file(
                            user_id, organization, file.name, file.size
                        )
                        if duplicate:
                            upload_date = duplicate.get('uploaded_at', '')
                            case_count = duplicate.get('total_cases', 0) or 0
                            duplicate_warnings.append({
                                'filename': file.name,
                                'size_mb': file.size / (1024 * 1024),
                                'uploaded_at': upload_date,
                                'cases': case_count
                            })
                    
                    # Show duplicate warnings if any
                    if duplicate_warnings:
                        st.warning("⚠️ **Potential Duplicate Files Detected:**")
                        for dup in duplicate_warnings:
                            upload_date_str = dup['uploaded_at'][:10] if dup['uploaded_at'] and len(dup['uploaded_at']) >= 10 else 'unknown date'
                            st.info(
                                f"📄 **{dup['filename']}** ({dup['size_mb']:.1f} MB) - "
                                f"Previously uploaded on {upload_date_str} "
                                f"with {dup['cases']:,} cases. "
                                "This file will be processed anyway, but you can skip it if it's a duplicate."
                            )
        except Exception:
            pass  # Don't break upload if duplicate check fails
        
        # Calculate total size for progress tracking
        total_size_bytes = sum(f.size for f in uploaded_files)
        total_size_mb = total_size_bytes / (1024 * 1024)
        total_files = len(uploaded_files)
        
        # Initialize file progress tracking in session state
        if 'file_progress' not in st.session_state:
            st.session_state.file_progress = {}
        
        # Initialize all files as pending
        for idx, file in enumerate(uploaded_files):
            file_key = f"file_{idx}"
            if file_key not in st.session_state.file_progress:
                file_size_mb = file.size / (1024 * 1024)
                st.session_state.file_progress[file_key] = {
                    'name': file.name,
                    'size_mb': file_size_mb,
                    'size_bytes': file.size,
                    'status': 'pending',  # pending, processing, complete
                    'progress_pct': 0,
                    'processed_mb': 0,
                    'current_step': None,
                    'internal_files': None
                }
        
        # Create a VERY prominent progress display card with metrics
        st.markdown(f"""
        <div class='block-card' style='background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border: 3px solid #3b82f6; padding: 1.5rem; margin: 1rem 0; box-shadow: 0 4px 12px rgba(59,130,246,0.3);'>
            <h3 style='margin-top: 0; color: #1e40af; font-size: 1.3rem;'>📤 Processing {total_files} File(s)</h3>
            <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem;'>
                <div style='background: white; padding: 1rem; border-radius: 8px; border: 2px solid #93c5fd;'>
                    <div style='font-size: 0.9rem; color: #64748b; margin-bottom: 0.5rem;'>Total Size</div>
                    <div style='font-size: 1.5rem; font-weight: 700; color: #1e40af;'>{total_size_mb:.1f} MB</div>
                </div>
                <div style='background: white; padding: 1rem; border-radius: 8px; border: 2px solid #93c5fd;'>
                    <div style='font-size: 0.9rem; color: #64748b; margin-bottom: 0.5rem;'>Files</div>
                    <div style='font-size: 1.5rem; font-weight: 700; color: #1e40af;'>0 / {total_files}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Create file list container for individual file progress (updatable)
        st.markdown("<h4 style='color: #1e40af; margin-top: 1.5rem; margin-bottom: 1rem;'>📋 File Progress</h4>", unsafe_allow_html=True)
        file_list_container = st.empty()
        
        # Helper function to render file list with progress (defined early so it can be called)
        def render_file_list():
            # Create HTML for file list (single line to prevent Streamlit from displaying as text)
            file_list_html = "<div style='background: white; border-radius: 8px; padding: 1rem; border: 1px solid #e2e8f0; max-height: 500px; overflow-y: auto;'>"
            
            for idx, file in enumerate(uploaded_files):
                file_key = f"file_{idx}"
                file_info = st.session_state.file_progress.get(file_key, {})
                
                file_name = file_info.get('name', file.name)
                file_size_mb = file_info.get('size_mb', file.size / (1024 * 1024))
                status = file_info.get('status', 'pending')
                progress_pct = file_info.get('progress_pct', 0)
                processed_mb = file_info.get('processed_mb', 0)
                current_step = file_info.get('current_step', None)
                internal_files = file_info.get('internal_files', None)
                
                # Determine status color and icon
                if status == 'complete':
                    status_color = '#16a34a'
                    status_icon = '✅'
                elif status == 'processing':
                    status_color = '#3b82f6'
                    status_icon = '⚙️'
                else:
                    status_color = '#94a3b8'
                    status_icon = '⏳'
                
                # Progress bar color
                if progress_pct == 100:
                    progress_color = '#22c55e'
                elif progress_pct > 0:
                    progress_color = '#3b82f6'
                else:
                    progress_color = '#e2e8f0'
                
                # Escape HTML entities in file name to prevent injection
                file_name_escaped = str(file_name).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;")
                
                # Build file card HTML (single line to prevent text display)
                file_list_html += f"<div style='padding:1rem;margin-bottom:0.75rem;background:#f8fafc;border-radius:6px;border-left:4px solid {status_color};'><div style='display:flex;justify-content:space-between;align-items:start;margin-bottom:0.5rem;'><div style='flex:1;'><div style='font-weight:600;color:#1e293b;font-size:0.95rem;margin-bottom:0.25rem;'>{status_icon} <code style='background:white;padding:2px 6px;border-radius:3px;font-size:0.9rem;'>{file_name_escaped}</code></div><div style='font-size:0.85rem;color:#64748b;'>{file_size_mb:.1f} MB</div></div><div style='text-align:right;margin-left:1rem;'><div style='font-weight:700;font-size:1.1rem;color:{status_color};'>{progress_pct:.0f}%</div><div style='font-size:0.8rem;color:#64748b;'>{processed_mb:.1f} MB / {file_size_mb:.1f} MB</div></div></div><div style='margin-top:0.5rem;'><div style='background:#e2e8f0;height:8px;border-radius:4px;overflow:hidden;'><div style='background:{progress_color};height:100%;width:{progress_pct}%;transition:width 0.3s ease;'></div></div></div>"
                
                # Show current step if processing
                if status == 'processing' and current_step:
                    # Escape step name for HTML
                    step_escaped = str(current_step).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;")
                    file_list_html += f"<div style='margin-top: 0.5rem; font-size: 0.85rem; color: #475569; font-style: italic;'>{step_escaped}</div>"
                
                # Show internal files progress if available
                if internal_files:
                    internal_current, internal_total = internal_files
                    file_list_html += f"<div style='margin-top: 0.5rem; font-size: 0.8rem; color: #64748b;'>Internal files: {internal_current}/{internal_total}</div>"
                
                file_list_html += "</div>"
            
            file_list_html += "</div>"
            # Use markdown with unsafe_allow_html to render HTML properly
            file_list_container.markdown(file_list_html, unsafe_allow_html=True)
        
        # Render initial file list (all pending)
        render_file_list()
        
        # Create VERY prominent progress tracking UI
        progress_bar = st.progress(0)
        
        # Large, visible progress indicators
        progress_metrics = st.container()
        with progress_metrics:
            col1, col2, col3 = st.columns(3)
            
            # Status container
            status_container = st.empty()
            
            with col1:
                bytes_container = st.empty()
            with col2:
                percentage_container = st.empty()
            with col3:
                files_container = st.empty()
            
            # Initialize display with VERY prominent styling
            status_container.markdown(
                f"<div style='font-size: 1.2rem; font-weight: 600; color: #1e40af; margin: 1rem 0; padding: 0.75rem; background: #e0f2fe; border-radius: 8px;'>"
                f"📤 Starting to process {total_files} file(s) ({total_size_mb:.1f} MB total)...</div>",
                unsafe_allow_html=True
            )
            
            bytes_container.markdown(
                f"<div style='text-align: center;'>"
                f"<div style='font-size: 0.85rem; color: #64748b; margin-bottom: 0.25rem;'>Bytes Processed</div>"
                f"<div style='font-size: 1.8rem; font-weight: 700; color: #2563eb;'>0.0 MB</div>"
                f"<div style='font-size: 0.9rem; color: #94a3b8;'>/ {total_size_mb:.1f} MB</div></div>",
                unsafe_allow_html=True
            )
            
            percentage_container.markdown(
                f"<div style='text-align: center;'>"
                f"<div style='font-size: 0.85rem; color: #64748b; margin-bottom: 0.25rem;'>Progress</div>"
                f"<div style='font-size: 1.8rem; font-weight: 700; color: #16a34a;'>0%</div>"
                f"<div style='font-size: 0.9rem; color: #94a3b8;'>Complete</div></div>",
                unsafe_allow_html=True
            )
            
            files_container.markdown(
                f"<div style='text-align: center;'>"
                f"<div style='font-size: 0.85rem; color: #64748b; margin-bottom: 0.25rem;'>Files</div>"
                f"<div style='font-size: 1.8rem; font-weight: 700; color: #7c3aed;'>0</div>"
                f"<div style='font-size: 0.9rem; color: #94a3b8;'>/ {total_files}</div></div>",
                unsafe_allow_html=True
            )
        
        # Define progress callback with file size tracking and step-level updates
        def update_progress(current_file_num, total_file_num, file_name, file_size_bytes=None, step_info=None):
            # Update file progress in session state
            file_key = f"file_{current_file_num - 1}"
            if file_key in st.session_state.file_progress:
                st.session_state.file_progress[file_key]['status'] = 'processing'
                if step_info:
                    st.session_state.file_progress[file_key]['current_step'] = step_info.get('step', 'Processing...')
                    internal_file = step_info.get('internal_file', 0)
                    total_internal = step_info.get('total_internal', 1)
                    st.session_state.file_progress[file_key]['internal_files'] = (internal_file, total_internal)
                    
                    # Calculate progress based on step
                    step_progress = step_info.get('step_progress', 0)
                    if file_size_bytes:
                        processed_bytes = file_size_bytes * step_progress / 100
                        processed_mb = processed_bytes / (1024 * 1024)
                        st.session_state.file_progress[file_key]['processed_mb'] = processed_mb
                        st.session_state.file_progress[file_key]['progress_pct'] = step_progress
                elif file_size_bytes:
                    # File complete
                    st.session_state.file_progress[file_key]['processed_mb'] = file_size_bytes / (1024 * 1024)
                    st.session_state.file_progress[file_key]['progress_pct'] = 100
                    st.session_state.file_progress[file_key]['status'] = 'complete'
                    st.session_state.file_progress[file_key]['current_step'] = None
            
            # Mark previous files as complete
            for i in range(current_file_num - 1):
                prev_file_key = f"file_{i}"
                if prev_file_key in st.session_state.file_progress:
                    st.session_state.file_progress[prev_file_key]['status'] = 'complete'
                    st.session_state.file_progress[prev_file_key]['progress_pct'] = 100
                    st.session_state.file_progress[prev_file_key]['processed_mb'] = st.session_state.file_progress[prev_file_key]['size_mb']
            
            # Calculate file progress
            file_progress = current_file_num / total_file_num
            
            # Render file list (update UI)
            try:
                render_file_list()
            except Exception as e:
                # Silently fail if rendering fails to avoid breaking progress
                pass
            
            # Handle step-level progress for FAERS ZIP processing
            if step_info and isinstance(step_info, dict):
                step_name = step_info.get('step', 'Processing...')
                step_progress = step_info.get('step_progress', 0)
                internal_file = step_info.get('internal_file', 0)
                total_internal = step_info.get('total_internal', 1)
                
                # Update status with step information
                status_container.markdown(
                    f"<div style='font-size: 1.2rem; font-weight: 600; color: #1e40af; margin: 1rem 0; padding: 0.75rem; background: #e0f2fe; border-radius: 8px; border-left: 4px solid #3b82f6;'>"
                    f"📄 {file_name}<br>"
                    f"<span style='font-size: 1rem; color: #475569; font-weight: 500;'>{step_name}</span><br>"
                    f"<span style='font-size: 0.9rem; color: #64748b;'>Internal files: {internal_file}/{total_internal}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
                
                # Calculate bytes based on step progress
                if file_size_bytes:
                    processed_bytes = sum(f.size for f in uploaded_files[:current_file_num-1]) + (file_size_bytes * step_progress / 100)
                    processed_mb = processed_bytes / (1024 * 1024)
                    bytes_progress = processed_bytes / total_size_bytes if total_size_bytes > 0 else 0
                    
                    # Update progress bar
                    progress_bar.progress(bytes_progress)
                    
                    # Update metrics
                    bytes_container.markdown(
                        f"<div style='text-align: center;'>"
                        f"<div style='font-size: 0.85rem; color: #64748b; margin-bottom: 0.25rem;'>Bytes Processed</div>"
                        f"<div style='font-size: 1.8rem; font-weight: 700; color: #2563eb;'>{processed_mb:.1f} MB</div>"
                        f"<div style='font-size: 0.9rem; color: #94a3b8;'>/ {total_size_mb:.1f} MB</div></div>",
                        unsafe_allow_html=True
                    )
                    
                    percentage_container.markdown(
                        f"<div style='text-align: center;'>"
                        f"<div style='font-size: 0.85rem; color: #64748b; margin-bottom: 0.25rem;'>Progress</div>"
                        f"<div style='font-size: 1.8rem; font-weight: 700; color: #16a34a;'>{bytes_progress*100:.1f}%</div>"
                        f"<div style='font-size: 0.9rem; color: #94a3b8;'>Step: {step_progress:.0f}%</div></div>",
                        unsafe_allow_html=True
                    )
                    
                    files_container.markdown(
                        f"<div style='text-align: center;'>"
                        f"<div style='font-size: 0.85rem; color: #64748b; margin-bottom: 0.25rem;'>Files</div>"
                        f"<div style='font-size: 1.8rem; font-weight: 700; color: #7c3aed;'>{current_file_num}</div>"
                        f"<div style='font-size: 0.9rem; color: #94a3b8;'>/ {total_file_num}</div>"
                        f"<div style='font-size: 0.8rem; color: #94a3b8; margin-top: 0.25rem;'>{internal_file}/{total_internal} internal</div></div>",
                        unsafe_allow_html=True
                    )
                
                return  # Step-level progress handled above
            
            # Regular file-level progress (non-step-based)
            # Update processed bytes if file size provided
            if file_size_bytes:
                # Calculate cumulative bytes processed so far
                processed_bytes = sum(f.size for f in uploaded_files[:current_file_num])
                processed_mb = processed_bytes / (1024 * 1024)
                bytes_progress = processed_bytes / total_size_bytes if total_size_bytes > 0 else 0
                
                # Update progress bar (use bytes-based progress for more accuracy)
                progress_bar.progress(bytes_progress)
                
                # Update status displays with VERY prominent styling
                status_container.markdown(
                    f"<div style='font-size: 1.2rem; font-weight: 600; color: #1e40af; margin: 1rem 0; padding: 0.75rem; background: #e0f2fe; border-radius: 8px; border-left: 4px solid #3b82f6;'>"
                    f"📄 Processing file {current_file_num}/{total_file_num}: <code style='background: white; padding: 4px 8px; border-radius: 4px; font-weight: 600;'>{file_name}</code></div>",
                    unsafe_allow_html=True
                )
                
                # Update metrics in columns
                bytes_container.markdown(
                    f"<div style='text-align: center;'>"
                    f"<div style='font-size: 0.85rem; color: #64748b; margin-bottom: 0.25rem;'>Bytes Processed</div>"
                    f"<div style='font-size: 1.8rem; font-weight: 700; color: #2563eb;'>{processed_mb:.1f} MB</div>"
                    f"<div style='font-size: 0.9rem; color: #94a3b8;'>/ {total_size_mb:.1f} MB</div></div>",
                    unsafe_allow_html=True
                )
                
                percentage_container.markdown(
                    f"<div style='text-align: center;'>"
                    f"<div style='font-size: 0.85rem; color: #64748b; margin-bottom: 0.25rem;'>Progress</div>"
                    f"<div style='font-size: 1.8rem; font-weight: 700; color: #16a34a;'>{bytes_progress*100:.1f}%</div>"
                    f"<div style='font-size: 0.9rem; color: #94a3b8;'>Complete</div></div>",
                    unsafe_allow_html=True
                )
                
                files_container.markdown(
                    f"<div style='text-align: center;'>"
                    f"<div style='font-size: 0.85rem; color: #64748b; margin-bottom: 0.25rem;'>Files</div>"
                    f"<div style='font-size: 1.8rem; font-weight: 700; color: #7c3aed;'>{current_file_num}</div>"
                    f"<div style='font-size: 0.9rem; color: #94a3b8;'>/ {total_file_num}</div></div>",
                    unsafe_allow_html=True
                )
            else:
                # Fallback to file count progress
                progress_bar.progress(file_progress)
                status_container.markdown(
                    f"<div style='font-size: 1.2rem; font-weight: 600; color: #1e40af; margin: 1rem 0; padding: 0.75rem; background: #e0f2fe; border-radius: 8px; border-left: 4px solid #3b82f6;'>"
                    f"📄 Processing file {current_file_num}/{total_file_num}: <code style='background: white; padding: 4px 8px; border-radius: 4px; font-weight: 600;'>{file_name}</code></div>",
                    unsafe_allow_html=True
                )
                files_container.markdown(
                    f"<div style='text-align: center;'>"
                    f"<div style='font-size: 0.85rem; color: #64748b; margin-bottom: 0.25rem;'>Files</div>"
                    f"<div style='font-size: 1.8rem; font-weight: 700; color: #7c3aed;'>{current_file_num}</div>"
                    f"<div style='font-size: 0.9rem; color: #94a3b8;'>/ {total_file_num} ({file_progress*100:.0f}%)</div></div>",
                    unsafe_allow_html=True
                )
        
        st.session_state.loading_in_progress = True
        try:
            raw_df = load_all_files(uploaded_files, progress_callback=update_progress)
            
            # Mark all files as complete
            for file_key in st.session_state.file_progress:
                st.session_state.file_progress[file_key]['status'] = 'complete'
                st.session_state.file_progress[file_key]['progress_pct'] = 100
                st.session_state.file_progress[file_key]['processed_mb'] = st.session_state.file_progress[file_key]['size_mb']
            
            # Render final file list
            render_file_list()
            
            # Show completion with prominent styling - explicitly set to 100%
            progress_bar.progress(1.0)
            
            # Update all progress displays to show 100% completion
            status_container.markdown(
                "<div style='font-size: 1.2rem; font-weight: 700; color: #16a34a; margin: 0.5rem 0; padding: 0.75rem; background: #dcfce7; border-radius: 8px; border-left: 4px solid #22c55e;'>"
                "✅ All files processed successfully! (100% Complete)</div>",
                unsafe_allow_html=True
            )
            bytes_container.markdown(
                f"<div style='text-align: center;'>"
                f"<div style='font-size: 0.85rem; color: #64748b; margin-bottom: 0.25rem;'>Bytes Processed</div>"
                f"<div style='font-size: 1.8rem; font-weight: 700; color: #2563eb;'>{total_size_mb:.1f} MB</div>"
                f"<div style='font-size: 0.9rem; color: #94a3b8;'>/ {total_size_mb:.1f} MB</div></div>",
                unsafe_allow_html=True
            )
            percentage_container.markdown(
                f"<div style='text-align: center;'>"
                f"<div style='font-size: 0.85rem; color: #64748b; margin-bottom: 0.25rem;'>Progress</div>"
                f"<div style='font-size: 1.8rem; font-weight: 700; color: #16a34a;'>100.0%</div>"
                f"<div style='font-size: 0.9rem; color: #94a3b8;'>Complete</div></div>",
                unsafe_allow_html=True
            )
            files_container.markdown(
                f"<div style='text-align: center;'>"
                f"<div style='font-size: 0.85rem; color: #64748b; margin-bottom: 0.25rem;'>Files</div>"
                f"<div style='font-size: 1.8rem; font-weight: 700; color: #7c3aed;'>{total_files}</div>"
                f"<div style='font-size: 0.9rem; color: #94a3b8;'>/ {total_files} (100%)</div></div>",
                unsafe_allow_html=True
            )
            
            # Process loaded data if successful
            if raw_df is None or raw_df.empty:
                st.error("❌ Could not read any rows from the provided files. Please verify formats.")
                
                # Check if XML was detected
                xml_detected = any("xml" in f.name.lower() for f in uploaded_files) if uploaded_files else False
                
                # Add helpful suggestions
                st.markdown("**💡 What to try:**")
                if xml_detected:
                    st.error(
                        "**❌ XML format detected!** XML files are not currently supported.\n\n"
                        "**Solution:** Download FAERS data in **ASCII format** (not XML) from FDA's website. "
                        "FAERS ASCII files should have names like `DEMO23Q.txt`, `DRUG23Q.txt`, etc."
                    )
                st.markdown("""
                - **FAERS exports**: Ensure you upload all 7 **ASCII** files (DEMO, DRUG, REAC, OUTC, THER, INDI, RPSR) 
                  or a ZIP containing them. **Note: XML format is NOT supported** - use ASCII (.txt) format.
                - **Argus/Veeva exports**: Export as CSV or Excel. Column names should include drug/reaction identifiers.
                - **CSV files**: Ensure proper comma separation and headers in the first row.
                - **Excel files**: Check that data starts in row 1 with headers.
                - **PDF files**: Only tabular PDFs are supported. Try exporting to CSV/Excel instead.
                """)
                
                if st.session_state.get("analytics_enabled"):
                    analytics.log_event("upload_failed", {"file_count": len(uploaded_files) if uploaded_files else 0})
            else:
                # Data loaded successfully - store and normalize
                st.session_state.data = raw_df
                if st.session_state.get("analytics_enabled"):
                    analytics.log_event(
                        "upload_success",
                        {
                            "file_count": len(uploaded_files),
                            "row_count": len(raw_df),
                            "columns": len(raw_df.columns),
                        },
                    )

                # Try to reuse a saved mapping template based on column similarity
                current_columns = list(raw_df.columns)
                templates = st.session_state.get("schema_templates", {}) or {}
                tpl_name, tpl, tpl_score = mapping_templates.find_best_template_for_columns(
                    current_columns, templates
                )

                mapping = None
                normalized = None

                if tpl and tpl_name:
                    with st.expander("Suggested schema mapping template", expanded=True):
                        st.caption(
                            f"Template **{tpl_name}** matches this dataset (column overlap ~{tpl_score:.0%}). "
                            "You can start from this template or use auto-detected mapping."
                        )
                        choice = st.radio(
                            "Mapping strategy",
                            ["Use suggested template", "Use auto-detected mapping"],
                            index=0,
                        )
                    if choice == "Use suggested template":
                        mapping = tpl.get("mapping") or {}
                        try:
                            normalized = pv_schema.normalize_dataframe(raw_df, mapping)
                            st.info(
                                f"Using saved schema template **{tpl_name}** for column mapping."
                            )
                        except Exception:
                            mapping = None
                            normalized = None
                            st.warning(
                                "Saved template could not be applied cleanly. Falling back to auto-detected mapping."
                            )

                # If no template used or it failed, fall back to cached detection and normalization
                if mapping is None or normalized is None:
                    mapping, normalized = cached_detect_and_normalize(raw_df)
                st.session_state.schema_mapping = mapping

                essential = ["drug_name", "reaction", "case_id"]
                found = [f for f in essential if f in mapping]
                
                # Check if schema mapping needs manual correction
                show_schema_mapper = False
                
                if len(found) == 0:
                    st.warning(
                        "⚠️ **Auto-detection found no essential fields.**\n\n"
                        "**Detected columns:** " + (", ".join(raw_df.columns[:10]) if len(raw_df.columns) > 0 else "None") + 
                        ("..." if len(raw_df.columns) > 10 else "") + "\n\n"
                        "**Expected fields (at least 2 required):**\n"
                        "- Case/Report ID (e.g., case_id, ISR, primaryid)\n"
                        "- Drug Name (e.g., drug_name, medication, product)\n"
                        "- Adverse Reaction (e.g., reaction, adverse_event, PT)\n\n"
                        "Please use the schema mapper below to manually map your columns."
                    )
                    show_schema_mapper = True
                elif len(found) < 2:
                    st.warning(
                        f"⚠️ **Only {len(found)} essential field(s) auto-detected:** {', '.join(found)}\n\n"
                        "**Missing:** " + ", ".join([f for f in essential if f not in found]) + "\n\n"
                        "**Available columns in your file:**\n" + 
                        ", ".join(raw_df.columns[:15].tolist()) + 
                        ("..." if len(raw_df.columns) > 15 else "") + "\n\n"
                        "You can manually map columns below or continue with limited features."
                    )
                    show_schema_mapper = True
                
                # Show schema mapper if needed
                if show_schema_mapper:
                    st.markdown("---")
                    manual_mapping = render_schema_mapper(raw_df, mapping)
                    
                    if manual_mapping is not None:
                        # Use manual mapping
                        mapping = manual_mapping
                        st.session_state.schema_mapping = mapping
                        # Re-normalize with manual mapping
                        normalized = pv_schema.normalize_dataframe(raw_df, mapping)
                        st.success(f"✅ Schema mapping applied! {len(mapping)} fields mapped.")
                        # Update found essential fields for validation
                        found = [f for f in essential if f in mapping]
                    else:
                        # User hasn't applied mapping yet
                        if len(found) == 0:
                            st.error("❌ Cannot proceed without essential field mapping. Please map at least 2 essential fields above.")
                            st.markdown("</div>", unsafe_allow_html=True)
                            return
                        # If some fields were found, continue with auto-detected
                        st.info("ℹ️ Using auto-detected mapping. You can refine it using the schema mapper above.")
                
                # Final validation
                if len(found) < 2:
                    st.warning(
                        f"⚠️ Only {len(found)} essential field(s) mapped: {', '.join(found)}. "
                        "Some analysis features may be limited."
                    )
                
                # Check if we should combine with existing data
                if combine_with_existing and data_loaded:
                    # Combine with existing data
                    existing_df = st.session_state.normalized_data
                    combined_df = pd.concat([existing_df, normalized], ignore_index=True)
                    
                    # Remove duplicates based on case_id if available
                    if 'case_id' in combined_df.columns:
                        before_dedup = len(combined_df)
                        combined_df = combined_df.drop_duplicates(subset=['case_id'], keep='first')
                        duplicates_removed = before_dedup - len(combined_df)
                        if duplicates_removed > 0:
                            st.info(f"ℹ️ Removed {duplicates_removed:,} duplicate cases when combining with existing data.")
                    
                    st.session_state.normalized_data = combined_df
                    st.session_state.data = combined_df
                    st.success(f"✅ Combined: {len(existing_df):,} existing + {len(normalized):,} new = {len(combined_df):,} total cases")
                else:
                    # Replace existing data
                    st.session_state.normalized_data = normalized
                    st.session_state.data = normalized  # Also set data for compatibility
                
                # Store data in database if user is authenticated
                try:
                    from src.auth.auth import is_authenticated, get_current_user
                    from src.pv_storage import store_pv_data
                    
                    if is_authenticated() and normalized is not None and not normalized.empty:
                        user = get_current_user()
                        if user:
                            user_id = user.get('user_id')
                            organization = user.get('organization', '')
                            source = 'FAERS'  # Default, can be enhanced to detect source from file
                            
                            # Option 3: User Review - Choose duplicate handling mode
                            st.markdown("---")
                            st.markdown("### 💾 Database Storage Options")
                            
                            duplicate_handling = st.radio(
                                "How would you like to handle duplicates?",
                                [
                                    "Auto-skip duplicates (recommended)",
                                    "Save all (including duplicates)"
                                ],
                                index=0,
                                key="duplicate_handling_mode",
                                help="Auto-skip: Only save new unique cases. Save all: Save all records including duplicates (useful for audit/compliance)."
                            )
                            
                            skip_duplicate_check = (duplicate_handling == "Save all (including duplicates)")
                            
                            if skip_duplicate_check:
                                st.warning("⚠️ **Option 3: Save All** - All records (including duplicates) will be saved to database. You can review and merge duplicates later.")
                            
                            with st.spinner("💾 Storing data in database..."):
                                result = store_pv_data(normalized, user_id, organization, source, skip_duplicate_check=skip_duplicate_check)
                                inserted = result.get('inserted', 0)
                                total = result.get('total', len(normalized))
                                
                                duplicates = result.get("duplicates", 0)
                                
                                if result.get("success") and inserted > 0:
                                    # Store database storage status in session state for display after rerun
                                    if skip_duplicate_check:
                                        # Option 3: Save All - all records saved including duplicates
                                        message = f"✅ Data stored in database! {inserted:,} case(s) saved (including duplicates)."
                                        st.session_state.db_storage_status = {
                                            "success": True,
                                            "inserted": inserted,
                                            "duplicates": 0,  # Not skipped, all saved
                                            "total": total,
                                            "message": message,
                                            "mode": "save_all"
                                        }
                                        st.success(f"✅ Data stored in database! {inserted:,} case(s) saved (including duplicates). You can review and merge duplicates later using the Duplicate Detection panel.")
                                    else:
                                        # Auto-skip mode - duplicates were skipped
                                        message = f"✅ Data stored in database! {inserted:,} new case(s) saved."
                                        if duplicates > 0:
                                            message += f" {duplicates:,} duplicate(s) skipped."
                                        
                                        st.session_state.db_storage_status = {
                                            "success": True,
                                            "inserted": inserted,
                                            "duplicates": duplicates,
                                            "total": total,
                                            "message": message,
                                            "mode": "auto_skip"
                                        }
                                        
                                        if duplicates > 0:
                                            st.success(f"✅ Data stored in database! {inserted:,} new case(s) saved. ⚠️ {duplicates:,} duplicate(s) skipped (already in database).")
                                        else:
                                            st.success(f"✅ Data stored in database! {inserted:,} cases saved.")
                                elif inserted == 0 and duplicates > 0:
                                    # All records were duplicates
                                    st.info(f"ℹ️ All {duplicates:,} case(s) already exist in database. No new records inserted.")
                                    st.session_state.db_storage_status = {
                                        "success": True,
                                        "inserted": 0,
                                        "duplicates": duplicates,
                                        "total": total,
                                        "message": f"ℹ️ All {duplicates:,} case(s) already exist in database."
                                    }
                                elif inserted == 0 and total > 0:
                                    # Critical: 0 cases saved but we tried to save many
                                    error_msg = result.get("error", "Unknown error - no cases were inserted")
                                    error_details = result.get("error_details", [])
                                    
                                    st.session_state.db_storage_status = {
                                        "success": False,
                                        "inserted": 0,
                                        "total": total,
                                        "error": error_msg,
                                        "error_details": error_details,
                                        "message": f"⚠️ Database storage failed: {error_msg}"
                                    }
                                    st.error(f"❌ **Database Storage Failed:** {error_msg}")
                                    if error_details:
                                        with st.expander("📋 Error Details"):
                                            for detail in error_details:
                                                st.text(detail)
                                else:
                                    # Store failure status
                                    error_msg = result.get("error", "Unknown error")
                                    st.session_state.db_storage_status = {
                                        "success": False,
                                        "error": error_msg,
                                        "inserted": inserted,
                                        "total": total,
                                        "message": f"⚠️ Database storage failed: {error_msg}"
                                    }
                                    st.warning(f"⚠️ Database storage partially failed: {error_msg}")
                        else:
                            # User object not available - clear any previous status
                            st.session_state.db_storage_status = {
                                "success": False,
                                "error": "User profile not found",
                                "message": "ℹ️ Data loaded in session only (not saved to database)."
                            }
                    else:
                        # Not authenticated or no data - clear any previous status
                        if 'db_storage_status' in st.session_state:
                            del st.session_state.db_storage_status
                except Exception as e:
                    # Store error status
                    st.session_state.db_storage_status = {
                        "success": False,
                        "error": str(e),
                        "message": f"⚠️ Database storage failed: {str(e)[:100]}"
                    }
                    # Continue without database storage if it fails
                    pass
                
                # Store file info in session state for later display (survives reruns)
                if uploaded_files:
                    st.session_state.uploaded_file_size = sum(f.size for f in uploaded_files)
                    st.session_state.uploaded_file_count = len(uploaded_files)
                    st.session_state.uploaded_file_names = [f.name for f in uploaded_files]
                st.session_state.data_loaded_successfully = True
                # Mark that loading completed successfully - prevents reprocessing on rerun
                st.session_state.data_loaded_at = st.session_state.get("data_loaded_at", None) or st.session_state.get("_last_loaded", None)
                if not st.session_state.data_loaded_at:
                    import time
                    st.session_state.data_loaded_at = time.time()
                st.success(f"✅ Loaded {len(raw_df):,} rows")
                
                # Verify data is set (should trigger Step 2 after rerun)
                if st.session_state.data is not None and st.session_state.normalized_data is not None:
                    # Show prominent "Step 2 Ready" banner
                    st.markdown("""
                    <div style='margin-top: 2rem; padding: 1.5rem; background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%); border: 3px solid #22c55e; border-radius: 12px; box-shadow: 0 4px 12px rgba(34,197,94,0.3);'>
                        <div style='display: flex; align-items: center; gap: 1rem;'>
                            <div style='font-size: 3rem;'>✅</div>
                            <div style='flex: 1;'>
                                <h3 style='color: #15803d; margin: 0 0 0.5rem 0; font-size: 1.5rem; font-weight: 700;'>
                                    Step 1 Complete! Ready for Step 2
                                </h3>
                                <p style='color: #16a34a; margin: 0; font-size: 1.1rem; font-weight: 500;'>
                                    Scroll down to <strong>Step 2: Query Your Data</strong> to search your data using natural language, drug watchlist, or advanced filters.
                                </p>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("⚠️ Data loaded but normalization failed. Step 2 may not appear.")

                # Dataset snapshot KPIs
                try:
                    drugs = (
                        normalized["drug_name"].nunique() if "drug_name" in normalized.columns else 0
                    )
                    reactions = (
                        normalized["reaction"].nunique() if "reaction" in normalized.columns else 0
                    )

                    dates = None
                    if "onset_date" in normalized.columns:
                        dates = pd.to_datetime(normalized["onset_date"], errors="coerce")
                    elif "report_date" in normalized.columns:
                        dates = pd.to_datetime(normalized["report_date"], errors="coerce")

                    if dates is not None:
                        dates = dates.dropna()
                        min_date = dates.min()
                        max_date = dates.max()
                    else:
                        min_date = max_date = None

                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.markdown(
                            f"<p class='kpi-value'>{len(raw_df):,}</p>"
                            "<p class='kpi-label'>Rows loaded</p>",
                            unsafe_allow_html=True,
                        )
                    with c2:
                        st.markdown(
                            f"<p class='kpi-value'>{drugs:,}</p>"
                            "<p class='kpi-label'>Distinct drugs</p>",
                            unsafe_allow_html=True,
                        )
                    with c3:
                        st.markdown(
                            f"<p class='kpi-value'>{reactions:,}</p>"
                            "<p class='kpi-label'>Distinct reactions</p>",
                            unsafe_allow_html=True,
                        )

                    if min_date and max_date:
                        st.caption(
                            f"Detected date range: **{min_date.date().isoformat()} – {max_date.date().isoformat()}**"
                        )
                except Exception:
                    pass

                # Data quality snapshot
                quality = signal_stats.get_data_quality_metrics(normalized)
                st.markdown("<div class='block-card'>", unsafe_allow_html=True)
                st.markdown("#### 🧪 Data quality snapshot")
                
                # Quality score with color indicator
                quality_score = quality.get('quality_score', 0)
                quality_color = quality.get('quality_color', 'red')
                quality_label = quality.get('quality_label', 'Poor')
                
                # Color mapping for HTML
                color_map = {
                    'green': '#22c55e',
                    'yellow': '#eab308',
                    'orange': '#f97316',
                    'red': '#ef4444',
                }
                score_color = color_map.get(quality_color, '#64748b')
                
                st.markdown(
                    f"""
                    <div style="margin-bottom: 1rem; padding: 0.75rem; background: rgba(15,23,42,0.03); border-radius: 8px; border-left: 4px solid {score_color};">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <div style="font-size: 0.85rem; color: #64748b; margin-bottom: 0.25rem;">Overall Quality Score</div>
                                <div style="font-size: 1.5rem; font-weight: 600; color: {score_color};">
                                    {quality_score:.1f}/100
                                </div>
                            </div>
                            <div style="text-align: right;">
                                <div style="font-size: 0.9rem; font-weight: 500; color: {score_color};">
                                    {quality_label}
                                </div>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                
                q1, q2 = st.columns(2)
                with q1:
                    st.metric("Rows", f"{quality['row_count']:,}")
                    st.metric("Columns", quality["column_count"])
                with q2:
                    st.metric("Duplicate case IDs", f"{quality['duplicate_cases']:,}")
                if quality["missing_percent"]:
                    st.caption("Missing values across key fields:")
                    for field, pct in quality["missing_percent"].items():
                        st.caption(f"- {field}: {pct:.1f}%")
                st.markdown("</div>", unsafe_allow_html=True)

                # FAERS / dataset import summary
                st.markdown("<div class='block-card'>", unsafe_allow_html=True)
                st.markdown("#### 📊 Dataset summary")
                s1, s2, s3 = st.columns(3)
                with s1:
                    st.metric("Total rows loaded", f"{len(raw_df):,}")
                    if "case_id" in normalized.columns:
                        st.metric("Distinct cases", f"{normalized['case_id'].nunique():,}")
                with s2:
                    drugs = (
                        normalized["drug_name"].nunique()
                        if "drug_name" in normalized.columns
                        else 0
                    )
                    reactions = (
                        normalized["reaction"].nunique()
                        if "reaction" in normalized.columns
                        else 0
                    )
                    st.metric("Distinct drugs", f"{drugs:,}")
                    st.metric("Distinct reactions", f"{reactions:,}")
                with s3:
                    # Date range if available
                    date_cols = ["onset_date", "event_date", "report_date", "receive_date"]
                    date_col = next(
                        (c for c in date_cols if c in normalized.columns), None
                    )
                    if date_col:
                        dates = pd.to_datetime(
                            normalized[date_col], errors="coerce"
                        ).dropna()
                        if not dates.empty:
                            min_date = dates.min().date().isoformat()
                            max_date = dates.max().date().isoformat()
                            st.metric("Date range", f"{min_date} → {max_date}")
                    # Simple FAERS detection heuristic
                    looks_like_faers = (
                        "case_id" in normalized.columns
                        and "drug_name" in normalized.columns
                        and "reaction" in normalized.columns
                    )
                    # Data quality tools section
                    if len(normalized) > 0:
                        st.markdown("---")
                        st.markdown("**🔧 Data Quality Tools**")
                        
                        # Check for multiple sources
                        has_multiple_sources = 'source' in normalized.columns and normalized['source'].nunique() > 1
                        
                        tool_cols = st.columns(2)
                        
                        with tool_cols[0]:
                            if "drug_name" in normalized.columns:
                                if st.button("✨ Normalize Drug Names", key="normalize_drugs_btn", use_container_width=True):
                                    try:
                                        from src.drug_name_normalization import normalize_drug_column, group_similar_drugs
                                        
                                        with st.spinner("Normalizing drug names..."):
                                            # Normalize drug names
                                            normalized_normalized = normalize_drug_column(normalized.copy(), drug_column='drug_name')
                                            
                                            # Group similar drugs
                                            normalized_grouped = group_similar_drugs(normalized_normalized, drug_column='drug_name', threshold=0.85)
                                            
                                            # Update session state
                                            st.session_state.normalized_data = normalized_grouped
                                            st.session_state.data = normalized_grouped
                                            
                                            # Show results
                                            original_unique = normalized['drug_name'].nunique()
                                            new_unique = normalized_grouped['drug_name_normalized'].nunique() if 'drug_name_normalized' in normalized_grouped.columns else normalized_grouped['drug_name'].nunique()
                                            
                                            st.success(f"✅ Drug names normalized! Reduced from {original_unique} to {new_unique} unique drug names.")
                                            st.info("💡 Similar drug names have been grouped together (e.g., 'TYLENOL' → 'Acetaminophen', 'aspirin HCL' → 'Aspirin')")
                                            st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Error normalizing drug names: {str(e)}")
                        
                        with tool_cols[1]:
                            if has_multiple_sources:
                                if st.button("🔍 Detect Cross-Source Duplicates", key="dedup_btn", use_container_width=True):
                                    try:
                                        from src.cross_source_deduplication import detect_cross_source_duplicates, get_deduplication_report
                                        
                                        with st.spinner("Detecting duplicates across sources..."):
                                            # Detect duplicates
                                            dedup_result = detect_cross_source_duplicates(
                                                normalized,
                                                source_column='source',
                                                method='hybrid',
                                                similarity_threshold=0.85,
                                                use_ml=True,
                                                use_quantum=True
                                            )
                                            
                                            # Generate report
                                            report = get_deduplication_report(
                                                normalized,
                                                dedup_result.get('duplicate_groups', []),
                                                source_column='source'
                                            )
                                            
                                            # Display results
                                            st.success(f"✅ Duplicate detection complete!")
                                            st.markdown("**📊 Deduplication Results:**")
                                            
                                            col1, col2, col3 = st.columns(3)
                                            with col1:
                                                st.metric("Total Cases", f"{dedup_result['total_cases']:,}")
                                            with col2:
                                                st.metric("Unique Cases", f"{dedup_result['unique_cases']:,}")
                                            with col3:
                                                st.metric("Duplicates", f"{dedup_result['duplicate_cases']:,}")
                                            
                                            if dedup_result['cross_source_duplicates'] > 0:
                                                st.info(f"🔗 Found {dedup_result['cross_source_duplicates']} duplicate groups spanning multiple sources")
                                            
                                            # Show breakdown
                                            if report.get('source_breakdown'):
                                                st.markdown("**Source Breakdown:**")
                                                for source, count in report['source_breakdown'].items():
                                                    st.caption(f"- {source}: {count} duplicate groups")
                                            
                                            # Store in session state for potential removal
                                            st.session_state.dedup_result = dedup_result
                                            st.session_state.dedup_report = report
                                            
                                            # Offer to remove duplicates
                                            if dedup_result['duplicate_cases'] > 0:
                                                st.markdown("---")
                                                if st.button("🗑️ Remove Duplicates", key="remove_dups_btn"):
                                                    from src.cross_source_deduplication import remove_duplicates
                                                    
                                                    with st.spinner("Removing duplicates..."):
                                                        cleaned_df = remove_duplicates(
                                                            normalized,
                                                            dedup_result.get('duplicate_groups', []),
                                                            keep_strategy='first'
                                                        )
                                                        
                                                        # Update session state
                                                        st.session_state.normalized_data = cleaned_df
                                                        st.session_state.data = cleaned_df
                                                        
                                                        st.success(f"✅ Removed {dedup_result['duplicate_cases']} duplicate cases. Dataset now has {len(cleaned_df):,} rows.")
                                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Error detecting duplicates: {str(e)}")
                                        import traceback
                                        st.code(traceback.format_exc())
                            else:
                                st.caption("💡 Upload data from multiple sources (FAERS, E2B, etc.) to enable cross-source deduplication")
                    
                    st.caption(
                        "Source: FAERS‑style PV table detected"
                        if looks_like_faers
                        else "Source: generic PV dataset (schema mapped)"
                    )

                # Per-file FAERS summary (if available)
                faers_summary = faers_loader.get_faers_file_summary()
                if faers_summary:
                    st.markdown("---")
                    st.caption("FAERS components detected in this load:")
                    summary_rows = []
                    for fname, meta in faers_summary.items():
                        summary_rows.append(
                            {
                                "File": fname,
                                "Type": meta.get("file_type", ""),
                                "Rows": meta.get("rows"),
                                "Approx. skipped lines": meta.get("approx_skipped_lines"),
                            }
                        )
                    if summary_rows:
                        # Local import to avoid circular dependencies in some environments
                        import pandas as _pd  # type: ignore
                        faers_df = _pd.DataFrame(summary_rows)
                        st.dataframe(
                            faers_df,
                            use_container_width=True,
                            hide_index=True,
                        )
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Loading completed successfully - prepare for rerun
                st.session_state.show_results = False
                st.session_state.loading_in_progress = False
                st.rerun()
        except Exception as e:
            # Loading failed - ensure flag is cleared and show error
            st.session_state.loading_in_progress = False
            progress_bar.progress(1.0)
            status_container.markdown(f"**❌ Error during processing**")
            bytes_container.markdown(f"**Error: {str(e)[:100]}...**")
            files_container.empty()
            st.error(f"❌ Error during file processing: {str(e)}")
            # Don't raise - let the UI show the error message
        finally:
            # Always clear loading flag, even on error
            st.session_state.loading_in_progress = False

    elif not uploaded_files:
        st.info("Upload at least one file to get started.")
    st.markdown("</div>", unsafe_allow_html=True)

    warnings = faers_loader.get_loader_warnings()
    if warnings:
        st.markdown("<div class='block-card'>", unsafe_allow_html=True)
        st.markdown("#### ⚠️ Import diagnostics")
        st.caption("Recent loader messages:")
        for msg in warnings[-5:]:
            st.markdown(f"- {msg}")
        st.markdown("</div>", unsafe_allow_html=True)
        faers_loader.clear_loader_warnings()

