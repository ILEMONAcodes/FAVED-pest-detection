import os
import io
import json
import re
import glob
import base64
import uuid
import threading
import time
import numpy as np
from pathlib import Path

import cv2
import docx
from PIL import Image
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from huggingface_hub import hf_hub_download
from pydantic import BaseModel
from llama_cpp import Llama
from dotenv import load_dotenv
from unified_pipeline import DETECTION_MODES, UnifiedDetector, annotate_image
from knowledge_base import load_markdown_kb, merge_recommendation_with_knowledge
from translation_utils import normalize_translation, parse_translation

app = FastAPI(title="FAVE API", version="1.0.0")
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
MAX_IMAGE_BYTES = 12 * 1024 * 1024
MAX_IMAGE_PIXELS = 25_000_000
MODEL_CACHE_DIR = Path(
    os.getenv("HF_HOME", str(BASE_DIR / ".cache" / "huggingface"))
).expanduser()
if not MODEL_CACHE_DIR.is_absolute():
    MODEL_CACHE_DIR = BASE_DIR / MODEL_CACHE_DIR


def resolve_model_path(
    path_env: str,
    default_path: str,
    repo_env: str,
    default_repo: str = "",
    filename_env: str = "",
) -> str:
    configured_path = Path(os.getenv(path_env, default_path)).expanduser()
    if not configured_path.is_absolute():
        configured_path = BASE_DIR / configured_path
    if configured_path.is_file():
        return str(configured_path)

    repo_id = os.getenv(repo_env, default_repo).strip()
    filename = os.getenv(filename_env, configured_path.name).strip() if filename_env else configured_path.name
    if not repo_id:
        raise FileNotFoundError(
            f"Model file '{configured_path}' is missing. Set {repo_env} and "
            f"{filename_env or 'the model filename environment variable'} to download it from Hugging Face."
        )

    return hf_hub_download(
        repo_id=repo_id,
        filename=filename,
        cache_dir=str(MODEL_CACHE_DIR),
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ).split(",")
        if origin.strip()
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPPORTED_LANGUAGES = ("English", "Hausa", "Igbo", "Yoruba")

# Use a local file when available; otherwise fetch the GGUF from Hugging Face.
llm = Llama(
    model_path=resolve_model_path(
        "LLM_MODEL_PATH",
        "N-ATLaS.Q4_K_M.gguf",
        "LLM_MODEL_REPO_ID",
        default_repo="QuantFactory/N-ATLaS-GGUF",
        filename_env="LLM_MODEL_FILENAME",
    ),
    # Expanded context window from 2048 to 4096 to prevent truncation of full multi-lingual knowledge base entries
    n_ctx=4096,
    n_threads=os.cpu_count() or 4,
    n_batch=512,
    verbose=False,
)

# Run this to load model from its repository
# llm = Llama.from_pretrained(
#     repo_id="QuantFactory/N-ATLaS-GGUF",
#     filename="N-ATLaS.Q4_K_M.gguf",
#     n_ctx=2048,
#     n_threads=4,
#     n_batch=512,
#     verbose=False,
# )

DETECTOR = UnifiedDetector(
    resolve_model_path(
        "PEST_MODEL_PATH",
        "bestpest1.pt",
        "PEST_MODEL_REPO_ID",
        filename_env="PEST_MODEL_FILENAME",
    ),
    resolve_model_path(
        "DETECTION_MODEL_PATH",
        "model.pt",
        "DETECTION_MODEL_REPO_ID",
        filename_env="DETECTION_MODEL_FILENAME",
    ),
    pest_conf=float(os.getenv("PEST_CONFIDENCE_THRESHOLD", "0.25")),
    disease_conf=float(os.getenv("DISEASE_CONFIDENCE_THRESHOLD", "0.5")),
    imgsz=int(os.getenv("YOLO_IMAGE_SIZE", "640")),
    review_conf=float(os.getenv("YOLO_REVIEW_CONFIDENCE", "0.45")),
)

DOCS_FOLDER = Path(os.getenv("DOCUMENTS_FOLDER_PATH", "CROP_DISEASES")).expanduser()
if not DOCS_FOLDER.is_absolute():
    DOCS_FOLDER = BASE_DIR / DOCS_FOLDER
PEST_KB_FOLDER = Path(os.getenv("PEST_KB_FOLDER_PATH", "pests")).expanduser()
if not PEST_KB_FOLDER.is_absolute():
    PEST_KB_FOLDER = BASE_DIR / PEST_KB_FOLDER

