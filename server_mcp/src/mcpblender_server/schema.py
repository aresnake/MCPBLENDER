from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ErrorPayload:
    code: str
    message: str
    details: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        payload = {"code": self.code, "message": self.message}
        if self.details is not None:
            payload["details"] = self.details
        return payload


@dataclass
class ResponsePayload:
    ok: bool
    request_id: str
    data: Any = None
    error: Optional[ErrorPayload] = None

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"ok": self.ok, "request_id": self.request_id}
        if self.data is not None:
            payload["data"] = self.data
        if self.error is not None:
            payload["error"] = self.error.to_dict()
        return payload

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_mapping(cls, payload: Any, fallback_request_id: str = "unknown") -> "ResponsePayload":
        if not isinstance(payload, dict):
            return error_response(fallback_request_id, "invalid_response", "Bridge payload is not a JSON object", {"raw": payload})

        ok = payload.get("ok")
        request_id = payload.get("request_id", fallback_request_id)
        data = payload.get("data") if "data" in payload else None
        error_payload = payload.get("error")

        if not isinstance(ok, bool):
            return error_response(request_id, "invalid_response", "Bridge payload missing boolean ok flag", payload)
        if not isinstance(request_id, str) or not request_id:
            request_id = fallback_request_id

        error_obj: Optional[ErrorPayload] = None
        if error_payload is not None:
            if not isinstance(error_payload, dict):
                return error_response(request_id, "invalid_response", "Bridge error payload must be an object", payload)
            code = error_payload.get("code", "unknown")
            message = error_payload.get("message", "")
            details = error_payload.get("details")
            error_obj = ErrorPayload(code=str(code), message=str(message), details=details)

        return cls(ok=ok, request_id=request_id, data=data, error=error_obj)


def success_response(request_id: str, data: Any = None) -> ResponsePayload:
    return ResponsePayload(ok=True, request_id=request_id, data=data, error=None)


def error_response(request_id: str, code: str, message: str, details: Any = None) -> ResponsePayload:
    return ResponsePayload(ok=False, request_id=request_id, data=None, error=ErrorPayload(code=code, message=message, details=details))


@dataclass
class ToolRequest:
    method: str
    params: Dict[str, Any]
    request_id: str

    @classmethod
    def from_json(cls, raw: str) -> "ToolRequest":
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError("Tool request must be a JSON object")
        method = payload.get("method")
        if not isinstance(method, str) or not method:
            raise ValueError("method is required")
        params = payload.get("params", {})
        if params is None:
            params = {}
        if not isinstance(params, dict):
            raise ValueError("params must be a JSON object")
        request_id = payload.get("request_id")
        if not isinstance(request_id, str) or not request_id:
            raise ValueError("request_id is required")
        return cls(method=method, params=params, request_id=request_id)

    def to_json(self) -> str:
        return json.dumps({"method": self.method, "params": self.params, "request_id": self.request_id})
