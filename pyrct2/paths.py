"""OS-specific path resolution for OpenRCT2 directories."""

import json
import os
import platform
import shutil
import subprocess
from pathlib import Path

CONFIG_DIR = Path.home() / ".pyrct2"
CONFIG_FILE = CONFIG_DIR / "config.json"


def get_plugin_dir() -> Path:
    """Return the OpenRCT2 plugin directory for the current OS."""
    system = platform.system()

    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "OpenRCT2" / "plugin"
    elif system == "Windows":
        import ctypes.wintypes

        buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buf)  # 5 = CSIDL_PERSONAL (Documents)
        return Path(buf.value) / "OpenRCT2" / "plugin"
    elif system == "Linux":
        config_home = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
        return Path(config_home) / "OpenRCT2" / "plugin"
    else:
        raise RuntimeError(f"Unsupported platform: {system}")


def find_openrct2_binary() -> Path | None:
    """Search for the OpenRCT2 binary on this system.

    Search order:
    1. PYRCT2_OPENRCT2_PATH environment variable
    2. OS-specific discovery (Spotlight on macOS, known dirs on Windows)
    3. shutil.which() fallback (covers PATH installs on all platforms)
    """
    # Environment variable override
    env_path = os.environ.get("PYRCT2_OPENRCT2_PATH")
    if env_path:
        p = Path(env_path)
        if p.exists():
            return p

    system = platform.system()

    if system == "Darwin":
        found = _find_macos()
        if found:
            return found
    elif system == "Windows":
        found = _find_windows()
        if found:
            return found

    # Fallback: check PATH (works on all platforms including Linux)
    on_path = shutil.which("openrct2")
    if on_path:
        return Path(on_path)

    return None


def _find_macos() -> Path | None:
    """Use Spotlight to find OpenRCT2.app on macOS."""
    try:
        result = subprocess.run(
            ["mdfind", "kMDItemFSName == 'OpenRCT2.app'"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        for line in result.stdout.strip().splitlines():
            binary = Path(line) / "Contents" / "MacOS" / "OpenRCT2"
            if binary.exists():
                return binary
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def _find_windows() -> Path | None:
    """Check known installation directories on Windows."""
    program_files = Path(os.environ.get("PROGRAMFILES", "C:/Program Files"))
    program_files_x86 = Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)"))
    binary = "openrct2.com"

    candidates = [
        program_files / "OpenRCT2" / binary,
        program_files_x86 / "OpenRCT2" / binary,
        program_files_x86 / "GOG Galaxy" / "Games" / "RollerCoaster Tycoon 2 Triple Thrill Pack" / "OpenRCT2" / binary,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def validate_openrct2_binary(path: Path) -> str:
    """Verify the binary is a real OpenRCT2 install. Returns the version string."""
    try:
        result = subprocess.run(
            [str(path), "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        first_line = result.stdout.strip().splitlines()[0]
        if not first_line.startswith("OpenRCT2"):
            raise RuntimeError(f"Not an OpenRCT2 binary: {path}")
        return first_line
    except (subprocess.TimeoutExpired, FileNotFoundError, IndexError) as e:
        raise RuntimeError(f"Failed to validate OpenRCT2 binary at {path}: {e}")


def load_config() -> dict:
    """Load pyrct2 config from ~/.pyrct2/config.json."""
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}


def save_config(data: dict) -> None:
    """Save pyrct2 config to ~/.pyrct2/config.json."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(data, indent=2) + "\n")
