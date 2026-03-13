"""Launch OpenRCT2 in headless mode and wait for plugin readiness."""

import atexit
import socket
import subprocess
import time
from pathlib import Path

from pyrct2.connection import Connection, DEFAULT_HOST, DEFAULT_PORT
from pyrct2.paths import load_config

HEALTH_POLL_INTERVAL = 0.5
LAUNCH_TIMEOUT = 30.0


class GameInstance:
    """A running OpenRCT2 process with an active bridge connection."""

    def __init__(self, process: subprocess.Popen, connection: Connection):
        self._process = process
        self.connection = connection
        atexit.register(self._cleanup)

    def check_alive(self) -> None:
        """Raise if the OpenRCT2 process has exited."""
        _check_process(self._process)

    def stop(self) -> None:
        """Terminate the game process and close the connection."""
        self.connection.close()
        self._process.terminate()
        self._process.wait(timeout=5)
        atexit.unregister(self._cleanup)

    def _cleanup(self) -> None:
        """Safety net called on interpreter shutdown."""
        try:
            self._process.terminate()
            self._process.wait(timeout=5)
        except (OSError, subprocess.TimeoutExpired):
            # Process may already be dead — nothing to do at shutdown
            pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.stop()


def launch(park_file: str | Path, port: int = DEFAULT_PORT) -> GameInstance:
    """Launch OpenRCT2 headless and return a connected GameInstance.

    Blocks until the bridge plugin is ready (up to 30s).
    """
    park_path = Path(park_file)
    if not park_path.exists():
        raise FileNotFoundError(f"Park file not found: {park_path}")

    config = load_config()
    binary = config.get("openrct2_path")
    if not binary:
        raise RuntimeError("OpenRCT2 not configured. Run `pyrct2 setup` first.")

    if _port_in_use(port):
        raise RuntimeError(f"Port {port} already in use. Is OpenRCT2 already running?")

    process = subprocess.Popen(
        [binary, "host", str(park_path), "--headless"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    connection = _wait_for_bridge(port, process)
    return GameInstance(process, connection)


def _check_process(process: subprocess.Popen) -> None:
    """Raise if the process has exited."""
    if process.poll() is not None:
        raise RuntimeError(f"OpenRCT2 exited unexpectedly (exit code {process.returncode})")


def _port_in_use(port: int, host: str = DEFAULT_HOST) -> bool:
    """Check if something is already listening on the given port."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    try:
        s.connect((host, port))
        s.close()
        return True
    except (ConnectionRefusedError, socket.timeout):
        return False


def _wait_for_bridge(port: int, process: subprocess.Popen) -> Connection:
    """Poll the health endpoint until the bridge responds or timeout."""
    deadline = time.monotonic() + LAUNCH_TIMEOUT

    while time.monotonic() < deadline:
        _check_process(process)

        try:
            conn = Connection(port=port, timeout=5)
            result = conn.send("health")
            if result.get("success"):
                return conn
            conn.close()
        except (ConnectionRefusedError, socket.timeout, OSError):
            # Bridge not ready yet — retry after interval
            pass

        time.sleep(HEALTH_POLL_INTERVAL)

    process.terminate()
    raise TimeoutError(f"Bridge did not respond within {LAUNCH_TIMEOUT}s")
