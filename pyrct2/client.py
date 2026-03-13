"""RCT2 client — main entry point for interacting with a running game."""

from __future__ import annotations

from pathlib import Path

from pyrct2.connection import Connection, DEFAULT_HOST, DEFAULT_PORT
from pyrct2.launcher import GameInstance, launch


class RCT2:
    """Client for interacting with an OpenRCT2 game via the bridge plugin.

    Two modes of operation:
    - RCT2.launch(park_file) — spawns a headless game and owns its lifecycle
    - RCT2.connect(host, port) — attaches to an already-running instance
    """

    def __init__(self, connection: Connection, instance: GameInstance | None = None):
        self._connection = connection
        self._instance = instance

    @classmethod
    def launch(cls, park_file: str | Path, port: int = DEFAULT_PORT) -> RCT2:
        """Launch OpenRCT2 headless and return a connected client."""
        instance = launch(park_file, port)
        return cls(instance.connection, instance)

    @classmethod
    def connect(cls, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> RCT2:
        """Connect to an already-running OpenRCT2 instance."""
        connection = Connection(host=host, port=port)
        result = connection.send("health")
        if not result.get("success"):
            connection.close()
            raise ConnectionError("Bridge responded but health check failed")
        return cls(connection)

    def execute(self, endpoint: str, params: dict | None = None) -> dict:
        """Send a command to the bridge and return the response."""
        if self._instance is not None:
            self._instance.check_alive()
        return self._connection.send(endpoint, params)

    def get_status(self) -> dict:
        """Get current game status (paused state, date, ticks)."""
        return self.execute("get_status")

    def get_version(self) -> dict:
        """Get bridge plugin and API version info."""
        return self.execute("get_version")

    def advance_ticks(self, ticks: int) -> dict:
        """Advance the game by N ticks (unpause → count → re-pause)."""
        return self.execute("advance_ticks", {"ticks": ticks})

    def close(self) -> None:
        """Shut down the connection and game process (if launched)."""
        if self._instance is not None:
            self._instance.stop()
        else:
            self._connection.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
