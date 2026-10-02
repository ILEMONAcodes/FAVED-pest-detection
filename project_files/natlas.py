import os
from typing import Any, Dict, Iterable, List, Optional, Tuple

from dotenv import load_dotenv

load_dotenv()

token = os.environ.get("HF_TOKEN")

DOCS_FOLDER = "/content/drive/MyDrive/CROP_DISEASES"
SUPPORTED_LANGUAGES = ("English", "Hausa")


class Load_KnowledgeBase:
    def __init__(self, folder: Optional[str] = None):
        self.folder = folder or DOCS_FOLDER
        self.kb: Dict[Tuple[str, str], str] = {}

    def load_kb_from_documents(self, folder: Optional[str] = None) -> dict:
        """Reads every .docx file in the folder into a {(crop, disease): facts} dictionary."""
        folder = folder or self.folder
        self.kb = {}

        try:
            import docx  # type: ignore
        except ImportError as exc:
            raise ImportError("python-docx is required to load .docx knowledge files.") from exc

        for filepath in sorted(os.walk(folder)):
            base_dir, _, files = filepath
            for filename in files:
                if not filename.endswith(".docx"):
                    continue

                full_path = os.path.join(base_dir, filename)
                stem = os.path.splitext(os.path.basename(full_path))[0]
                if "_" not in stem:
                    print(f"Skipping '{stem}' - expected format is Crop_Disease")
                    continue

                crop, _, disease = stem.partition("_")
                document = docx.Document(full_path)
                paragraphs = [p.text.strip() for p in document.paragraphs if p.text.strip()]
                facts = " ".join(paragraphs)
                self.kb[(crop, disease)] = facts

        return self.kb


class Retrieval:
    def __init__(self, crop_name: Optional[str] = None, disease_name: Optional[str] = None, docs_folder: Optional[str] = None):
        self.crop_name = crop_name
        self.disease_name = disease_name
        self.docs_folder = docs_folder or DOCS_FOLDER
        self._kb = Load_KnowledgeBase(self.docs_folder).load_kb_from_documents(self.docs_folder)
        self.messages: List[Dict[str, str]] = []
        self.llm = None

    def load_model(self, repo_id: str = "QuantFactory/N-ATLaS-GGUF", filename: str = "N-ATLaS.Q4_K_M.gguf", **kwargs: Any) -> Any:
        try:
            from llama_cpp import Llama  # type: ignore
        except ImportError as exc:
            raise ImportError("llama-cpp-python is required to load the N-ATLaS model.") from exc

        config = {
            "n_ctx": 2048,
            "n_gpu_layers": -1,
            "n_threads": 2,
            "n_batch": 512,
            "verbose": False,
            **kwargs,
        }
        self.llm = Llama.from_pretrained(repo_id=repo_id, filename=filename, **config)
        return self.llm

    def retrieve_facts(self, crop: str, disease: str) -> str:
        """Look up verified treatment facts for a given crop + disease pair."""
        facts = self._kb.get((crop, disease))
        if facts is None:
            return (
                "No verified record found for this specific crop/disease pair in the knowledge base. "
                "Answer using general, widely-accepted plant pathology practice, and clearly tell the "
                "farmer this is general guidance and to confirm with a local agricultural extension officer."
            )
        return facts

    def build_prompt(self, crop: str, disease: str, confidence: float, facts: str, language: str) -> list:
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

    def call_llm(self, messages: list, max_new_tokens: int = 500, retries: int = 1) -> str:
        if self.llm is None:
            self.load_model()

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

            except Exception as exc:
                print(f"LLM call failed (attempt {attempt + 1}/{retries + 1}): {exc}")

        return (
            "Sorry, the recommendation could not be generated right now. "
            "Please try again, or consult your local agricultural extension officer."
        )

    def get_recommendation(self, crop: str, disease: str, confidence: float, language: str) -> str:
        if language not in SUPPORTED_LANGUAGES:
            return (
                f"Language '{language}' is not supported. "
                f"Choose one of: {', '.join(SUPPORTED_LANGUAGES)}."
            )

        facts = self.retrieve_facts(crop, disease)
        messages = self.build_prompt(crop, disease, confidence, facts, language=language)
        return self.call_llm(messages)

    def recommend_from_model_output(self, model_output: Any, disease_name: Optional[str] = None, language: str = "English") -> str:
        if isinstance(model_output, dict):
            crop_name = model_output.get("crop") or model_output.get("label")
            confidence = float(model_output.get("confidence", 0.0))
        elif isinstance(model_output, (list, tuple)) and len(model_output) >= 2:
            crop_name = model_output[0]
            confidence = float(model_output[1])
        else:
            crop_name = getattr(model_output, "crop", None) or getattr(model_output, "label", None)
            confidence = float(getattr(model_output, "confidence", 0.0))

        if not crop_name:
            raise ValueError("No crop name was provided by the model output.")

        disease = disease_name or "Unknown"
        return self.get_recommendation(str(crop_name), disease, confidence, language)

    def recommend_from_model_details(self, details: Iterable[Tuple[str, float, int]], disease_name: Optional[str] = None, language: str = "English") -> List[str]:
        recommendations: List[str] = []
        for crop_name, confidence, _cls_id in details:
            recommendations.append(self.recommend_from_model_output({"crop": crop_name, "confidence": confidence}, disease_name=disease_name, language=language))
        return recommendations

