"""
Low-level RCON wrapper for Factorio.

Handles connection management and Lua command execution.
"""

from factorio_rcon import RCONClient
from typing import Optional, Any
import re


class RCONError(Exception):
    """Base exception for RCON errors."""
    pass


class ConnectionError(RCONError):
    """Raised when connection to server fails."""
    pass


class CommandError(RCONError):
    """Raised when a Lua command fails."""
    pass


class RCONWrapper:
    """
    Wrapper around factorio-rcon-py with convenience methods.

    Usage:
        rcon = RCONWrapper()
        rcon.connect()

        # Execute Lua (fire and forget)
        rcon.execute_lua('game.print("Hello")')

        # Query Lua (get result back)
        tick = rcon.query_lua('game.tick')

        rcon.disconnect()
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 27015,
        password: str = "test123"
    ):
        self.host = host
        self.port = port
        self.password = password
        self._client: Optional[RCONClient] = None

    @property
    def connected(self) -> bool:
        """Check if connected to server."""
        return self._client is not None

    def connect(self) -> None:
        """Connect to Factorio RCON server."""
        if self._client is not None:
            return  # Already connected

        try:
            self._client = RCONClient(self.host, self.port, self.password)
        except Exception as e:
            raise ConnectionError(f"Failed to connect to {self.host}:{self.port}: {e}")

    def disconnect(self) -> None:
        """Disconnect from server."""
        if self._client is not None:
            try:
                self._client.close()
            except Exception:
                pass  # Ignore errors on disconnect
            self._client = None

    def send_command(self, command: str) -> Optional[str]:
        """
        Send raw command to server.

        Args:
            command: Raw command string (e.g., "/version" or "/c ...")

        Returns:
            Response string, or None if no response.
        """
        if self._client is None:
            raise ConnectionError("Not connected to server")

        try:
            result = self._client.send_command(command)
            return result if result else None
        except Exception as e:
            # Check if connection was lost
            self._client = None
            raise ConnectionError(f"Connection lost: {e}")

    def execute_lua(self, lua_code: str) -> Optional[str]:
        """
        Execute Lua code on the server.

        This is "fire and forget" - for commands that don't return data,
        or where you don't care about the result.

        Args:
            lua_code: Lua code to execute (without /c prefix)

        Returns:
            Raw response string, or None.
        """
        command = f"/c {lua_code}"
        result = self.send_command(command)

        # Check for Lua errors in response
        if result and self._is_lua_error(result):
            raise CommandError(f"Lua error: {result}")

        return result

    def query_lua(self, lua_expression: str) -> Optional[str]:
        """
        Query a Lua expression and return the result.

        Automatically wraps the expression in rcon.print() to get the value back.
        For tables, wraps in serpent.line() for serialization.

        Args:
            lua_expression: Lua expression to evaluate (e.g., "game.tick")

        Returns:
            String result of the expression.
        """
        # Wrap in rcon.print to get the value back
        lua_code = f"rcon.print({lua_expression})"
        return self.execute_lua(lua_code)

    def query_lua_table(self, lua_expression: str, format: str = "line") -> Optional[str]:
        """
        Query a Lua table expression and return serialized result.

        Uses serpent library to serialize the table to a string.

        Args:
            lua_expression: Lua expression that returns a table
            format: Serpent format - "line" (compact), "block" (readable), or "dump"

        Returns:
            Serialized table as string.
        """
        if format not in ("line", "block", "dump"):
            format = "line"

        lua_code = f"rcon.print(serpent.{format}({lua_expression}))"
        return self.execute_lua(lua_code)

    def _is_lua_error(self, response: str) -> bool:
        """Check if response indicates a Lua error."""
        error_patterns = [
            r"Error",
            r"attempt to",
            r"expected",
            r"syntax error",
        ]
        for pattern in error_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                return True
        return False

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
        return False
