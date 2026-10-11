"""Google Gemini-backed aggregate-only AI insights for trial operations."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from backend.app.core import config as app_config
from backend.app.schemas.ai import AIInsightTopic

try:
    from google import genai  # type: ignore
except Exception:  # pragma: no cover - optional dependency fallback for tests
    genai = None


class GeminiServiceError(RuntimeError):
    """Base class for provider-related AI failures."""


class GeminiConfigurationError(GeminiServiceError):
    """Raised when the API key or SDK is unavailable."""


class GeminiTimeoutError(GeminiServiceError):
    """Raised when the provider call times out."""


class GeminiRateLimitError(GeminiServiceError):
    """Raised when the provider rate limits a request."""


class GeminiProviderError(GeminiServiceError):
    """Raised when the provider returns an unexpected or malformed response."""


TOPIC_QUESTIONS = {
    AIInsightTopic.ENROLLMENT: "Summarize enrollment momentum based on total participants, active counts, and completion/withdrawal patterns.",
    AIInsightTopic.COMPLETION: "Summarize completion trends based on the completion rate, active counts, and overall cohort progress.",
    AIInsightTopic.WITHDRAWALS: "Summarize withdrawal activity based on withdrawn counts, withdrawal rate, and any operational caution indicated by the metrics.",
    AIInsightTopic.PARTICIPANT_STATUS_DISTRIBUTION: "Summarize the participant status distribution across active, completed, and withdrawn counts without referencing any participant identifiers.",
}


def _get_settings() -> Any:
    """Return the live application settings instance, avoiding stale module-level copies."""
    return app_config.settings


def ensure_gemini_configured() -> None:
    """Validate the configured provider state before making a request to Gemini."""
    settings = _get_settings()
    api_key = (settings.GEMINI_API_KEY or "").strip()
    model_name = (settings.GEMINI_MODEL or "").strip()

    if not api_key:
        raise GeminiConfigurationError("The Gemini API key is not configured.")
    if not model_name:
        raise GeminiConfigurationError("The Gemini model is not configured.")
    if genai is None:
        raise GeminiConfigurationError("The Google GenAI SDK is not available.")


def build_ai_prompt(metrics: dict[str, Any], topic: AIInsightTopic | str | None = None) -> str:
    """Construct a prompt from a fixed allowed topic and aggregate trial metrics only."""
    normalized_topic = topic.value if isinstance(topic, AIInsightTopic) else str(topic or AIInsightTopic.ENROLLMENT).lower()
    fixed_question = TOPIC_QUESTIONS.get(AIInsightTopic(normalized_topic), TOPIC_QUESTIONS[AIInsightTopic.ENROLLMENT])

    total = int(metrics.get("total_participants", 0) or 0)
    status_counts = metrics.get("status_breakdown", []) or []
    status_lookup = {item.get("status"): item for item in status_counts if isinstance(item, dict)}
    active_count = int(metrics.get("active_count", status_lookup.get("active", {}).get("count", 0)) or 0)
    completed_count = int(metrics.get("completed_count", status_lookup.get("completed", {}).get("count", 0)) or 0)
    withdrawn_count = int(metrics.get("withdrawn_count", status_lookup.get("withdrawn", {}).get("count", 0)) or 0)
    enrollment_rate = float(metrics.get("active_rate", 0.0) or 0.0)
    completion_rate = float(metrics.get("completion_rate", 0.0) or 0.0)
    withdrawal_rate = float(metrics.get("withdrawal_rate", 0.0) or 0.0)

    lines = [
        "You are an operational trial dashboard assistant.",
        "Use only the aggregate metrics provided below.",
        "Never reference participant IDs, names, email addresses, raw CSV rows, or free-text notes.",
        "Do not infer clinical safety, efficacy, diagnoses, or treatment recommendations.",
        "Do not invent follow-up needs, completion dates, or participant risk scores.",
        "Return a short plain-text summary that clearly states it is AI-generated and requires human review.",
        "",
        "Aggregate metrics:",
        f"- total_participants: {total}",
        f"- active_count: {active_count}",
        f"- completed_count: {completed_count}",
        f"- withdrawn_count: {withdrawn_count}",
        f"- enrollment_rate: {enrollment_rate:.1f}%",
        f"- completion_rate: {completion_rate:.1f}%",
        f"- withdrawal_rate: {withdrawal_rate:.1f}%",
        "",
        f"Fixed analysis topic: {fixed_question}",
        "",
        "Response requirements:",
        "- Limit the answer to one short paragraph or bullet list.",
        "- Mention only operational patterns visible in the metrics.",
        "- Explicitly warn that this is advisory and should be validated by a human reviewer.",
    ]
    return "\n".join(lines)


async def generate_ai_insight(prompt: str) -> dict[str, Any]:
    """Generate an AI summary using the configured Gemini model."""
    settings = _get_settings()
    ensure_gemini_configured()
    api_key = (settings.GEMINI_API_KEY or "").strip()

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model=settings.GEMINI_MODEL, contents=prompt)
        text = getattr(response, "text", None)

        if text is None and hasattr(response, "candidates"):
            candidates = getattr(response, "candidates", []) or []
            if candidates:
                first = candidates[0]
                content = getattr(first, "content", None)
                parts = getattr(content, "parts", []) or []
                text = "".join(part.text for part in parts if getattr(part, "text", None))

        if not isinstance(text, str) or not text.strip():
            raise ValueError("Gemini returned an empty or malformed response.")

        generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        return {
            "analysis": text.strip(),
            "model": settings.GEMINI_MODEL,
            "generated_at": generated_at,
            "disclaimer": "AI-generated operational summary; review independently. Not a clinical conclusion.",
        }
    except TimeoutError as exc:  # pragma: no cover - exercised by app-level tests
        raise GeminiTimeoutError("The Gemini API timed out while generating insight.") from exc
    except Exception as exc:  # pragma: no cover - exercised by app-level tests
        message = str(exc).lower()
        if "429" in message or "rate limit" in message or "quota" in message:
            raise GeminiRateLimitError("The Gemini API rate limit has been exceeded.") from exc
        if "timeout" in message or "timed out" in message:
            raise GeminiTimeoutError("The Gemini API timed out while generating insight.") from exc
        raise GeminiProviderError("The Gemini provider request failed.") from exc
