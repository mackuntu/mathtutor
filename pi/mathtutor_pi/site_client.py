"""Minimal stdlib HTTP client for the MathTutor device API."""

import json
import socket
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass


class SiteError(Exception):
    """A site request failed. Messages are short and never contain the token."""


@dataclass(frozen=True)
class PrintableWorksheet:
    serial: str
    html: str


_STATUS_REASONS = {401: "unauthorized", 404: "child not found"}


class SiteClient:
    def __init__(self, base_url: str, token: str, timeout_s: float):
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._timeout_s = timeout_s

    def __repr__(self) -> str:
        return f"SiteClient(base_url={self._base_url!r})"

    def new_worksheet(self, child_id: str) -> PrintableWorksheet:
        quoted = urllib.parse.quote(child_id, safe="")
        data = self._request("POST", f"/api/children/{quoted}/worksheets")
        try:
            return PrintableWorksheet(serial=data["serial"], html=data["html"])
        except (KeyError, TypeError):
            raise SiteError("bad response") from None

    def children(self) -> list[dict]:
        data = self._request("GET", "/api/children")
        kids = data.get("children") if isinstance(data, dict) else None
        if not isinstance(kids, list):
            raise SiteError("bad response")
        return kids

    def _request(self, method: str, path: str):
        req = urllib.request.Request(
            self._base_url + path,
            method=method,
            data=b"" if method == "POST" else None,
            headers={
                "Authorization": f"Bearer {self._token}",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout_s) as resp:
                body = resp.read()
        except urllib.error.HTTPError as exc:
            exc.close()
            reason = _STATUS_REASONS.get(exc.code, f"http {exc.code}")
            raise SiteError(reason) from None
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, (socket.timeout, TimeoutError)):
                raise SiteError("timeout") from None
            raise SiteError("connection failed") from None
        except (socket.timeout, TimeoutError):
            raise SiteError("timeout") from None
        except OSError:
            raise SiteError("connection failed") from None
        try:
            return json.loads(body)
        except ValueError:
            raise SiteError("bad response") from None
