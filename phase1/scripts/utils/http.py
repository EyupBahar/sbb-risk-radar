"""Shared HTTP utilities for Phase 1 extractors."""

from __future__ import annotations

import json
import ssl
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

REQUEST_TIMEOUT_SECONDS = 30

_HTTP_ERROR_MESSAGES: dict[int, str] = {
    401: "401 Unauthorized — check API key.",
    403: "403 Forbidden — plan/quota/permissions may block this request.",
    429: "429 Too Many Requests — hit rate limit; wait and retry.",
}


def make_ssl_context(insecure_skip_tls_verify: bool) -> ssl.SSLContext | None:
    if insecure_skip_tls_verify:
        return ssl._create_unverified_context()  # noqa: SLF001
    return None


def fetch_json(
    url: str,
    *,
    insecure_skip_tls_verify: bool = False,
    timeout: int = REQUEST_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Fetch a URL and return the parsed JSON body.

    Raises RuntimeError with a human-readable message on any HTTP or
    network error so callers do not need to handle urllib internals.
    """
    context = make_ssl_context(insecure_skip_tls_verify)
    try:
        with urlopen(url, timeout=timeout, context=context) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        msg = _HTTP_ERROR_MESSAGES.get(exc.code, f"HTTP {exc.code}")
        raise RuntimeError(msg) from exc
    except URLError as exc:
        reason = getattr(exc, "reason", None)
        if isinstance(reason, ssl.SSLCertVerificationError):
            raise RuntimeError(
                "TLS certificate verification failed. "
                "Retry with --insecure-skip-tls-verify as a temporary workaround."
            ) from exc
        raise RuntimeError(f"Network error: {reason or exc}") from exc
