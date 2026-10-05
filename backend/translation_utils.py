import json
import re
from typing import Any


_TRANSLATION_STRING_FIELDS = ("description", "cause", "more_about")
_TRANSLATION_LIST_FIELDS = ("steps", "prevention")


def parse_translation(text: str) -> dict[str, Any] | None:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.IGNORECASE)
    if not cleaned:
        return None

    candidates = [cleaned]
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end > start:
        candidates.append(cleaned[start : end + 1])

    for candidate in candidates:
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return None


def normalize_translation(value: dict[str, Any] | None) -> dict[str, Any] | None:
    if value is None:
        return None

    result: dict[str, Any] = {}
    for field in _TRANSLATION_STRING_FIELDS:
        item = value.get(field)
        if not isinstance(item, str) or not item.strip():
            return None
        result[field] = item.strip()

    for field in _TRANSLATION_LIST_FIELDS:
        item = value.get(field)
        if not isinstance(item, list):
            return None
        cleaned_items = [entry.strip() for entry in item if isinstance(entry, str) and entry.strip()]
        if not cleaned_items:
            return None
        result[field] = cleaned_items

    pathogen = value.get("pathogen", "")
    result["pathogen"] = pathogen.strip() if isinstance(pathogen, str) else ""
    return result
