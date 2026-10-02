from __future__ import annotations
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

SUPPORTED_LANGUAGES = ("English", "Hausa")


@dataclass
class DetectionRecord:
    """Represents one crop disease detection result."""

    crop: str
    disease: str
    confidence: float
    recommendation: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DocumentKnowledgeBase:
    """Loads crop disease facts from .docx files into an in-memory lookup table."""

    def __init__(self, folder: str | os.PathLike[str] | None = None) -> None:
        self.folder = Path(folder) if folder is not None else None
        self._kb: Dict[Tuple[str, str], str] = {}

    def load(self, folder: str | os.PathLike[str] | None = None) -> Dict[Tuple[str, str], str]:
        target_folder = Path(folder) if folder is not None else self.folder
        if target_folder is None:
            raise ValueError("A knowledge-base folder must be provided.")

        try:
            import docx  # type: ignore
        except ImportError as exc:  # pragma: no cover - import dependency may be missing
            raise ImportError("python-docx is required to load document-based knowledge base files.") from exc

        kb: Dict[Tuple[str, str], str] = {}
        filepaths = sorted(target_folder.rglob("*.docx"))

        for filepath in filepaths:
            filename = filepath.stem
            if "_" not in filename:
                print(f"Skipping '{filename}' - expected format is Crop_Disease")
                continue

            crop, _, disease = filename.partition("_")
            document = docx.Document(str(filepath))
            paragraphs = [p.text.strip() for p in document.paragraphs if p.text.strip()]
            facts = " ".join(paragraphs)
            kb[(crop, disease)] = facts

        self._kb = kb
        return kb

    def retrieve(self, crop: str, disease: str) -> str:
        facts = self._kb.get((crop, disease))
        if facts is None:
            return (
                "No verified record found for this specific crop/disease pair in the knowledge base. "
                "Answer using general, widely-accepted plant pathology practice, and clearly tell the "
                "farmer this is general guidance and to confirm with a local agricultural extension officer."
            )
        return facts

    @property
    def knowledge_base(self) -> Dict[Tuple[str, str], str]:
        return self._kb


