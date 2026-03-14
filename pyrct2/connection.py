"""TCP connection to openrct2-bridge (NDJSON protocol on port 9090)."""

import json
import socket

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9090
DEFAULT_TIMEOUT = 10.0


class Connection:
    """Single TCP connection to an openrct2-bridge plugin instance."""

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.settimeout(timeout)
        self._socket.connect((host, port))
        self._buffer = ""

    def send(self, endpoint: str, params: dict | None = None) -> dict:
        """Send a request and return the parsed response."""
        msg: dict = {"endpoint": endpoint}
        if params is not None:
            msg["params"] = params

        self._socket.sendall(json.dumps(msg).encode() + b"\n")

        while "\n" not in self._buffer:
            chunk = self._socket.recv(4096).decode()
            if not chunk:
                raise ConnectionError("Bridge closed the connection")
            self._buffer += chunk

        line, self._buffer = self._buffer.split("\n", 1)
        return json.loads(line)

    def close(self) -> None:
        """Close the TCP connection."""
        self._socket.close()
