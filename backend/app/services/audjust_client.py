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

    logger.warning("[AUDJUST] fetch_structure_segments called with audio_path=%s", audio_path)

    settings = get_settings()
    if not settings.audjust_base_url or not settings.audjust_api_key:
        raise AudjustConfigurationError("Audjust API credentials are not configured.")

    base_url = str(settings.audjust_base_url).rstrip("/")
    logger.warning("[AUDJUST] Base URL configured: %s", base_url)

    def _build_url(path: str | None, default: str) -> str:
        target = (path or default).strip()
        if not target.startswith("/"):
            target = f"/{target}"
        return f"{base_url}{target}"

    upload_url = _build_url(settings.audjust_upload_path, "/upload")
    structure_url = _build_url(settings.audjust_structure_path, "/structure")
    
    logger.warning("[AUDJUST] Upload URL: %s", upload_url)
    logger.warning("[AUDJUST] Structure URL: %s", structure_url)

    headers = {"X-API-Key": settings.audjust_api_key}
    timeout = settings.audjust_timeout_sec or 30.0

    try:
        logger.warning("[AUDJUST] Requesting upload URLs from: %s", upload_url)
        upload_resp = httpx.get(upload_url, headers=headers, timeout=timeout)
        upload_resp.raise_for_status()
    except httpx.HTTPError as exc:
        logger.error("[AUDJUST] Failed to get upload URL: %s", exc)
        raise AudjustRequestError(f"Failed to obtain Audjust upload URL: {exc}") from exc

    upload_payload = upload_resp.json()
    storage_url = upload_payload.get("storageUrl")
    retrieval_url = upload_payload.get("retrievalUrl")
    if not storage_url or not retrieval_url:
        logger.error("[AUDJUST] Upload response missing URLs. Response: %s", upload_payload)
        raise AudjustRequestError("Audjust upload endpoint did not return storage/retrieval URLs.")

    logger.warning(
        "[AUDJUST] Upload URLs acquired:\n  Storage: %s\n  Retrieval: %s",
        storage_url,
        retrieval_url,
    )

    try:
        with audio_path.open("rb") as fh:
            file_bytes = fh.read()
        logger.warning("[AUDJUST] Uploading %d bytes to storage", len(file_bytes))
        put_resp = httpx.put(
            storage_url,
            content=file_bytes,
            timeout=timeout,
        )
        put_resp.raise_for_status()
        logger.warning("[AUDJUST] Storage upload succeeded (status: %s)", put_resp.status_code)
    except httpx.HTTPError as exc:
        logger.error("[AUDJUST] Failed to upload to storage: %s", exc)
        raise AudjustRequestError(f"Failed to upload audio to Audjust storage: {exc}") from exc

    payload = {
        "sourceFileUrl": retrieval_url,
    }
    
    logger.warning(
        "[AUDJUST] Calling structure API\n  URL: %s\n  Payload: %s\n  Headers: %s",
        structure_url,
        payload,
        {k: ("***" if k == "X-API-Key" else v) for k, v in headers.items()},
    )
    
    try:
        response = httpx.post(
            structure_url,
            headers={**headers, "Content-Type": "application/json"},
            json=payload,
            timeout=timeout,
        )
        logger.warning("[AUDJUST] Response status: %s", response.status_code)
    except httpx.HTTPError as exc:
        logger.error("[AUDJUST] HTTP error during request: %s", exc)
        raise AudjustRequestError(f"Failed to call Audjust structure endpoint: {exc}") from exc

    if response.status_code >= 400:
        logger.error(
            "[AUDJUST] API returned error %s: %s",
            response.status_code,
            response.text[:500],
        )
        raise AudjustRequestError(
            f"Audjust API request failed with status {response.status_code}"
        )

    logger.warning(
        "[AUDJUST] Response details:\n  Status: %s\n  Length: %s\n  Preview: %s",
        response.status_code,
        len(response.text),
        response.text[:750],
    )

    try:
        structure_payload = response.json()
    except ValueError as exc:  # noqa: B902
        logger.error("[AUDJUST] Response was not valid JSON: %s", response.text[:500])
        raise AudjustRequestError("Audjust API response was not valid JSON") from exc

    logger.warning("[AUDJUST] Parsed JSON keys: %s", list(structure_payload.keys()) if isinstance(structure_payload, dict) else type(structure_payload))

    sections = None
    if isinstance(structure_payload, dict):
        if isinstance(structure_payload.get("sections"), list):
            sections = structure_payload["sections"]
        elif isinstance(structure_payload.get("result"), dict) and isinstance(
            structure_payload["result"].get("sections"), list
        ):
            sections = structure_payload["result"]["sections"]

    if not sections:
        logger.error("[AUDJUST] No sections found in response. Full payload: %s", structure_payload)
        raise AudjustRequestError("Audjust API response did not include sections.")

    logger.warning(
        "[AUDJUST] Successfully extracted %d sections",
        len(sections),
    )

    return sections

