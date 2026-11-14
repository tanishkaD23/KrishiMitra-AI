"""Official Gnani.ai (Vachana API) Speech-to-Text (Prisma v3.0) and Text-to-Speech (Timbre v2.5)
integration for KrishiSathi AI.

Official Documentation References:
- Introduction: https://docs.gnani.ai/api/introduction/introduction
- Speech-to-Text (Prisma): https://docs.gnani.ai/api/STT/speech-to-text
  Endpoint: POST https://api.vachana.ai/stt/v3
- Text-to-Speech (Timbre): https://docs.gnani.ai/api/TTS/tts-inference
  Endpoint: POST https://api.vachana.ai/api/v1/tts/inference
- Authentication Header: X-API-Key-ID: <GNANI_API_KEY>
"""

import base64
from email.parser import BytesParser
from email.policy import default as default_email_policy
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import requests
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT_DIR / ".env")

logger = logging.getLogger(__name__)

GNANI_BASE_URL = os.getenv("GNANI_BASE_URL", "https://api.vachana.ai").rstrip("/")
GNANI_STT_ENDPOINT = f"{GNANI_BASE_URL}/stt/v3"
GNANI_TTS_ENDPOINT = f"{GNANI_BASE_URL}/api/v1/tts/inference"

DEFAULT_STT_MODEL = "prisma-v3.0"
DEFAULT_TTS_MODEL = "timbre-v2.5"

# Supported audio file formats per https://docs.gnani.ai/api/STT/speech-to-text
SUPPORTED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".ogg", ".flac", ".aac", ".m4a"}
MIME_BY_EXTENSION = {
    ".wav": "audio/wav",
    ".mp3": "audio/mpeg",
    ".ogg": "audio/ogg",
    ".flac": "audio/flac",
    ".aac": "audio/aac",
    ".m4a": "audio/mp4",
}

# Official Timbre v2.5 Voice Personas
TIMBRE_V25_VOICES = {
    "female": "Nalini",
    "male": "Deepak",
    "alt_female": "Kaveri",
}

AGRICULTURAL_KEYTERMS = [
    "PM-KISAN",
    "PMFBY",
    "Kisan Credit Card",
    "PM-KUSUM",
    "Soil Health Card",
    "PMKSY",
    "KrishiSathi",
    "Rabi",
    "Kharif",
    "Wheat",
    "Mustard",
    "CRI irrigation",
    "Yellow Rust",
    "Urea",
    "DAP",
    "Quintal",
]


def _get_gnani_api_key() -> str:
    """Securely retrieves GNANI_API_KEY from environment without logging or exposing it."""
    load_dotenv(ROOT_DIR / ".env", override=False)
    return (os.getenv("GNANI_API_KEY") or "").strip()


def normalize_stt_language(lang: Optional[str]) -> str:
    """Normalizes language selection into Gnani Prisma v3.0 language_code format."""
    raw = (lang or "hi-IN,en-IN").strip()
    lower = raw.lower()
    if lower in ("hi", "hi-in", "hindi"):
        return "hi-IN"
    if lower in ("en", "en-in", "english"):
        return "en-IN"
    if lower in ("hinglish", "auto", "indic-auto", "bilingual", "hi-en"):
        return "indic-auto"
    if "," in raw or "-" in raw:
        return raw
    return "indic-auto"


def normalize_tts_language(lang: Optional[str], text: str = "") -> str:
    """Normalizes language code into Gnani Timbre v2.5 locale ('hi-IN' or 'en-IN')."""
    raw = (lang or "").strip().lower()
    has_devanagari = bool(re.search(r"[\u0900-\u097F]", text or ""))
    if has_devanagari or raw in ("hi", "hi-in", "hindi"):
        return "hi-IN"
    return "en-IN"


