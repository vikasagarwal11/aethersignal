"""
Version Information - AetherSignal version tracking
"""

APP_VERSION = "v1.0.0"
RELEASE_DATE = "2025-12-01"
BUILD_DATE = "2025-12-01"

# Version components
VERSION_MAJOR = 1
VERSION_MINOR = 0
VERSION_PATCH = 0

# Version string
VERSION_STRING = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}"

# Release info
RELEASE_INFO = {
    "version": APP_VERSION,
    "version_string": VERSION_STRING,
    "release_date": RELEASE_DATE,
    "build_date": BUILD_DATE,
    "major": VERSION_MAJOR,
    "minor": VERSION_MINOR,
    "patch": VERSION_PATCH
}


def get_version() -> str:
    """Get version string."""
    return VERSION_STRING


def get_version_info() -> dict:
    """Get full version information."""
    return RELEASE_INFO.copy()

