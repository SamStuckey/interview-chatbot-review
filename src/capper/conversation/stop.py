"""Running turns and their cancellation tokens, held in-process by turn ID."""

from pydantic_ai import CancellationToken


class StopRegistry:
    def __init__(self) -> None:
        self._tokens: dict[str, CancellationToken] = {}

    def register(self, turn_id: str) -> CancellationToken:
        token = CancellationToken()
        self._tokens[turn_id] = token
        return token

    def release(self, turn_id: str) -> None:
        self._tokens.pop(turn_id, None)

    def stop(self, turn_id: str) -> bool:
        """Cancel the turn's run if it's still running here; `False` if there's nothing to stop."""
        token = self._tokens.get(turn_id)
        if token is None or token.cancelled:
            return False
        token.cancel()
        return True