# --- Concurrency guards: the loaded model objects are shared across
# request threads once we run jobs in the background. ---
LLM_LOCK = threading.Lock()

# --- Job store for fire-and-poll ---
JOBS: dict[str, dict] = {}
JOBS_LOCK = threading.Lock()
JOB_TTL_SECONDS = 60 * 30  # prune finished jobs after 30 min so JOBS doesn't grow forever


def _prune_old_jobs():
    cutoff = time.time() - JOB_TTL_SECONDS
    with JOBS_LOCK:
        stale = [
            jid for jid, job in JOBS.items()
            if job.get("status") in ("done", "error") and job.get("created_at", 0) < cutoff
        ]
        for jid in stale:
            del JOBS[jid]


def load_kb_from_documents(folder):
    kb = {}
    for filepath in glob.glob(os.path.join(folder, "**", "*.docx"), recursive=True):
        filename = os.path.splitext(os.path.basename(filepath))[0]
        if "_" not in filename:
            print(f"Skipping '{filename}' - expected format is Crop_Disease")
            continue
        crop, _, disease = filename.partition("_")
        document = docx.Document(filepath)
        paragraphs = [p.text.strip() for p in document.paragraphs if p.text.strip()]
        kb[(crop, disease)] = " ".join(paragraphs)
    return kb


TREATMENT_KB = load_kb_from_documents(DOCS_FOLDER)
print(f"Loaded {len(TREATMENT_KB)} knowledge base entries: {list(TREATMENT_KB.keys())}")


PEST_KB = load_markdown_kb(PEST_KB_FOLDER)
print(f"Loaded {len(PEST_KB)} Markdown KB entries: {list(PEST_KB)}")

DISEASE_DOCX_KEYS = {
    "cocoa_black_pod": ("Cocoa", "BlackPod"),
    "cocoa_frosty_pod": ("Cocoa", "FrostyPod"),
    "cocoa_mirid": ("Cocoa", "Mirid"),
    "maize_common_rust": ("Maize", "Common Rust"),
    "maize_gray_leaf_spot": ("Maize", "Gray Leaf Spot"),
}


def retrieve_facts(crop, disease):
    return TREATMENT_KB.get((crop, disease)) or (
        "No verified record found for this specific crop/disease pair in the knowledge base. "
        "Answer using general, widely-accepted plant pathology practice, and clearly tell the "
        "farmer this is general guidance and to confirm with a local agricultural extension officer."
    )


def retrieve_finding_facts(finding: dict) -> tuple[str, bool]:
    label_key = finding["label_key"]
    markdown_entry = PEST_KB.get(label_key)
    if markdown_entry:
        metadata = markdown_entry["metadata"]
        facts = f"{metadata.get('display_name', finding['label'])}\n{markdown_entry['text']}"
        return facts, metadata.get("status", "").lower().startswith("draft")

    docx_key = DISEASE_DOCX_KEYS.get(label_key)
    if docx_key and docx_key in TREATMENT_KB:
        return TREATMENT_KB[docx_key], False
    return (
        "No verified condition-specific entry is available in the knowledge base. "
        "Do not invent treatment or prevention instructions; advise the farmer to ask a local agricultural extension officer.",
        True,
    )


def split_crop_disease(class_name: str):
    crop, _, disease = class_name.strip().partition(" ")
    return crop, disease


def build_prompt(crop, disease, confidence, facts, status, language="English"):
    system_message = (
        "You are an agricultural assistant that returns crop-disease treatment advice for "
        "farmers as a single structured JSON object. "
        f"Write every text value in {language}, but keep the JSON field names exactly as "
        "given, in English. Use ONLY the verified facts provided; do not invent facts not "
        "supported by them. Never name a specific tool, product, or resource (e.g. a "
        "fungicide brand, a spray type) unless it is explicitly stated in the facts given "
        "to you — if no specific product is confirmed, say so plainly and suggest "
        "consulting a local agricultural extension officer instead. Return ONLY the JSON "
        "object — no markdown, no code fences, no commentary before or after it."
    )

    user_message = f"""
A crop disease detection system has produced this result:
- Crop: {crop}
- Detected condition: {disease}
- Model confidence: {confidence:.0%} (for tone/urgency context only — do not restate this number in your answer)

Verified facts about this condition:
\"\"\"{facts}\"\"\"

Using ONLY the facts above, return a JSON object with exactly these fields:
{{
  "pathogen": "scientific name of the causal organism, or empty string if unknown",
  "description": "2-3 sentence summary of what this disease is and its typical symptoms",
  "cause": "1-2 sentence summary of the most likely causes",
  "steps": ["3-5 short imperative treatment steps, most urgent first."],
  "more_about": "2-3 sentences: how it spreads, conditions it thrives in, how quickly it progresses",
  "prevention": ["3-5 short imperative steps to prevent this disease in future seasons"]
}}

Write it in {language}. Respond with ONLY the JSON object above filled in — nothing else.
"""
    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]


