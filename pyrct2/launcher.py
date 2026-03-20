"""Launch OpenRCT2 and wait for plugin readiness."""

import atexit
import re
import socket
import subprocess
import threading
import time
from pathlib import Path

from pyrct2.connection import Connection
from pyrct2.paths import load_config
from pyrct2.scenarios import SCENARIO_PACK, Scenario

HEALTH_POLL_INTERVAL = 0.5
LAUNCH_TIMEOUT = 30.0
PORT_PATTERN = re.compile(r"\[openrct2-bridge\] TCP server listening on port (\d+)")


class GameInstance:
    """A running OpenRCT2 process with an active bridge connection."""

    def __init__(
        self,
        process: subprocess.Popen,
        connection: Connection,
        logs: list[str],
    ):
        self._process = process
        self.connection = connection
        self.logs = logs
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


def launch(park_file: str | Path | Scenario, headless: bool = True) -> GameInstance:
    """Launch OpenRCT2 and return a connected GameInstance.

    The bridge plugin discovers its own port. This function reads the
    bound port from stdout, then connects. Blocks up to 30s.
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

    cmd = [binary, "host", str(park_path)]
    if headless:
        cmd.append("--headless")

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        text=True,
    )

    logs: list[str] = []
    port = _read_port_from_stdout(process, logs)
    connection = _wait_for_bridge(port, process)
    return GameInstance(process, connection, logs)


def _check_process(process: subprocess.Popen) -> None:
    """Raise if the process has exited."""
    if process.poll() is not None:
        raise RuntimeError(f"OpenRCT2 exited unexpectedly (exit code {process.returncode})")


def _read_port_from_stdout(process: subprocess.Popen, logs: list[str]) -> int:
    """Read stdout lines until the bridge reports its bound port."""
    deadline = time.monotonic() + LAUNCH_TIMEOUT

    for line in process.stdout:  # type: ignore[union-attr]
        line = line.rstrip("\n")
        logs.append(line)

        match = PORT_PATTERN.search(line)
        if match:
            return int(match.group(1))

        if time.monotonic() > deadline:
            break

        _check_process(process)

    process.terminate()
    last_lines = "\n".join(logs[-10:])
    raise TimeoutError(
        f"Bridge did not report port within {LAUNCH_TIMEOUT}s. "
        f"Expected log line matching: [openrct2-bridge] TCP server listening on port <N>\n"
        f"Last output:\n{last_lines}"
    )


def _wait_for_bridge(port: int, process: subprocess.Popen) -> Connection:
    """Connect and health-check."""
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
    raise TimeoutError(f"Bridge bound port {port} but health check failed within {LAUNCH_TIMEOUT}s")