def clean_text_for_tts(text: str, max_chars: int = 1400) -> str:
    """Cleans markdown formatting and URLs from chatbot RAG answers for natural speech synthesis."""
    if not text:
        return ""
    cleaned = re.sub(r"\*\*(.+?)\*\*", r"\1", str(text))
    cleaned = re.sub(r"\*(.+?)\*", r"\1", cleaned)
    cleaned = re.sub(r"`(.+?)`", r"\1", cleaned)
    cleaned = re.sub(r"https?://\S+", "", cleaned)
    cleaned = re.sub(r"[#•_~]+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if len(cleaned) > max_chars:
        cleaned = cleaned[:max_chars].rsplit(" ", 1)[0] + "."
    return cleaned


def get_gnani_voice_status() -> Dict[str, Any]:
    """Returns Gnani.ai voice configuration metadata without exposing the API key."""
    api_key = _get_gnani_api_key()
    return {
        "status": "success",
        "gnani_configured": bool(api_key),
        "provider": "Gnani.ai (Vachana API)",
        "base_url": GNANI_BASE_URL,
        "stt": {
            "endpoint": "/api/krishisathi/stt",
            "upstream_url": GNANI_STT_ENDPOINT,
            "model": DEFAULT_STT_MODEL,
            "supported_languages": ["hi-IN", "en-IN", "indic-auto", "hi-IN,en-IN"],
            "supported_formats": ["wav", "mp3", "ogg", "flac", "aac", "m4a"],
            "max_duration_seconds": 30,
        },
        "tts": {
            "endpoint": "/api/krishisathi/tts",
            "upstream_url": GNANI_TTS_ENDPOINT,
            "model": DEFAULT_TTS_MODEL,
            "supported_languages": ["hi-IN", "en-IN"],
            "voices": TIMBRE_V25_VOICES,
        },
    }


def transcribe_speech_gnani(
    audio_bytes: bytes,
    filename: str = "recording.wav",
    language_code: Optional[str] = "hi-IN,en-IN",
    model: Optional[str] = DEFAULT_STT_MODEL,
    output_format: Optional[str] = "codemix",
) -> Dict[str, Any]:
    """Transcribes farmer voice audio using Gnani Prisma STT REST API (`POST https://api.vachana.ai/stt/v3`)."""
    if not audio_bytes or len(audio_bytes) < 64:
        return {
            "status": "error",
            "error_code": "EMPTY_AUDIO",
            "message": "Recorded audio clip is empty or too short. Please hold the microphone and speak clearly.",
        }

    if len(audio_bytes) > 15 * 1024 * 1024:
        return {
            "status": "error",
            "error_code": "AUDIO_TOO_LARGE",
            "message": "Audio clip exceeds the 30-second limit for synchronous STT. Please record a shorter question.",
        }

    ext = Path(filename or "recording.wav").suffix.lower()
    if not ext:
        ext = ".wav"
        filename = f"{filename}.wav"

    if ext not in SUPPORTED_AUDIO_EXTENSIONS:
        return {
            "status": "error",
            "error_code": "UNSUPPORTED_AUDIO_FORMAT",
            "message": (
                f"Unsupported audio format '{ext}'. Gnani Prisma STT supports WAV, MP3, OGG, FLAC, AAC, and M4A."
            ),
        }

    api_key = _get_gnani_api_key()
    if not api_key:
        return {
            "status": "error",
            "error_code": "GNANI_API_KEY_MISSING",
            "message": "GNANI_API_KEY is not set on the backend server. Falling back to browser speech recognition.",
        }

    stt_model = (model or DEFAULT_STT_MODEL).strip()
    if stt_model.lower() in ("prismav3.0", "prisma_v3.0", "prisma-v3"):
        stt_model = "prisma-v3.0"
    elif stt_model.lower() in ("prismav2.5", "prisma_v2.5", "prisma-v2"):
        stt_model = "prisma-v2.5"

    norm_lang = normalize_stt_language(language_code)
    if stt_model == "prisma-v2.5" and ("," in norm_lang or norm_lang == "indic-auto"):
        norm_lang = "hi-IN"

    mime_type = MIME_BY_EXTENSION.get(ext, "audio/wav")

    form_data: Dict[str, Any] = {
        "model": stt_model,
        "language_code": norm_lang,
    }
    if stt_model == "prisma-v3.0":
        if output_format in ("verbatim", "transcribe", "codemix", "transliterate"):
            form_data["format"] = output_format
        form_data["topic"] = "Indian agriculture, crop yield, irrigation, fertilizers, and government schemes"

    headers = {
        "X-API-Key-ID": api_key,
    }

    try:
        response = requests.post(
            GNANI_STT_ENDPOINT,
            headers=headers,
            files={"audio_file": (filename, audio_bytes, mime_type)},
            data=form_data,
            timeout=22,
        )
    except requests.exceptions.Timeout:
        logger.warning("Gnani Prisma STT request timed out.")
        return {
            "status": "error",
            "error_code": "API_TIMEOUT",
            "message": "Gnani Speech-to-Text service timed out. Please try speaking again or type your question.",
        }
    except requests.exceptions.RequestException as exc:
        logger.warning("Gnani Prisma STT network error: %s", type(exc).__name__)
        return {
            "status": "error",
            "error_code": "NETWORK_ERROR",
            "message": "Could not reach Gnani Speech-to-Text service. Please check your connection or use text chat.",
        }

    if response.status_code == 429:
        return {
            "status": "error",
            "error_code": "RATE_LIMIT_EXCEEDED",
            "message": "Gnani STT rate limit reached (HTTP 429). Please wait a few seconds before trying voice input again.",
        }

    if response.status_code in (401, 403):
        return {
            "status": "error",
            "error_code": "AUTH_FAILED",
            "message": "Gnani API authentication failed. Please verify GNANI_API_KEY in backend environment variables.",
        }

    try:
        payload = response.json()
    except ValueError:
        payload = {}

    if not response.ok or payload.get("success") is False:
        err_msg = (
            payload.get("message")
            or payload.get("detail")
            or payload.get("error")
            or f"Gnani STT returned HTTP {response.status_code}"
        )
        return {
            "status": "error",
            "error_code": "STT_FAILED",
            "status_code": response.status_code,
            "message": str(err_msg),
        }

    transcript = (payload.get("transcript") or payload.get("text") or "").strip()
    if not transcript:
        return {
            "status": "error",
            "error_code": "NO_SPEECH_DETECTED",
            "message": "No clear speech was detected in the recording. Please speak closer to the microphone.",
        }

    return {
        "status": "success",
        "success": True,
        "request_id": payload.get("request_id", ""),
        "transcript": transcript,
        "model": payload.get("model", stt_model),
        "detected_language_code": payload.get("detected_language_code", norm_lang),
        "processing_time": payload.get("processing_time"),
        "end_to_end_latency": payload.get("end_to_end_latency"),
    }


def synthesize_speech_gnani(
    text: str,
    language: Optional[str] = "hi-IN",
    voice: Optional[str] = None,
    gender: Optional[str] = "female",
    model: Optional[str] = DEFAULT_TTS_MODEL,
    speed: float = 1.0,
    sample_rate: int = 48000,
    container: str = "wav",
) -> Dict[str, Any]:
    """Synthesizes natural spoken audio using Gnani Timbre v2.5 (`POST https://api.vachana.ai/api/v1/tts/inference`)."""
    cleaned_text = clean_text_for_tts(text)
    if not cleaned_text:
        return {
            "status": "error",
            "error_code": "EMPTY_TEXT",
            "message": "Text is required for speech synthesis.",
        }

    api_key = _get_gnani_api_key()
    if not api_key:
        return {
            "status": "error",
            "error_code": "GNANI_API_KEY_MISSING",
            "message": "GNANI_API_KEY is not configured on the backend server.",
        }

    tts_model = (model or DEFAULT_TTS_MODEL).strip()
    if tts_model.lower() in ("timbrev2.5", "timbre_v2.5", "timbre-v2.5", "gnani-timbre-v2.5"):
        tts_model = "timbre-v2.5"
    elif tts_model.lower() in ("timbrev3.0", "timbre_v3.0", "timbre-v3.0"):
        tts_model = "timbre-v3.0"

    target_lang = normalize_tts_language(language, cleaned_text)

    selected_voice = (voice or "").strip()
    if not selected_voice:
        if (gender or "female").strip().lower() == "male":
            selected_voice = TIMBRE_V25_VOICES["male"]
        else:
            selected_voice = TIMBRE_V25_VOICES["female"]

    clamped_speed = max(0.5, min(2.0, float(speed or 1.0)))
    req_payload = {
        "text": cleaned_text,
        "voice": selected_voice,
        "model": tts_model,
        "language": target_lang,
        "speed": clamped_speed,
        "audio_config": {
            "encoding": "linear_pcm",
            "container": container if container in ("wav", "mp3") else "wav",
            "num_channels": 1,
            "sample_rate": int(sample_rate or 48000),
            "sample_width": 2,
        },
    }

    headers = {
        "Content-Type": "application/json",
        "X-API-Key-ID": api_key,
    }

    try:
        response = requests.post(
            GNANI_TTS_ENDPOINT,
            headers=headers,
            json=req_payload,
            timeout=25,
        )
    except requests.exceptions.Timeout:
        logger.warning("Gnani Timbre TTS request timed out.")
        return {
            "status": "error",
            "error_code": "API_TIMEOUT",
            "message": "Gnani Text-to-Speech service timed out.",
        }
    except requests.exceptions.RequestException as exc:
        logger.warning("Gnani Timbre TTS network error: %s", type(exc).__name__)
        return {
            "status": "error",
            "error_code": "NETWORK_ERROR",
            "message": "Could not connect to Gnani Text-to-Speech service.",
        }

    if response.status_code == 429:
        return {
            "status": "error",
            "error_code": "RATE_LIMIT_EXCEEDED",
            "message": "Gnani TTS rate limit reached (HTTP 429). Please try again shortly.",
        }

    if response.status_code in (401, 403):
        return {
            "status": "error",
            "error_code": "AUTH_FAILED",
            "message": "Gnani API authentication failed. Please check GNANI_API_KEY on the backend.",
        }

    content_type = (response.headers.get("Content-Type") or "").lower()
    if not response.ok or "application/json" in content_type:
        try:
            err_json = response.json()
        except ValueError:
            err_json = {}

        # Some integrations may return base64 audio inside JSON; check before treating as error
        b64_audio = err_json.get("audio") or err_json.get("audio_base64") or err_json.get("audioContent")
        if response.ok and b64_audio:
            raw_bytes = base64.b64decode(b64_audio)
            return {
                "status": "success",
                "audio_bytes": raw_bytes,
                "audio_base64": b64_audio,
                "content_type": "audio/wav",
                "model": tts_model,
                "voice": selected_voice,
                "language": target_lang,
            }

        err_msg = (
            err_json.get("message")
            or err_json.get("detail")
            or f"Gnani Timbre TTS failed with HTTP {response.status_code}"
        )
        return {
            "status": "error",
            "error_code": "TTS_FAILED",
            "status_code": response.status_code,
            "message": str(err_msg),
        }

    audio_bytes = response.content
    if not audio_bytes or len(audio_bytes) < 64:
        return {
            "status": "error",
            "error_code": "EMPTY_TTS_AUDIO",
            "message": "Gnani TTS returned an empty audio stream.",
        }

    return {
        "status": "success",
        "audio_bytes": audio_bytes,
        "audio_base64": base64.b64encode(audio_bytes).decode("ascii"),
        "content_type": "audio/wav" if req_payload["audio_config"]["container"] == "wav" else "audio/mpeg",
        "model": tts_model,
        "voice": selected_voice,
        "language": target_lang,
    }


def parse_raw_multipart_or_json(content_type: str, body: bytes) -> Tuple[bytes, str, Dict[str, Any]]:
    """Extracts (audio_bytes, filename, fields_dict) from raw multipart/form-data or application/json body."""
    ctype = (content_type or "").lower()
    if "application/json" in ctype:
        import json as _json
        data = _json.loads(body.decode("utf-8", errors="replace") or "{}")
        b64_str = data.get("audio_base64") or data.get("audio") or ""
        if "," in b64_str and b64_str.startswith("data:"):
            b64_str = b64_str.split(",", 1)[1]
        raw_audio = base64.b64decode(b64_str) if b64_str else b""
        fname = data.get("filename") or "recording.wav"
        return raw_audio, fname, data

    if "multipart/form-data" in ctype:
        header_bytes = f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("utf-8")
        msg = BytesParser(policy=default_email_policy).parsebytes(header_bytes + body)
        audio_bytes = b""
        filename = "recording.wav"
        fields: Dict[str, Any] = {}
        if msg.is_multipart():
            for part in msg.iter_parts():
                cd = part.get("Content-Disposition", "")
                name_match = re.search(r'name="([^"]+)"', cd)
                fname_match = re.search(r'filename="([^"]+)"', cd)
                field_name = name_match.group(1) if name_match else ""
                payload = part.get_payload(decode=True) or b""
                if fname_match or field_name in ("audio_file", "audio", "file"):
                    audio_bytes = payload
                    if fname_match:
                        filename = fname_match.group(1)
                elif field_name:
                    fields[field_name] = payload.decode("utf-8", errors="replace")
        return audio_bytes, filename, fields

    return body, "recording.wav", {}

