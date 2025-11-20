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
from src.app_helpers import cached_detect_and_normalize, load_all_files


def render_upload_section():
    """Render file upload UI and handle loading."""
    st.markdown(
        """
        <div class="session-chip-row" style="margin-bottom: 16px !important;">
            <div class="session-chip">🗂 Session-based, no login</div>
            <div class="session-chip">📄 Works with FAERS / CSV / Excel / PDF exports</div>
            <div class="session-chip">⚛️ Quantum-inspired ranking (demo)</div>
        </div>
        <div class='block-card' style="margin-top: 0 !important;">
            <h3>📤 1️⃣ Upload safety dataset</h3>
        """,
        unsafe_allow_html=True,
    )

    uploaded_files = st.file_uploader(
        "Drop FAERS ASCII, Argus/Veeva exports, CSV, Excel, text, ZIP or PDF",
        type=["csv", "xlsx", "xls", "txt", "zip", "pdf"],
        accept_multiple_files=True,
        help=(
            "You can upload multiple files. FAERS ASCII (DEMO/DRUG/REAC/OUTC…), "
            "Argus/Veeva exports, or ad-hoc CSV/Excel are supported. "
            "⚠️ Note: XML format is NOT supported - use FAERS ASCII (.txt) files instead. "
            "Large files (>200MB) are supported."
        ),
    )
    
    # Add upload progress tracking JavaScript
    # This will inject a progress display right after the file uploader
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

    # Show upload status and file info if files are uploaded
    if uploaded_files:
        total_size = sum(f.size for f in uploaded_files)
        size_mb = total_size / (1024 * 1024)
        total_files = len(uploaded_files)
        
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

    load_clicked = st.button("🔄 Load & map data", disabled=not uploaded_files)

    if load_clicked and uploaded_files:
        # Calculate total size for progress tracking
        total_size_bytes = sum(f.size for f in uploaded_files)
        total_size_mb = total_size_bytes / (1024 * 1024)
        total_files = len(uploaded_files)
        
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
        
        # Define progress callback with file size tracking
        def update_progress(current_file_num, total_file_num, file_name, file_size_bytes=None):
            # Calculate file progress
            file_progress = current_file_num / total_file_num
            
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
        
        try:
            raw_df = load_all_files(uploaded_files, progress_callback=update_progress)
            
            # Show completion with prominent styling
            progress_bar.progress(1.0)
            status_container.markdown(
                "<div style='font-size: 1.2rem; font-weight: 700; color: #16a34a; margin: 0.5rem 0;'>"
                "✅ All files processed successfully!</div>",
                unsafe_allow_html=True
            )
            bytes_container.markdown(
                f"<div style='font-size: 1.2rem; font-weight: 700; color: #2563eb; margin: 0.5rem 0;'>"
                f"📊 Total: <strong>{total_size_mb:.1f} MB</strong> processed</div>",
                unsafe_allow_html=True
            )
            files_container.markdown(
                f"<div style='font-size: 1rem; color: #475569; margin: 0.5rem 0;'>"
                f"📁 All <strong>{total_files}</strong> files loaded</div>",
                unsafe_allow_html=True
            )
        except Exception as e:
            # Show error with progress
            progress_bar.progress(1.0)
            status_container.markdown(f"**❌ Error during processing**")
            bytes_container.markdown(f"**Error: {str(e)[:100]}...**")
            files_container.empty()
            st.error(f"❌ Error during file processing: {str(e)}")
            raw_df = None
            if raw_df is None or raw_df.empty:
                st.error("❌ Could not read any rows from the provided files. Please verify formats.")
                
                # Check if XML was detected
                xml_detected = any("xml" in f.name.lower() for f in uploaded_files)
                
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
                    analytics.log_event("upload_failed", {"file_count": len(uploaded_files)})
            else:
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

                # Use cached detection and normalization
                mapping, normalized = cached_detect_and_normalize(raw_df)
                st.session_state.schema_mapping = mapping

                essential = ["drug_name", "reaction", "case_id"]
                found = [f for f in essential if f in mapping]
                if len(found) == 0:
                    st.error(
                        "Critical: could not detect any essential PV fields "
                        "(drug_name, reaction, case_id). Check column names or input format."
                    )
                elif len(found) < 2:
                    st.warning(
                        "Only detected "
                        f"{len(found)} essential field(s): {', '.join(found)}. "
                        "Some analysis features may be limited."
                    )
                st.session_state.normalized_data = normalized
                st.success(f"✅ Loaded {len(raw_df):,} rows")

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

                quality = signal_stats.get_data_quality_metrics(normalized)
                st.markdown("<div class='block-card'>", unsafe_allow_html=True)
                st.markdown("#### 🧪 Data quality snapshot")
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

                if mapping:
                    with st.expander("Detected schema mapping", expanded=False):
                        st.dataframe(
                            pv_schema.get_schema_summary(mapping),
                            use_container_width=True,
                            hide_index=True,
                        )
                st.session_state.show_results = False
                st.rerun()

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