def build_translation_prompt(crop, disease, description, cause, steps, more_about, prevention, target_language, pathogen=""):
    """
    A dedicated TRANSLATION prompt, not a "regenerate in a new language" prompt.
    Translating a finished English answer is a much simpler task for this model
    than building structured JSON and switching language at the same time.
    """
    system_message = (
        f"You translate short crop-disease farm advice into {target_language} for a "
        "Nigerian farmer. Keep the meaning exactly the same as the English original — do "
        "not add, remove, or change any facts. Use simple, everyday words a farmer would "
        "understand. Return ONLY a JSON object with these exact fields: \"description\", "
        "\"cause\", \"steps\" (list of strings), \"more_about\", \"prevention\" (list of "
        "strings), and \"pathogen\" (string). Translate descriptive pathogen/source text, "
        "but keep scientific Latin names and specific product/brand names unchanged. Every "
        "other value must be fully written in the target language. No markdown, no commentary, "
        "no extra fields."
    )

    def compact_text(value, limit):
        text = " ".join(str(value).split())
        if len(text) <= limit:
            return text
        shortened = text[:limit].rsplit(" ", 1)[0]
        return f"{shortened.rstrip('.,;:')}…"

    steps_block = "\n".join(
        f"{i + 1}. {compact_text(step, 320)}" for i, step in enumerate(steps[:4])
    )
    prevention_block = "\n".join(
        f"{i + 1}. {compact_text(step, 280)}" for i, step in enumerate(prevention[:3])
    )

    user_message = f"""
Crop: {crop}
Condition: {disease}
Pathogen or disease source:
{compact_text(pathogen, 240)}

Translate the following English farm advice into {target_language}. Do not leave any
part of it in English (except proper product/brand names).

Description:
{compact_text(description, 700)}

Cause:
{compact_text(cause, 400)}

Steps:
{steps_block}

More about:
{compact_text(more_about, 500)}

Prevention:
{prevention_block}

Return ONLY this JSON, fully translated into {target_language}:
{{
  "description": "...",
  "cause": "...",
    "pathogen": "...",
  "steps": ["...", "..."],
  "more_about": "...",
  "prevention": ["...", "..."]
}}
"""
    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]


def call_llm(messages, max_new_tokens=900, retries=2, json_mode=False, temperature=0.1):
    """
    Calls the loaded LLM and returns raw text, with retries so a single bad
    generation doesn't crash the pipeline. Returns "" if every attempt fails
    or returns empty text, so the caller can detect failure and fall back.
    """
    kwargs = dict(temperature=temperature, top_p=0.9, repeat_penalty=1.1)
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    for attempt in range(1, retries + 2):
        try:
            with LLM_LOCK:
                output = llm.create_chat_completion(
                    messages=messages, max_tokens=max_new_tokens, **kwargs,
                )
            content = output["choices"][0]["message"]["content"].strip()
            if content:
                return content
        except Exception as e:
            print(f"[call_llm] Attempt {attempt}/{retries + 1} failed: {e}")

    print(f"[call_llm] All {retries + 1} attempts exhausted, returning empty.")
    return ""


def _fallback_record(status="unknown"):
    return {
        "pathogen": "",
        "description": "We couldn't generate a detailed recommendation right now.",
        "cause": "",
        "steps": ["Please consult your local agricultural extension officer for guidance."],
        "more_about": "",
        "prevention": [],
        "status": status,
    }


