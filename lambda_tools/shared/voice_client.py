"""Nova Sonic voice synthesis module.

Provides speech synthesis via Amazon Nova Sonic on Bedrock InvokeModel API.
When ``voice=true`` is set on a request, call ``synthesize_speech`` after the
agent produces a text response to return both text and an audio stream.

Graceful degradation: if Nova Sonic fails for any reason, the caller receives
``None`` (text-only fallback) rather than an exception.

Target latency: < 3 seconds for synthesis.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_MODEL_ID = "amazon.nova-sonic-v1:0"
_CONTENT_TYPE = "application/json"
_ACCEPT = "audio/mpeg"
_MAX_TEXT_LENGTH = 3000  # guard against excessively long inputs
_LATENCY_WARN_SECONDS = 3.0

# Module-level client (reused across Lambda invocations)
_bedrock_client = None


def _get_client():
    """Lazy-initialise the Bedrock Runtime client."""
    global _bedrock_client
    if _bedrock_client is None:
        _bedrock_client = boto3.client("bedrock-runtime")
    return _bedrock_client


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def synthesize_speech(text: str) -> Optional[bytes]:
    """Convert *text* to speech using Nova Sonic via Bedrock InvokeModel.

    Parameters
    ----------
    text:
        The agent's text response to synthesise.  Truncated to
        ``_MAX_TEXT_LENGTH`` characters to stay within model limits.

    Returns
    -------
    bytes | None
        Raw audio bytes (MP3) on success, or ``None`` if synthesis fails
        (caller should fall back to text-only response).
    """
    if not text or not text.strip():
        logger.warning("synthesize_speech called with empty text — skipping")
        return None

    # Truncate overly long inputs
    if len(text) > _MAX_TEXT_LENGTH:
        logger.info(
            "Text truncated from %d to %d chars for voice synthesis",
            len(text),
            _MAX_TEXT_LENGTH,
        )
        text = text[:_MAX_TEXT_LENGTH]

    payload = {
        "inputText": text,
        "voiceConfig": {
            "engine": "neural",
            "languageCode": "en-US",
        },
    }

    start = time.monotonic()
    try:
        client = _get_client()
        response = client.invoke_model(
            modelId=_MODEL_ID,
            contentType=_CONTENT_TYPE,
            accept=_ACCEPT,
            body=json.dumps(payload),
        )
        audio_bytes: bytes = response["body"].read()
        elapsed = time.monotonic() - start

        if elapsed > _LATENCY_WARN_SECONDS:
            logger.warning(
                "Nova Sonic synthesis took %.2fs (target < %.1fs)",
                elapsed,
                _LATENCY_WARN_SECONDS,
            )
        else:
            logger.info("Nova Sonic synthesis completed in %.2fs", elapsed)

        if not audio_bytes:
            logger.error("Nova Sonic returned empty audio body")
            return None

        return audio_bytes

    except (ClientError, BotoCoreError) as exc:
        elapsed = time.monotonic() - start
        logger.error(
            "Nova Sonic synthesis failed after %.2fs: %s", elapsed, exc
        )
        return None
    except Exception:
        elapsed = time.monotonic() - start
        logger.exception(
            "Unexpected error during Nova Sonic synthesis after %.2fs", elapsed
        )
        return None


def build_response_with_voice(
    text: str, voice_enabled: bool
) -> dict:
    """Build a response payload, optionally including voice audio.

    Parameters
    ----------
    text:
        The agent's text response.
    voice_enabled:
        Whether the caller requested voice output (``voice=true``).

    Returns
    -------
    dict
        Always contains ``"text"``; contains ``"audio"`` (base64-ready bytes)
        only when *voice_enabled* is ``True`` and synthesis succeeds.
    """
    result: dict = {"text": text}

    if voice_enabled:
        audio = synthesize_speech(text)
        if audio is not None:
            result["audio"] = audio
        else:
            logger.info("Voice requested but synthesis failed — text-only fallback")

    return result