class NAtlasRecommendationEngine:
    """High-level class that wraps the LLM and document knowledge base into an importable API."""

    def __init__(
        self,
        docs_folder: str | os.PathLike[str] | None = None,
        llm: Any = None,
        model_repo: str = "QuantFactory/N-ATLaS-GGUF",
        model_filename: str = "N-ATLaS.Q4_K_M.gguf",
        llm_kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.docs_folder = Path(docs_folder) if docs_folder is not None else None
        self.knowledge_base = DocumentKnowledgeBase(self.docs_folder)
        self.llm = llm
        self.model_repo = model_repo
        self.model_filename = model_filename
        self.llm_kwargs = llm_kwargs or {
            "n_ctx": 2048,
            "n_gpu_layers": -1,
            "n_threads": 2,
            "n_batch": 512,
            "verbose": False,
        }

    def load_knowledge_base(self, folder: str) -> Dict[Tuple[str, str], str]:
        return self.knowledge_base.load(folder or self.docs_folder)

    def load_model(self, repo_id: Optional[str] = None, filename: Optional[str] = None, **kwargs: Any) -> Any:
        try:
            from llama_cpp import Llama  # type: ignore
        except ImportError as exc:  # pragma: no cover - import dependency may be missing
            raise ImportError("llama-cpp-python is required to load the N-ATLaS model.") from exc

        repo_id = repo_id or self.model_repo
        filename = filename or self.model_filename
        config = {**self.llm_kwargs, **kwargs}
        self.llm = Llama.from_pretrained(
            repo_id=repo_id,
            filename=filename,
            **config,
        )
        return self.llm

    def retrieve_facts(self, crop: str, disease: str) -> str:
        return self.knowledge_base.retrieve(crop, disease)

    def build_prompt(self, crop: str, disease: str, confidence: float, facts: str, language: str) -> List[Dict[str, str]]:
        system_message = (
            "You are an agricultural assistant that writes short, clear, practical treatment advice for farmers. "
            f"Reply ONLY in {language}. Use simple, everyday language. Avoid long paragraphs. "
            "Use verified facts you are given and do not invent facts not supported by them. "
            "Never name a tool, product, or resource unless it is stated in the facts given to you."
        )

        user_message = f"""
A crop disease detection system has produced this result:
- Crop: {crop}
- Detected condition: {disease}
- Model confidence: {confidence:.0%}

Verified facts about this condition:
\"\"\"
{facts}
\"\"\"

Using ONLY the facts above, write a short answer for the farmer with these 3 parts:

1. WHAT IT IS: One simple sentence saying what this disease/problem is.
2. WHY IT HAPPENED OR WHAT COULD HAVE CAUSED IT TO HAPPEN AT THE FARM: One simple sentence on what usually causes it and the likely root cause(weather, soil, water, pests, etc).
3. HOW TO FIX IT: 3-4 clear steps to treat or stop it. For each step, name the exact
   tool, product, or resource to use (for example: a named based fungicide, a spray type,
   a trap, a local extension office) -- only if that detail is in the facts above.
   If the facts do not name a specific tool, say plainly that no specific product
   is confirmed yet and to ask a local agricultural extension officer.

Keep your ENTIRE answer to a MAXIMUM of 100 words total. Count as you write.
Stop as soon as you reach 100 words, even if you must shorten a step. Write it in {language}
Do not add a greeting or sign-off. Just the 3 parts above, in plain simple language with the action steps bulleted.
"""

        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ]

    def call_llm(self, messages: List[Dict[str, str]], max_new_tokens: int = 500, retries: int = 1) -> str:
        if self.llm is None:
            raise RuntimeError("The language model has not been loaded. Call load_model() first.")

        for attempt in range(retries + 1):
            try:
                output = self.llm.create_chat_completion(
                    messages=messages,
                    max_tokens=max_new_tokens,
                    temperature=0.1,
                    top_p=0.9,
                    repeat_penalty=1.1,
                )
                content = output["choices"][0]["message"]["content"].strip()
                if content:
                    return content
            except Exception as exc:  # pragma: no cover - network/model errors
                print(f"LLM call failed (attempt {attempt + 1}/{retries + 1}): {exc}")

        return (
            "Sorry, the recommendation could not be generated right now. "
            "Please try again, or consult your local agricultural extension officer."
        )

    def get_recommendation(self, crop: str, disease: str, confidence: float, language: str) -> str:
        facts = self.retrieve_facts(crop, disease)
        messages = self.build_prompt(crop, disease, confidence, facts, language=language)
        return self.call_llm(messages)

    def get_recommendations(self, detections: Iterable[DetectionRecord | Dict[str, Any]], language: str = "English") -> List[DetectionRecord]:
        results: List[DetectionRecord] = []
        for item in detections:
            if isinstance(item, DetectionRecord):
                record = item
            else:
                record = DetectionRecord(
                    crop=str(item.get("crop", "")),
                    disease=str(item.get("disease", "")),
                    confidence=float(item.get("confidence", 0.0)),
                )

            recommendation = self.get_recommendation(record.crop, record.disease, record.confidence, language)
            record.recommendation = recommendation
            results.append(record)
        return results


def load_kb_from_documents(folder: str | os.PathLike[str]) -> Dict[Tuple[str, str], str]:
    return DocumentKnowledgeBase(folder).load(folder)


if __name__ == "__main__":
    engine = NAtlasRecommendationEngine(docs_folder="/content/drive/MyDrive/CROP_DISEASES")
    engine.load_knowledge_base()

    sample_detections = [
        {"crop": "Tomato", "disease": "Early_blight", "confidence": 0.94},
        {"crop": "Tomato", "disease": "Late_blight", "confidence": 0.88},
    ]

    print("Loading model...")
    engine.load_model()
    print("Generating sample recommendations...")
    results = engine.get_recommendations(sample_detections, language="English")
    for item in results:
        print(f"- {item.crop}/{item.disease}: {item.recommendation[:120]}...")