def _parse_llm_json(text: str, status: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    if text:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass

    return _fallback_record(status)


def _parse_json_or_none(text: str):
    return parse_translation(text)


def get_recommendation(crop, disease, confidence, status):
    """Always generates live — no cache, no shortcuts."""
    facts = retrieve_facts(crop, disease)

    # Step 1: generate the base answer in English
    english_messages = build_prompt(crop, disease, confidence, facts, status, language="English")
    english_raw = call_llm(english_messages, json_mode=True)
    english_parsed = _parse_llm_json(english_raw, status)
    english_parsed["status"] = status  # enforce, don't trust the model to echo it back correctly

    recommendations = {"English": english_parsed}

    # Step 2: translate the English answer into every other supported language
    for language in SUPPORTED_LANGUAGES:
        if language == "English":
            continue

        translation_messages = build_translation_prompt(
            crop, disease,
            english_parsed.get("description", ""),
            english_parsed.get("cause", ""),
            english_parsed.get("steps", []),
            english_parsed.get("more_about", ""),
            english_parsed.get("prevention", []),
            target_language=language,
            pathogen=english_parsed.get("pathogen", ""),
        )
        translation_raw = call_llm(
            translation_messages,
            max_new_tokens=1600,
            retries=3,
            json_mode=True,
            temperature=0.0,
        )
        translated = normalize_translation(_parse_json_or_none(translation_raw))

        if translated:
            recommendations[language] = {
                "pathogen": translated.get("pathogen") or english_parsed.get("pathogen", ""),
                "description": translated["description"],
                "cause": translated["cause"],
                "steps": translated["steps"],
                "more_about": translated["more_about"],
                "prevention": translated["prevention"],
                "status": status,
            }
        else:
            print(f"Warning: translation to {language} failed; no English copy was stored under that language.")

    return recommendations


def build_combined_prompt(crop: str | None, findings: list[dict], facts: list[dict], language: str):
    findings_text = "\n".join(
        f"- {finding['type']}: {finding['label']} ({finding['crop'] or crop or 'crop'}), "
        f"confidence {finding['max_confidence']:.0%}, detections {finding['count']}"
        for finding in findings
    )
    facts_text = "\n\n".join(
        f"[{item['label_key']} | {item['review_status']}]\n{item['facts']}"
        for item in facts
    )
    system_message = (
        "You are an agricultural assistant writing cautious, practical guidance for smallholder farmers in Nigeria. "
        f"Write every text value in {language}; keep JSON keys in English. Use only the supplied knowledge-base text. "
        "Do not infer pesticide names, doses, products, or action thresholds. If the knowledge is missing or marked draft, "
        "say that it needs local agronomist or extension-officer confirmation. Keep scientific names unchanged. "
        "Return only a JSON object, without markdown."
    )
    user_message = f"""
Detected crop: {crop or 'not certain'}
Detected findings:
{findings_text}

Knowledge-base text:
{facts_text}

Return exactly these fields:
{{
  "pathogen": "scientific names when the knowledge base supplies them, otherwise empty string",
  "description": "briefly summarize the detected pest/disease findings",
  "cause": "describe known causes using only the supplied text",
  "steps": ["3-5 concise, safe actions supported by the supplied text"],
  "more_about": "explain symptoms, spread, or conditions only when supplied",
  "prevention": ["2-5 prevention actions supported by the supplied text"]
}}

Write in {language}. Do not turn a detection into certainty: the confidence is a model score, not a confirmed diagnosis.
"""
    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]


def get_combined_recommendation(
    crop: str | None,
    findings: list[dict],
    review_required: bool,
    language: str = "English",
):
    facts = []
    for finding in findings[:3]:
        finding_facts, needs_review = retrieve_finding_facts(finding)
        review_required = review_required or needs_review
        facts.append(
            {
                "label_key": finding["label_key"],
                "review_status": "draft; agronomist review required" if needs_review else "knowledge base",
                "facts": finding_facts,
            }
        )
    for general_key in ("general_ipm_and_scouting", "general_pesticide_safety", "general_when_to_get_help"):
        general_entry = PEST_KB.get(general_key)
        if general_entry:
            facts.append(
                {
                    "label_key": general_key,
                    "review_status": "draft; agronomist review required",
                    "facts": general_entry["text"],
                }
            )
        review_required = True

    english_raw = call_llm(
        build_combined_prompt(crop, findings, facts, "English"),
        max_new_tokens=550,
        retries=1,
        json_mode=True,
    )
    english_result = _parse_llm_json(english_raw, "diseased")
    english_result = merge_recommendation_with_knowledge(english_result, findings, PEST_KB)
    english_result["status"] = "diseased"
    recommendations = {"English": english_result}
    if language != "English":
        translation_raw = call_llm(
            build_translation_prompt(
                crop or "crop",
            ", ".join(finding["label"] for finding in findings),
                english_result.get("description", ""),
                english_result.get("cause", ""),
                english_result.get("steps", []),
                english_result.get("more_about", ""),
                english_result.get("prevention", []),
                language,
                pathogen=english_result.get("pathogen", ""),
            ),
            max_new_tokens=1400,
            retries=3,
            json_mode=True,
            temperature=0.0,
        )
        translated = normalize_translation(_parse_json_or_none(translation_raw))
        if translated:
            recommendations[language] = {
                "pathogen": translated.get("pathogen") or english_result.get("pathogen", ""),
                "description": translated["description"],
                "cause": translated["cause"],
                "steps": translated["steps"],
                "more_about": translated["more_about"],
                "prevention": translated["prevention"],
                "status": "diseased",
            }
        else:
            print(f"Warning: translation to {language} failed; the frontend can retry it on demand.")
    return recommendations, review_required


