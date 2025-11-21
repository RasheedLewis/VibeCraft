from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class AudjustConfigurationError(RuntimeError):
    """Raised when the Audjust client is not properly configured."""


class AudjustRequestError(RuntimeError):
    """Raised when the Audjust API request fails."""


def fetch_structure_segments(audio_path: Path) -> List[Dict[str, Any]]:
    """
    Upload an audio file to the Audjust structure endpoint and return the sections payload.

    Returns:
        List of dictionaries with keys like {"startMs": int, "endMs": int, "label": int}

    Raises:
        AudjustConfigurationError: If required settings are missing.
        AudjustRequestError: If the request fails or the payload is unexpected.
    """

    logger.debug("fetch_structure_segments called with audio_path=%s", audio_path)

    settings = get_settings()
    if not settings.audjust_base_url or not settings.audjust_api_key:
        raise AudjustConfigurationError("Audjust API credentials are not configured.")

    base_url = str(settings.audjust_base_url).rstrip("/")

    def _build_url(path: str | None, default: str) -> str:
        target = (path or default).strip()
        if not target.startswith("/"):
            target = f"/{target}"
        return f"{base_url}{target}"

    upload_url = _build_url(settings.audjust_upload_path, "/upload")
    structure_url = _build_url(settings.audjust_structure_path, "/structure")

    headers = {"X-API-Key": settings.audjust_api_key}
    timeout = settings.audjust_timeout_sec or 30.0

    try:
        upload_resp = httpx.get(upload_url, headers=headers, timeout=timeout)
        upload_resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise AudjustRequestError(f"Failed to obtain Audjust upload URL: {exc}") from exc

    upload_payload = upload_resp.json()
    storage_url = upload_payload.get("storageUrl")
    retrieval_url = upload_payload.get("retrievalUrl")
    if not storage_url or not retrieval_url:
        raise AudjustRequestError("Audjust upload endpoint did not return storage/retrieval URLs.")

    logger.debug(
        "Audjust upload URL acquired (storage_url=%s, retrieval_url=%s)",
        storage_url,
        retrieval_url,
    )

    try:
        with audio_path.open("rb") as fh:
            file_bytes = fh.read()
        put_resp = httpx.put(
            storage_url,
            content=file_bytes,
            timeout=timeout,
        )
        put_resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise AudjustRequestError(f"Failed to upload audio to Audjust storage: {exc}") from exc

    logger.debug("Audjust storage upload succeeded")

    payload = {
        "sourceFileUrl": retrieval_url,
    }
    
    try:
        response = httpx.post(
            structure_url,
            headers={**headers, "Content-Type": "application/json"},
            json=payload,
            timeout=timeout,
        )
    except httpx.HTTPError as exc:
        raise AudjustRequestError(f"Failed to call Audjust structure endpoint: {exc}") from exc

    if response.status_code >= 400:
        logger.error(
            "Audjust API returned error %s: %s",
            response.status_code,
            response.text[:500],
        )
        raise AudjustRequestError(
            f"Audjust API request failed with status {response.status_code}"
        )

    logger.debug(
        "Audjust API response status=%s length=%s body_preview=%s",
        response.status_code,
        len(response.text),
        response.text[:750],
    )

    try:
        structure_payload = response.json()
    except ValueError as exc:  # noqa: B902
        raise AudjustRequestError("Audjust API response was not valid JSON") from exc

    sections = None
    if isinstance(structure_payload, dict):
        if isinstance(structure_payload.get("sections"), list):
            sections = structure_payload["sections"]
        elif isinstance(structure_payload.get("result"), dict) and isinstance(
            structure_payload["result"].get("sections"), list
        ):
            sections = structure_payload["result"]["sections"]

    if not sections:
        raise AudjustRequestError("Audjust API response did not include sections.")

    logger.info(
        "Audjust returned %d sections (status=%s)",
        len(sections),
        response.status_code,
    )

    return sections

