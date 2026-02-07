from __future__ import annotations

from typing import Iterable, List, Tuple
import json
import logging
import socket
import time
import urllib.error
import urllib.request

from .types import Message
from .errors import LLMRequestError, QuotaViolation

logger = logging.getLogger(__name__)

def split_system_messages(messages: Iterable[Message]) -> Tuple[str, List[Message]]:
    system_parts: List[str] = []
    non_system: List[Message] = []
    for msg in messages:
        role = msg.get("role", "")
        if role == "system":
            system_parts.append(msg.get("content", ""))
        else:
            non_system.append(msg)
    return "\n\n".join([part for part in system_parts if part.strip()]), non_system

def _parse_retry_delay(value: str | None) -> float | None:
    if not value:
        return None
    raw = value.strip().lower()
    if raw.endswith("s"):
        raw = raw[:-1]
    elif raw.endswith("m"):
        return float(raw[:-1]) * 60.0
    try:
        return float(raw)
    except ValueError:
        return None

def _extract_error_details(body: str, status_code: int) -> LLMRequestError:
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return LLMRequestError(
            status_code=status_code,
            message=body or "Request failed",
            retry_after_seconds=None,
            quota_violations=[],
            raw_response=body,
        )
    error = payload.get("error", {}) if isinstance(payload, dict) else {}
    message = error.get("message") or body or "Request failed"
    details = error.get("details", []) if isinstance(error, dict) else []
    retry_after = None
    quota_violations: List[QuotaViolation] = []
    for detail in details:
        if not isinstance(detail, dict):
            continue
        detail_type = detail.get("@type", "")
        if detail_type.endswith("RetryInfo"):
            retry_after = _parse_retry_delay(detail.get("retryDelay"))
        if detail_type.endswith("QuotaFailure"):
            for violation in detail.get("violations", []):
                if not isinstance(violation, dict):
                    continue
                quota_violations.append(
                    QuotaViolation(
                        quota_metric=str(violation.get("quotaMetric", "")),
                        quota_id=str(violation.get("quotaId", "")),
                        quota_dimensions=violation.get("quotaDimensions", {}) or {},
                        quota_value=str(violation.get("quotaValue", "")),
                    )
                )
    return LLMRequestError(
        status_code=status_code,
        message=str(message),
        retry_after_seconds=retry_after,
        quota_violations=quota_violations,
        raw_response=payload,
    )

def post_json(
    url: str,
    payload: dict,
    headers: dict,
    timeout: int = 30,
    max_retries: int = 0,
    retry_backoff: float = 1.0,
) -> dict:
    def _retry_transport(reason: str, attempt_index: int) -> None:
        delay = retry_backoff * (2 ** attempt_index)
        logger.warning("Retrying after %.2fs due to %s", delay, reason)
        time.sleep(delay)

    attempt = 0
    while True:
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8") if exc.fp else ""
            err = _extract_error_details(body, exc.code)
            if err.quota_violations:
                logger.warning("Quota violation: %s", err)
            if attempt < max_retries and exc.code in {429, 500, 502, 503, 504}:
                delay = err.retry_after_seconds
                if delay is None:
                    delay = retry_backoff * (2 ** attempt)
                logger.warning("Retrying after %.2fs due to HTTP %s", delay, exc.code)
                time.sleep(delay)
                attempt += 1
                continue
            raise err from exc
        except (TimeoutError, socket.timeout) as exc:
            if attempt < max_retries:
                _retry_transport("read timeout", attempt)
                attempt += 1
                continue
            raise RuntimeError(
                f"Transport timeout calling {url} after {attempt + 1} attempts (timeout={timeout}s): {exc}"
            ) from exc
        except urllib.error.URLError as exc:
            reason = getattr(exc, "reason", None)
            if isinstance(reason, (TimeoutError, socket.timeout)):
                if attempt < max_retries:
                    _retry_transport("read timeout", attempt)
                    attempt += 1
                    continue
                raise RuntimeError(
                    f"Transport timeout calling {url} after {attempt + 1} attempts (timeout={timeout}s): {reason}"
                ) from exc
            if attempt < max_retries:
                _retry_transport("transport error", attempt)
                attempt += 1
                continue
            raise RuntimeError(f"Transport error calling {url}: {exc}") from exc
        try:
            return json.loads(body)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Non-JSON response from {url}: {body}") from exc