def predict_disease(image_bytes: bytes, mode="both"):
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image_bgr = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)
    prediction = DETECTOR.analyze(image_bgr, mode=mode)
    detections = prediction["detections"]
    annotated_frame = annotate_image(image_bgr, detections)

    max_dim = 800
    h, w = annotated_frame.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        annotated_frame = cv2.resize(annotated_frame, (int(w * scale), int(h * scale)))

    success, buffer = cv2.imencode(".jpg", annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
    annotated_b64 = base64.b64encode(buffer).decode("utf-8") if success else None

    if not prediction["recognized"]:
        return {
            "recognized": False,
            "mode": mode,
            "message": (
                "No pest or plant disease was detected. Please make sure the photo is "
                "close, in focus, and well lit, then try again."
            ),
            "annotated_image": annotated_b64,
            "findings": [],
            "warnings": prediction["warnings"],
        }

    primary_finding = prediction["primary_finding"]
    confidence = primary_finding["max_confidence"] if primary_finding else max(
        detection["confidence"] for detection in detections
    )
    disease = primary_finding["label"] if primary_finding else "Healthy"
    status = "healthy" if prediction["status"] == "healthy" else "diseased"

    return {
        **prediction,
        "crop": prediction["crop"] or "Unknown",
        "disease": disease,
        "confidence": round(confidence, 4),
        "detections_count": len(detections),
        "annotated_image": annotated_b64,
        "status": status,
    }


async def read_uploaded_image(file: UploadFile) -> bytes:
    image_bytes = await file.read(MAX_IMAGE_BYTES + 1)
    if not image_bytes:
        raise HTTPException(status_code=400, detail="The uploaded image is empty.")
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image must be 12 MB or smaller.")
    try:
        with Image.open(io.BytesIO(image_bytes)) as image:
            if image.format not in {"JPEG", "PNG", "WEBP"}:
                raise HTTPException(status_code=415, detail="Upload a JPEG, PNG, or WebP image.")
            if image.width * image.height > MAX_IMAGE_PIXELS:
                raise HTTPException(status_code=413, detail="Image dimensions are too large.")
            image.verify()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail="The uploaded file is not a valid image.") from exc
    return image_bytes


def _run_diagnosis_job(job_id: str, image_bytes: bytes, language: str, mode: str):
    try:
        with JOBS_LOCK:
            JOBS[job_id]["stage"] = "vision"
        prediction = predict_disease(image_bytes, mode)

        if prediction["recognized"] and prediction["status"] != "healthy":
            with JOBS_LOCK:
                JOBS[job_id]["stage"] = "recommendation"
            llm_result, review_required = get_combined_recommendation(
                prediction["crop"],
                prediction["findings"],
                bool(prediction["warnings"]),
                language,
            )
            final = {**prediction, "RESULT": llm_result, "review_required": review_required}
        else:
            final = prediction

        with JOBS_LOCK:
            JOBS[job_id] = {
                "status": "done",
                "result": final,
                "created_at": JOBS[job_id]["created_at"],
            }
    except Exception as e:
        print(f"[job {job_id}] failed: {e}")
        with JOBS_LOCK:
            JOBS[job_id] = {
                "status": "error",
                "error": str(e),
                "created_at": JOBS[job_id]["created_at"],
            }


