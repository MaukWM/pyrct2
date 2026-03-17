"""Launch OpenRCT2 and wait for plugin readiness."""

import atexit
import socket
import subprocess
import threading
import time
from pathlib import Path

from pyrct2.connection import Connection, DEFAULT_HOST, DEFAULT_PORT
from pyrct2.paths import load_config
from pyrct2.scenarios import SCENARIO_PACK, Scenario

HEALTH_POLL_INTERVAL = 0.5
LAUNCH_TIMEOUT = 30.0


class GameInstance:
    """A running OpenRCT2 process with an active bridge connection."""

    def __init__(self, process: subprocess.Popen, connection: Connection):
        self._process = process
        self.connection = connection
        self.logs: list[str] = []
        self._log_thread = threading.Thread(target=self._capture_logs, daemon=True)
        self._log_thread.start()
        atexit.register(self._cleanup)

    def _capture_logs(self) -> None:
        """Read stdout+stderr from the game process into self.logs."""
        for line in self._process.stdout:  # type: ignore[union-attr]
            self.logs.append(line.rstrip("\n"))

    def check_alive(self) -> None:
        """Raise if the OpenRCT2 process has exited."""
        _check_process(self._process)

    def stop(self) -> None:
        """Terminate the game process and close the connection."""
        self.connection.close()
        self._process.terminate()
        self._process.wait(timeout=5)
        self._log_thread.join(timeout=2)
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


def _resolve_scenario(scenario: Scenario) -> Path:
    """Resolve a Scenario enum to a full path using the configured rct2_path."""
    rct2_path = load_config()["rct2_path"]
    park_path = Path(rct2_path) / "Scenarios" / scenario.value
    if not park_path.exists():
        pack = SCENARIO_PACK.get(scenario)
        msg = f"Scenario '{scenario.name}' not found at {park_path}"
        if pack:
            msg += f"\nThis scenario requires the {pack} expansion pack."
        raise FileNotFoundError(msg)

    return park_path


def launch(park_file: str | Path | Scenario, port: int = DEFAULT_PORT, headless: bool = True) -> GameInstance:
    """Launch OpenRCT2 and return a connected GameInstance.

    Blocks until the bridge plugin is ready (up to 30s).
    Set headless=False to launch with the game window visible.
    """
    config = load_config()
    binary = config.get("openrct2_path")
    if not binary:
        raise RuntimeError("OpenRCT2 not configured. Run `pyrct2 setup` first.")

    if isinstance(park_file, Scenario):
        park_path = _resolve_scenario(park_file)
    else:
        park_path = Path(park_file)
        if not park_path.exists():
            raise FileNotFoundError(f"Park file not found: {park_path}")

    if _port_in_use(port):
        raise RuntimeError(f"Port {port} already in use. Is OpenRCT2 already running?")

    cmd = [binary, "host", str(park_path)]
    if headless:
        cmd.append("--headless")

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
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
            pass

        time.sleep(HEALTH_POLL_INTERVAL)

    process.terminate()
    raise TimeoutError(f"Bridge did not respond within {LAUNCH_TIMEOUT}s")
