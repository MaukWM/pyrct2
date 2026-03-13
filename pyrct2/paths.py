"""OS-specific path resolution for OpenRCT2 directories."""

import platform
from pathlib import Path


def get_plugin_dir() -> Path:
    """Return the OpenRCT2 plugin directory for the current OS."""
    system = platform.system()

    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "OpenRCT2" / "plugin"
    elif system == "Windows":
        # Windows stores OpenRCT2 data under Documents, not AppData
        import ctypes.wintypes
        buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buf)  # 5 = CSIDL_PERSONAL (Documents)
        return Path(buf.value) / "OpenRCT2" / "plugin"
    elif system == "Linux":
        import os
        config_home = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
        return Path(config_home) / "OpenRCT2" / "plugin"
    else:
        raise RuntimeError(f"Unsupported platform: {system}")
