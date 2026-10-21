"""Explicit diagnostic-only IPC envelope. No filesystem or process commands."""
import json
import re

SCHEMA_VERSION = 1
MAX_REQUEST_BYTES = 4096
MAX_MESSAGE_BYTES = 128
REQUEST_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def error(request_id, code):
    return encode({
        "schemaVersion": SCHEMA_VERSION,
        "requestId": request_id,
        "event": "diagnostics.error",
        "payload": {"code": code},
    })


def handle_request(raw):
    """Validate all untrusted JS inputs, always return a bounded JSON response."""
    if not isinstance(raw, str) or len(raw.encode("utf-8")) > MAX_REQUEST_BYTES:
        return error(None, "REQUEST_TOO_LARGE")
    try:
        obj = json.loads(raw)
    except (ValueError, TypeError):
        return error(None, "INVALID_JSON")
    if not isinstance(obj, dict):
        return error(None, "INVALID_ENVELOPE")
    rid = obj.get("requestId")
    rid = rid if isinstance(rid, str) and REQUEST_ID.fullmatch(rid) else None
    if type(obj.get("schemaVersion")) is not int or obj["schemaVersion"] != SCHEMA_VERSION:
        return error(rid, "INVALID_SCHEMA")
    if rid is None:
        return error(None, "INVALID_REQUEST_ID")
    if set(obj) != {"schemaVersion", "requestId", "command", "payload"}:
        return error(rid, "INVALID_ENVELOPE")
    if obj["command"] != "diagnostics.ping":
        return error(rid, "UNKNOWN_COMMAND")
    payload = obj["payload"]
    if (not isinstance(payload, dict) or set(payload) != {"message"}
            or not isinstance(payload["message"], str)
            or len(payload["message"].encode("utf-8")) > MAX_MESSAGE_BYTES):
        return error(rid, "INVALID_PAYLOAD")
    return encode({
        "schemaVersion": SCHEMA_VERSION,
        "requestId": rid,
        "event": "diagnostics.pong",
        "payload": {"message": payload["message"], "status": "ok"},
    })
