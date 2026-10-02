from pathlib import Path
import re


def load_markdown_kb(folder: Path) -> dict[str, dict[str, str]]:
    entries = {}
    for filepath in folder.glob("*.md"):
        text = filepath.read_text(encoding="utf-8")
        parts = text.split("---", 2)
        if len(parts) != 3 or parts[0].strip():
            continue

        metadata = {}
        for line in parts[1].splitlines():
            key, separator, value = line.partition(":")
            if separator:
                metadata[key.strip()] = value.strip()

        label_key = metadata.get("label_key")
        body = parts[2].strip()
        if label_key and body:
            entries[label_key] = {"metadata": metadata, "text": body}
    return entries


def recommendation_from_knowledge(finding: dict, entry: dict) -> dict:
    sections = {}
    current_heading = None
    for line in entry["text"].splitlines():
        heading = re.match(r"^##\s+(.+?)\s*$", line)
        if heading:
            current_heading = heading.group(1).strip().lower()
            sections.setdefault(current_heading, [])
        elif current_heading and line.strip():
            sections[current_heading].append(line.strip())

    def section(*names: str) -> list[str]:
        return [paragraph for name in names for paragraph in sections.get(name, [])]

    identification = section("identification")
    damage = section("damage and symptoms")
    conditions = section("conditions that favour it", "conditions that favor it")
    cultural = section("cultural and prevention practices")
    biological = section("biological and low-risk controls")
    chemical = section("chemical control (registered products only, label rates, protective equipment)")
    extension = section("when to contact an extension officer")

    scientific_name = entry["metadata"].get("scientific_name", "").strip()
    description = " ".join((identification + damage)[:2])
    cause = " ".join(conditions) or (
        "The knowledge file does not specify conditions that favour this pest. "
        "Ask a local agricultural extension officer to assess the crop."
    )
    steps = [text for text in (" ".join(cultural), " ".join(biological), " ".join(chemical), " ".join(extension)) if text]
    prevention = [text for text in (" ".join(cultural), " ".join(biological)) if text]
    more_about = " ".join(damage + conditions)

    return {
        "pathogen": scientific_name,
        "description": description or f"The knowledge file identifies {finding['label']} as a crop pest.",
        "cause": cause,
        "steps": steps or ["Show the affected crop to a local agricultural extension officer for advice."],
        "more_about": more_about or cause,
        "prevention": prevention or ["Scout the crop regularly and ask a local extension officer for locally appropriate prevention advice."],
        "status": "diseased",
    }


def merge_recommendation_with_knowledge(
    recommendation: dict,
    findings: list[dict],
    knowledge_base: dict[str, dict[str, str]],
) -> dict:
    for finding in findings:
        entry = knowledge_base.get(finding["label_key"])
        if not entry:
            continue
        knowledge_result = recommendation_from_knowledge(finding, entry)
        for field in ("description", "cause", "steps", "more_about", "prevention", "pathogen"):
            current_value = recommendation.get(field)
            if field in {"steps", "prevention"}:
                missing_value = (
                    not isinstance(current_value, list)
                    or not current_value
                    or current_value == ["Please consult your local agricultural extension officer for guidance."]
                )
            else:
                missing_value = (
                    not isinstance(current_value, str)
                    or not current_value.strip()
                    or current_value == "We couldn't generate a detailed recommendation right now."
                )
            if missing_value:
                recommendation[field] = knowledge_result[field]
        break
    return recommendation