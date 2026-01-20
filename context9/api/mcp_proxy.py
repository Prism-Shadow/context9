"""
MCP Proxy API: forwards MCP JSON-RPC requests to a target URL to avoid CORS.
The frontend sends target_url, headers (e.g. Authorization for the MCP server), and body.
The proxy forwards them server-side so the MCP server receives the headers correctly.
"""

import re
from typing import Any

import requests
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from starlette.responses import Response

from ..auth.admin_auth import get_current_admin
from ..database.models import Admin

router = APIRouter()


class MCPProxyRequest(BaseModel):
    target_url: str
    headers: dict[str, str] = {}
    body: dict[str, Any]

    @field_validator("target_url")
    @classmethod
    def target_url_http_or_https(cls, v: str) -> str:
        v = (v or "").strip()
        if not re.match(r"^https?://", v, re.IGNORECASE):
            raise ValueError("target_url must start with http:// or https://")
        return v


@router.post("")
def mcp_proxy(
    req: MCPProxyRequest,
    _admin: Admin = Depends(get_current_admin),
):
    """
    Forward MCP JSON-RPC to target_url with the given headers and body.
    Used by the MCP Inspector to avoid CORS; the backend forwards the request
    so the MCP server receives headers (e.g. Authorization) correctly.
    """
    try:
        resp = requests.post(
            req.target_url,
            headers=req.headers,
            json=req.body,
            timeout=60,
        )
    except requests.RequestException as e:
        raise HTTPException(
            status_code=502, detail=f"Proxy request failed: {str(e)}"
        ) from e

    # Forward status, body, and mcp-session-id (required by MCP for subsequent requests).
    # MCP SDK uses header name "mcp-session-id". We must set Access-Control-Expose-Headers
    # so the browser exposes it to JS in cross-origin (e.g. dev: frontend :3000, API :8011).
    headers: dict[str, str] = {
        "Access-Control-Expose-Headers": "mcp-session-id",
    }
    session_id = resp.headers.get("mcp-session-id") or resp.headers.get(
        "Mcp-Session-Id"
    )
    if session_id:
        headers["mcp-session-id"] = session_id

    return Response(
        content=resp.content if resp.content is not None else b"",
        status_code=resp.status_code,
        media_type=resp.headers.get("Content-Type") or "application/json",
        headers=headers,
    )
