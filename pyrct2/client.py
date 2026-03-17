"""RCT2 client — main entry point for interacting with a running game."""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from pyrct2.cli import BRIDGE_VERSION
from pyrct2.connection import Connection, DEFAULT_HOST, DEFAULT_PORT
from pyrct2.launcher import GameInstance, launch
from pyrct2.scenarios import Scenario
from pyrct2._generated.actions import ActionsProxy
from pyrct2._generated.actions import GENERATED_API_VERSION as _ACTIONS_API_VERSION
from pyrct2._generated.state import StateProxy
from pyrct2._generated.state import GENERATED_API_VERSION as _STATE_API_VERSION

if _ACTIONS_API_VERSION != _STATE_API_VERSION:
    raise RuntimeError(
        f"Generated files are out of sync: actions.py is API v{_ACTIONS_API_VERSION} "
        f"but state.py is API v{_STATE_API_VERSION}. Regenerate both together."
    )

GENERATED_API_VERSION = _ACTIONS_API_VERSION


class RCT2:
    """Client for interacting with an OpenRCT2 game via the bridge plugin.

    Two modes of operation:
    - RCT2.launch(park_file) — spawns a headless game and owns its lifecycle
    - RCT2.connect(host, port) — attaches to an already-running instance
    """

    actions: ActionsProxy
    state: StateProxy

    def __init__(self, connection: Connection, instance: GameInstance | None = None):
        self._connection = connection
        self._instance = instance
        self.actions = ActionsProxy(self)
        self.state = StateProxy(self)

    @classmethod
    def launch(
        cls,
        park_file: str | Path | Scenario,
        port: int = DEFAULT_PORT,
        start_paused: bool = True,
        headless: bool = True,
    ) -> RCT2:
        """Launch OpenRCT2 and return a connected client.

        If start_paused is True (default), the game is paused immediately after
        the bridge becomes ready. A few scenario ticks (~10-20) may have elapsed.
        Set headless=False to launch with the game window visible.
        """
        instance = launch(park_file, port, headless=headless)
        client = cls(instance.connection, instance)
        client._check_bridge_version()
        if start_paused:
            client.pause()
        return client

    @classmethod
    def connect(cls, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> RCT2:
        """Connect to an already-running OpenRCT2 instance."""
        connection = Connection(host=host, port=port)
        result = connection.send("health")
        if not result.get("success"):
            connection.close()
            raise ConnectionError("Bridge responded but health check failed")
        client = cls(connection)
        client._check_bridge_version()
        return client

    def execute(self, endpoint: str, params: dict | BaseModel | None = None) -> dict:
        """Send a command to the bridge and return the response."""
        if self._instance is not None:
            self._instance.check_alive()
        if isinstance(params, BaseModel):
            params = params.model_dump(by_alias=True)
        return self._connection.send(endpoint, params)

    def get_status(self) -> dict:
        """Get current game status (paused state, date, ticks)."""
        return self.execute("get_status")

    def get_version(self) -> dict:
        """Get bridge plugin and API version info."""
        return self.execute("get_version")

    def pause(self) -> dict:
        """Pause the game."""
        return self.execute("pause")

    def unpause(self) -> dict:
        """Unpause the game."""
        return self.execute("unpause")

    def _query(self, endpoint: str) -> Any:
        """Send a state query and return the payload, raising on failure."""
        resp = self.execute(endpoint)
        if not resp.get("success"):
            raise RuntimeError(f"Query {endpoint!r} failed: {resp.get('error', resp)}")
        return resp.get("payload")

    def advance_ticks(self, ticks: int) -> dict:
        """Advance the game by N ticks (unpause → count → re-pause)."""
        return self.execute("advance_ticks", {"ticks": ticks})

    def _check_bridge_version(self) -> None:
        """Warn if the connected bridge plugin or API version doesn't match expectations."""
        result = self.execute("get_version")
        payload = result["payload"]

        plugin_version = payload["pluginVersion"]
        expected = BRIDGE_VERSION.lstrip("v")
        if plugin_version != expected:
            warnings.warn(
                f"Bridge plugin version mismatch: connected to {plugin_version}, "
                f"expected {expected}. Run `pyrct2 setup` to update.",
                stacklevel=3,
            )

        api_version = payload["apiVersion"]
        if api_version != GENERATED_API_VERSION:
            warnings.warn(
                f"API version mismatch: pyrct2 was generated against API v{GENERATED_API_VERSION} "
                f"but bridge reports v{api_version}. "
                f"Action calls may fail or behave unexpectedly. "
                f"Regenerate pyrct2 with openrct2-actiongen.",
                stacklevel=3,
            )

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