def _run_recommendation_translation(job_id: str, request: "RecommendationTranslationRequest"):
    try:
        with JOBS_LOCK:
            JOBS[job_id]["stage"] = "translation"
        source = request.recommendation
        raw_translation = call_llm(
            build_translation_prompt(
                request.crop,
                request.disease,
                source["description"],
                source["cause"],
                source["steps"],
                source["more_about"],
                source["prevention"],
                request.language,
                pathogen=source.get("pathogen", ""),
            ),
            max_new_tokens=1400,
            retries=3,
            json_mode=True,
            temperature=0.0,
        )
        translated = normalize_translation(_parse_json_or_none(raw_translation))
        if not translated:
            raise ValueError(
                f"A complete {request.language} translation could not be generated. "
                "The model returned invalid or incomplete structured output. Please retry."
            )

        result = {
            "pathogen": translated.get("pathogen") or source.get("pathogen", ""),
            "description": translated["description"],
            "cause": translated.get("cause", ""),
            "steps": translated["steps"],
            "more_about": translated.get("more_about", ""),
            "prevention": translated.get("prevention", []),
            "status": source.get("status", "diseased"),
        }
        with JOBS_LOCK:
            JOBS[job_id] = {
                "status": "done",
                "result": result,
                "created_at": JOBS[job_id]["created_at"],
            }
    except Exception as exc:
        print(f"[translation {job_id}] failed: {exc}")
        with JOBS_LOCK:
            JOBS[job_id] = {
                "status": "error",
                "error": str(exc),
                "created_at": JOBS[job_id]["created_at"],
            }


class DetectionRequest(BaseModel):
    crop: str
    disease: str
    confidence: float
    status: str = "diseased"


class RecommendationTranslationRequest(BaseModel):
    language: str
    crop: str
    disease: str
    recommendation: dict


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    image_bytes = await read_uploaded_image(file)
    return predict_disease(image_bytes)


@app.post("/recommend")
def recommend(req: DetectionRequest):
    return {"RESULT": get_recommendation(req.crop, req.disease, req.confidence, req.status)}


@app.post("/recommend/translate/start")
def start_recommendation_translation(req: RecommendationTranslationRequest):
    if req.language not in SUPPORTED_LANGUAGES or req.language == "English":
        raise HTTPException(status_code=422, detail="Choose Hausa, Igbo, or Yoruba for translation.")

    source = req.recommendation
    required_fields = ("description", "cause", "steps", "more_about", "prevention")
    if any(field not in source for field in required_fields):
        raise HTTPException(status_code=422, detail="The English recommendation is incomplete.")
    if not isinstance(source["steps"], list) or not isinstance(source["prevention"], list):
        raise HTTPException(status_code=422, detail="The English recommendation has invalid list fields.")

    _prune_old_jobs()
    job_id = str(uuid.uuid4())
    with JOBS_LOCK:
        JOBS[job_id] = {"status": "processing", "stage": "queued", "created_at": time.time()}
    thread = threading.Thread(
        target=_run_recommendation_translation,
        args=(job_id, req),
        daemon=True,
    )
    thread.start()
    return {"job_id": job_id}


@app.post("/diagnose/start")
async def diagnose_start(
    file: UploadFile = File(...),
    language: str = Form("English"),
    mode: str = Form("both"),
):
    _prune_old_jobs()
    if language not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=422, detail="Unsupported language.")
    if mode not in DETECTION_MODES:
        raise HTTPException(status_code=422, detail="Unsupported detection mode.")
    image_bytes = await read_uploaded_image(file)

    job_id = str(uuid.uuid4())
    with JOBS_LOCK:
        JOBS[job_id] = {"status": "processing", "stage": "queued", "created_at": time.time()}

    thread = threading.Thread(target=_run_diagnosis_job, args=(job_id, image_bytes, language, mode), daemon=True)
    thread.start()

    return {"job_id": job_id}


@app.get("/diagnose/status/{job_id}")
def diagnose_status(job_id: str):
    with JOBS_LOCK:
        job = JOBS.get(job_id)

    if job is None:
        return {"status": "not_found"}

    # Don't leak created_at to the client, it's internal bookkeeping
    return {k: v for k, v in job.items() if k != "created_at"}



# @app.post("/diagnose")
# async def diagnose(file: UploadFile = File(...)):
#     image_bytes = await file.read()
#     prediction = predict_disease(image_bytes)

#     if (not prediction["recognized"]) or (prediction["status"] == "healthy"):
#         return prediction

#     llm_result = get_recommendation(
#         prediction["crop"], prediction["disease"], prediction["confidence"], prediction["status"]
#     )

#     return {
#         **prediction,
#         "RESULT": llm_result,
#     }
