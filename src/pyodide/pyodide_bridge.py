"""
Pyodide Bridge (CHUNK 7.6.2)
Frontend loader for Pyodide Worker integration with Streamlit.
Provides Python interface to JavaScript Web Worker running Pyodide.
"""
import streamlit as st
import base64
import json
import uuid
from typing import Dict, Any, Optional, Callable
from pathlib import Path


def init_pyodide_worker() -> str:
    """
    Initialize Pyodide worker and return encoded JavaScript code.
    
    Returns:
        Base64-encoded JavaScript worker code
    """
    if "pyodide_worker_encoded" not in st.session_state:
        # Path to worker JavaScript file
        worker_path = Path(__file__).parent / "pyodide_worker.js"
        
        try:
            if worker_path.exists():
                worker_js = worker_path.read_text(encoding="utf-8")
                # Encode JS so Streamlit can inject it into browser
                encoded = base64.b64encode(worker_js.encode("utf-8")).decode("utf-8")
                st.session_state.pyodide_worker_encoded = encoded
            else:
                # Fallback: return empty string if file doesn't exist
                st.session_state.pyodide_worker_encoded = ""
        except Exception as e:
            st.warning(f"Could not load Pyodide worker: {e}")
            st.session_state.pyodide_worker_encoded = ""
    
    return st.session_state.pyodide_worker_encoded


def inject_pyodide_worker_script():
    """
    Inject Pyodide worker initialization script into Streamlit page.
    This creates the Web Worker in the browser.
    """
    encoded_worker = init_pyodide_worker()
    
    if not encoded_worker:
        return
    
    # Create callback function name
    callback_name = "streamlitPyodideCallback"
    
    # Inject worker initialization script
    script = f"""
<script>
(function() {{
    if (window.localSummaryWorker) {{
        return; // Worker already initialized
    }}
    
    try {{
        // Decode and create worker from blob
        const workerCode = atob("{encoded_worker}");
        const blob = new Blob([workerCode], {{ type: "application/javascript" }});
        const url = URL.createObjectURL(blob);
        
        window.localSummaryWorker = new Worker(url);
        
        // Message handler for worker responses
        window.localSummaryWorker.onmessage = function(e) {{
            const data = e.data;
            
            // Store result in Streamlit session state via custom event
            const event = new CustomEvent("pyodideResult", {{
                detail: JSON.stringify(data)
            }});
            
            window.parent.document.dispatchEvent(event);
            
            // Also call callback if defined
            if (window.{callback_name}) {{
                window.{callback_name}(data);
            }}
        }};
        
        // Error handler
        window.localSummaryWorker.onerror = function(error) {{
            console.error("Pyodide Worker Error:", error);
            const event = new CustomEvent("pyodideError", {{
                detail: JSON.stringify({{
                    type: "error",
                    message: error.message || "Unknown worker error"
                }})
            }});
            window.parent.document.dispatchEvent(event);
        }};
        
        console.log("Pyodide Worker initialized successfully");
    }} catch (error) {{
        console.error("Failed to initialize Pyodide Worker:", error);
    }}
}})();
</script>
"""
    
    st.markdown(script, unsafe_allow_html=True)


def run_local_summary(csv_data: str) -> Optional[Dict[str, Any]]:
    """
    Run local summary engine via Pyodide worker.
    
    Args:
        csv_data: CSV data as string
        
    Returns:
        Summary dictionary or None if error
    """
    if "pyodide_worker_initialized" not in st.session_state:
        st.session_state.pyodide_worker_initialized = False
    
    # Generate task ID
    task_id = str(uuid.uuid4())
    
    # Create command message
    command = {
        "command": "run_local_summary",
        "payload": {
            "csv": csv_data
        },
        "taskId": task_id
    }
    
    # Send command to worker via JavaScript
    script = f"""
<script>
if (window.localSummaryWorker) {{
    window.localSummaryWorker.postMessage({json.dumps(command)});
    
    // Store task ID for result tracking
    window.currentPyodideTask = "{task_id}";
}} else {{
    console.error("Pyodide Worker not initialized");
}}
</script>
"""
    
    st.markdown(script, unsafe_allow_html=True)
    
    # Store task in session state
    if "pyodide_tasks" not in st.session_state:
        st.session_state.pyodide_tasks = {}
    
    st.session_state.pyodide_tasks[task_id] = {
        "status": "pending",
        "command": "run_local_summary"
    }
    
    return None  # Result will be available via event listener


def wait_for_pyodide_result(task_id: str, timeout: float = 10.0) -> Optional[Dict[str, Any]]:
    """
    Wait for Pyodide worker result (non-blocking check).
    
    Args:
        task_id: Task ID to check
        timeout: Maximum time to wait in seconds
        
    Returns:
        Result dictionary if available, None otherwise
    """
    if "pyodide_results" not in st.session_state:
        st.session_state.pyodide_results = {}
    
    # Check if result is available
    if task_id in st.session_state.pyodide_results:
        result = st.session_state.pyodide_results.pop(task_id)
        return result
    
    return None


def register_pyodide_result_listener():
    """
    Register JavaScript event listener to capture Pyodide worker results.
    This should be called on page initialization.
    """
    script = """
<script>
window.parent.document.addEventListener("pyodideResult", function(event) {
    try {
        const data = JSON.parse(event.detail);
        
        // Send result to Streamlit backend
        fetch("/_stcore/Event", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                name: "pyodide_result",
                json_args: data
            })
        });
    } catch (error) {
        console.error("Error handling Pyodide result:", error);
    }
});
</script>
"""
    
    st.markdown(script, unsafe_allow_html=True)


def handle_pyodide_result_event(payload: Dict[str, Any]):
    """
    Handle Pyodide result event from JavaScript.
    
    Args:
        payload: Result payload from worker
    """
    task_id = payload.get("taskId")
    
    if not task_id:
        return
    
    # Store result in session state
    if "pyodide_results" not in st.session_state:
        st.session_state.pyodide_results = {}
    
    if payload.get("type") == "result":
        st.session_state.pyodide_results[task_id] = payload.get("result")
    elif payload.get("type") == "error":
        st.session_state.pyodide_results[task_id] = {
            "error": True,
            "message": payload.get("message", "Unknown error")
        }
    elif payload.get("type") == "status":
        # Update status
        if "pyodide_status" not in st.session_state:
            st.session_state.pyodide_status = {}
        st.session_state.pyodide_status[task_id] = payload.get("message", "")

