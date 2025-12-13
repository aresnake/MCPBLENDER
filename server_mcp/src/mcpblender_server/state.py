from collections import deque
from typing import Any, Deque, Dict, Optional


class ServerState:
    """Lightweight in-memory diagnostics tracker."""

    def __init__(self, max_logs: int = 50, max_requests: int = 50) -> None:
        self.logs: Deque[str] = deque(maxlen=max_logs)
        self.request_ids: Deque[str] = deque(maxlen=max_requests)
        self.last_error: Optional[Dict[str, Any]] = None

    def record_request(self, request_id: str, tool: str) -> None:
        self.request_ids.append(request_id)
        self.logs.append(f"{request_id}:{tool}")

    def record_log(self, message: str) -> None:
        self.logs.append(message)

    def record_error(self, error: Dict[str, Any]) -> None:
        self.last_error = error
        self.logs.append(f"ERROR:{error.get('message', error)}")

    def diagnostics_payload(self) -> Dict[str, Any]:
        return {
            "logs": list(self.logs)[-10:],
            "last_error": self.last_error,
            "recent_request_ids": list(self.request_ids),
        }
