"""
Browser Capability Detector (CHUNK H1.3)
Detects browser hardware capability (RAM, CPU, WASM support, device class) for hybrid mode selection.
Runs client-side JavaScript and returns structured capability information.
"""
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
import json

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False


@dataclass
class BrowserCapabilities:
    """
    Structured browser and hardware capability information.
    """
    is_mobile: bool
    ram_gb: Optional[float]
    cpu_cores: Optional[int]
    device_class: str  # "low", "medium", "high"
    wasm_supported: bool
    simd_supported: bool
    webgl_supported: bool
    webgpu_supported: bool
    user_agent: str
    capability_score: float  # 0.0-1.0 for Hybrid Mode Manager
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class BrowserCapabilityDetector:
    """
    Detects browser hardware capability using client-side JavaScript.
    
    Provides capability information used by Hybrid Mode Manager to determine
    whether local compute, Pyodide, FAERS parsing, or trend detection can run safely.
    """
    
    def __init__(self):
        """Initialize Browser Capability Detector."""
        self._capabilities: Optional[BrowserCapabilities] = None
    
    def run_detection(self, force_refresh: bool = False) -> Optional[BrowserCapabilities]:
        """
        Run browser capability detection.
        
        This injects JavaScript into the page to detect:
        - RAM (navigator.deviceMemory)
        - CPU cores (navigator.hardwareConcurrency)
        - WASM support
        - SIMD support
        - WebGL support
        - WebGPU support
        - Mobile detection
        - User agent
        
        Args:
            force_refresh: Force re-detection even if cached
            
        Returns:
            BrowserCapabilities object or None if detection failed
        """
        # Check cache first
        if not force_refresh and self._capabilities:
            return self._capabilities
        
        if STREAMLIT_AVAILABLE:
            # Check session state cache
            if "browser_capabilities" in st.session_state and not force_refresh:
                cached = st.session_state.browser_capabilities
                if cached and isinstance(cached, dict):
                    return self._create_capabilities_from_dict(cached)
        
        # Generate JavaScript detection code
        js_code = self._generate_detection_js()
        
        if STREAMLIT_AVAILABLE:
            # Inject JavaScript (will run in browser)
            st.components.v1.html(js_code, height=0)
            
            # Check if capabilities were detected and stored
            if "browser_capabilities" in st.session_state:
                browser_info = st.session_state.browser_capabilities
                if browser_info and isinstance(browser_info, dict):
                    capabilities = self._create_capabilities_from_dict(browser_info)
                    self._capabilities = capabilities
                    return capabilities
        
        # Fallback: return conservative defaults
        return self._get_default_capabilities()
    
    def _generate_detection_js(self) -> str:
        """Generate JavaScript code for browser capability detection."""
        return """
        <script>
            (async function() {
                const capabilities = {};
                
                // RAM (approximate, if available)
                capabilities.ram_gb = navigator.deviceMemory || null;
                
                // CPU cores
                capabilities.cpu_cores = navigator.hardwareConcurrency || null;
                
                // WASM support
                try {
                    capabilities.wasm_supported = (typeof WebAssembly === "object");
                } catch (e) {
                    capabilities.wasm_supported = false;
                }
                
                // SIMD support (basic check)
                capabilities.simd_supported = false;
                try {
                    if (typeof WebAssembly !== "undefined") {
                        // Simple WASM validation as proxy for SIMD support
                        const wasmModule = new Uint8Array([0, 97, 115, 109, 1, 0, 0, 0]);
                        if (WebAssembly.validate) {
                            capabilities.simd_supported = WebAssembly.validate(wasmModule);
                        }
                    }
                } catch (e) {
                    capabilities.simd_supported = false;
                }
                
                // WebGL support
                try {
                    const canvas = document.createElement('canvas');
                    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                    capabilities.webgl_supported = !!gl;
                } catch (e) {
                    capabilities.webgl_supported = false;
                }
                
                // WebGPU support
                try {
                    capabilities.webgpu_supported = typeof navigator.gpu !== "undefined";
                } catch (e) {
                    capabilities.webgpu_supported = false;
                }
                
                // Mobile detection
                const ua = navigator.userAgent.toLowerCase();
                capabilities.is_mobile = /iphone|android|ipad|mobile|tablet/.test(ua);
                
                // User agent
                capabilities.user_agent = navigator.userAgent;
                
                // Send to Streamlit via custom event
                try {
                    const event = new CustomEvent("streamlit:browser_info", {
                        detail: JSON.stringify(capabilities)
                    });
                    window.parent.postMessage({
                        type: "streamlit:browser_info",
                        data: capabilities
                    }, "*");
                } catch (e) {
                    console.log("Could not send browser info:", e);
                }
            })();
        </script>
        """
    
    def _create_capabilities_from_dict(self, browser_info: Dict[str, Any]) -> BrowserCapabilities:
        """Create BrowserCapabilities from dictionary."""
        ram_gb = browser_info.get("ram_gb")
        cpu_cores = browser_info.get("cpu_cores")
        
        device_class = self._classify_device(ram_gb, cpu_cores)
        capability_score = self._calculate_capability_score(
            ram_gb=ram_gb,
            cpu_cores=cpu_cores,
            wasm_supported=browser_info.get("wasm_supported", False),
            simd_supported=browser_info.get("simd_supported", False),
            is_mobile=browser_info.get("is_mobile", False),
            device_class=device_class
        )
        
        return BrowserCapabilities(
            is_mobile=browser_info.get("is_mobile", False),
            ram_gb=ram_gb,
            cpu_cores=cpu_cores,
            device_class=device_class,
            wasm_supported=browser_info.get("wasm_supported", False),
            simd_supported=browser_info.get("simd_supported", False),
            webgl_supported=browser_info.get("webgl_supported", False),
            webgpu_supported=browser_info.get("webgpu_supported", False),
            user_agent=browser_info.get("user_agent", "Unknown"),
            capability_score=capability_score
        )
    
    def _classify_device(self, ram_gb: Optional[float], cpu_cores: Optional[int]) -> str:
        """
        Classify device performance class.
        
        Args:
            ram_gb: RAM in GB (if available)
            cpu_cores: CPU core count (if available)
            
        Returns:
            "low", "medium", or "high"
        """
        if not ram_gb or not cpu_cores:
            return "low"
        
        # High: 8+ GB RAM and 8+ cores
        if ram_gb >= 8 and cpu_cores >= 8:
            return "high"
        
        # Medium: 4+ GB RAM and 4+ cores
        if ram_gb >= 4 and cpu_cores >= 4:
            return "medium"
        
        # Low: everything else
        return "low"
    
    def _calculate_capability_score(
        self,
        ram_gb: Optional[float],
        cpu_cores: Optional[int],
        wasm_supported: bool,
        simd_supported: bool,
        is_mobile: bool,
        device_class: str
    ) -> float:
        """
        Calculate capability score (0.0-1.0) for Hybrid Mode Manager.
        
        Args:
            ram_gb: RAM in GB
            cpu_cores: CPU core count
            wasm_supported: WebAssembly support
            simd_supported: SIMD support
            is_mobile: Mobile device flag
            device_class: Device class ("low", "medium", "high")
            
        Returns:
            Capability score between 0.0 and 1.0
        """
        score = 0.0
        
        # RAM component (0-0.3)
        if ram_gb:
            if ram_gb >= 16:
                score += 0.3
            elif ram_gb >= 8:
                score += 0.25
            elif ram_gb >= 4:
                score += 0.15
            elif ram_gb >= 2:
                score += 0.1
            else:
                score += 0.05
        else:
            # Unknown RAM - assume conservative
            score += 0.1
        
        # CPU component (0-0.3)
        if cpu_cores:
            if cpu_cores >= 12:
                score += 0.3
            elif cpu_cores >= 8:
                score += 0.25
            elif cpu_cores >= 4:
                score += 0.15
            elif cpu_cores >= 2:
                score += 0.1
            else:
                score += 0.05
        else:
            # Unknown CPU - assume conservative
            score += 0.1
        
        # WASM support (0-0.2)
        if wasm_supported:
            score += 0.2
            # SIMD bonus
            if simd_supported:
                score += 0.05  # Bonus for SIMD
        else:
            # No WASM = very limited
            score *= 0.5  # Halve score if no WASM
        
        # Device class adjustment
        if device_class == "high":
            score = min(1.0, score * 1.1)  # 10% boost
        elif device_class == "low":
            score = score * 0.8  # 20% reduction
        
        # Mobile penalty
        if is_mobile:
            score = score * 0.7  # 30% reduction for mobile
        
        return min(1.0, max(0.0, score))
    
    def _get_default_capabilities(self) -> BrowserCapabilities:
        """
        Get conservative default capabilities when detection fails.
        
        Returns:
            Default BrowserCapabilities with low capability score
        """
        return BrowserCapabilities(
            is_mobile=False,
            ram_gb=None,
            cpu_cores=None,
            device_class="low",
            wasm_supported=False,
            simd_supported=False,
            webgl_supported=False,
            webgpu_supported=False,
            user_agent="Unknown",
            capability_score=0.3  # Conservative default
        )
    
    def get_capability_score(self) -> float:
        """
        Get capability score (0.0-1.0) for Hybrid Mode Manager.
        
        Returns:
            Capability score
        """
        capabilities = self.run_detection()
        if capabilities:
            return capabilities.capability_score
        return 0.3  # Conservative default


# Global singleton instance
_global_detector: Optional[BrowserCapabilityDetector] = None


def get_browser_capability_detector() -> BrowserCapabilityDetector:
    """
    Get or create the global Browser Capability Detector instance.
    
    Returns:
        BrowserCapabilityDetector singleton
    """
    global _global_detector
    
    if _global_detector is None:
        _global_detector = BrowserCapabilityDetector()
    
    return _global_detector


def detect_browser_capabilities(force_refresh: bool = False) -> Optional[BrowserCapabilities]:
    """
    Convenience function to detect browser capabilities.
    
    Args:
        force_refresh: Force re-detection
        
    Returns:
        BrowserCapabilities or None
    """
    detector = get_browser_capability_detector()
    return detector.run_detection(force_refresh=force_refresh)


def get_capability_score() -> float:
    """
    Get browser capability score (0.0-1.0).
    
    Returns:
        Capability score for Hybrid Mode Manager
    """
    detector = get_browser_capability_detector()
    return detector.get_capability_score()
