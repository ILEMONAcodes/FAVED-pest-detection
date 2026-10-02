import os
import io
import json
import re
import glob
import base64

import cv2
import docx
from PIL import Image
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from llama_cpp import Llama
from ultralytics import YOLO

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to your Vercel domain once live
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPPORTED_LANGUAGES = ("English", "Hausa")




llm = Llama(
    model_path=r"C:\Users\user\Desktop\crop-predict\backend\N-ATLaS.Q4_K_M.gguf",  # adjust to your actual file path
    n_ctx=2048,
    n_threads=os.cpu_count() or 4,
    n_batch=512,
    verbose=False,
)

DETECTION_MODEL = YOLO(r"C:\Users\user\Desktop\crop-predict\backend\model.pt")
CONFIDENCE_THRESHOLD = 0.5  # tune based on real-world behavior

DOCS_FOLDER = r"C:\Users\user\Desktop\crop-predict\backend\CROP_DISEASES"


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

# Pre-generated cache — see generate_cache.py. Loaded if present; safe to run without it.
RECOMMENDATION_CACHE = {}
CACHE_PATH = r"C:\Users\user\Desktop\crop-predict\recommendation_cache.json"
if os.path.exists(CACHE_PATH):
    with open(CACHE_PATH, "r", encoding="utf-8") as f:
        RECOMMENDATION_CACHE = json.load(f)
    print(f"Loaded {len(RECOMMENDATION_CACHE)} cached recommendations.")
else:
    print("No recommendation cache found — will generate live for every request.")




def retrieve_facts(crop, disease):
    return TREATMENT_KB.get((crop, disease)) or (
        "No verified record found for this specific crop/disease pair in the knowledge base. "
        "Answer using general, widely-accepted plant pathology practice, and clearly tell the "
        "farmer this is general guidance and to confirm with a local agricultural extension officer."
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




def build_translation_prompt(crop, disease, description, cause, steps, more_about, prevention, target_language):
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
        "strings). Every value must be fully written in the target language — do not leave "
        "any English words in the translation (specific product/brand names can stay as-is "
        "since they are proper names). No markdown, no commentary, no extra fields."
    )

    steps_block = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(steps))
    prevention_block = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(prevention))

    user_message = f"""
Crop: {crop}
Condition: {disease}

Translate the following English farm advice into {target_language}. Do not leave any
part of it in English (except proper product/brand names).

Description:
{description}

Cause:
{cause}

Steps:
{steps_block}

More about:
{more_about}

Prevention:
{prevention_block}

Return ONLY this JSON, fully translated into {target_language}:
{{
  "description": "...",
  "cause": "...",
  "steps": ["...", "..."],
  "more_about": "...",
  "prevention": ["...", "..."]
}}
"""
    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]




def call_llm(messages, max_new_tokens=900, retries=2, json_mode=False):
    """
    Calls the loaded LLM and returns raw text, with retries so a single bad
    generation doesn't crash the pipeline. Returns "" if every attempt fails
    or returns empty text, so the caller can detect failure and fall back.
    """
    kwargs = dict(temperature=0.1, top_p=0.9, repeat_penalty=1.1)
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    for attempt in range(1, retries + 2):
        try:
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
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    return None




def generate_bilingual_recommendation(crop, disease, confidence, status):
    """Always generates live — no cache check. Used by generate_cache.py and
    as the fallback inside get_recommendation() below."""
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
        )
        translation_raw = call_llm(translation_messages, json_mode=True)
        translated = _parse_json_or_none(translation_raw)

        if translated and translated.get("description") and translated.get("steps"):
            recommendations[language] = {
                "pathogen": english_parsed.get("pathogen", ""),  # scientific names stay as-is
                "description": translated.get("description", english_parsed["description"]),
                "cause": translated.get("cause", english_parsed.get("cause", "")),
                "steps": translated.get("steps", english_parsed.get("steps", [])),
                "more_about": translated.get("more_about", english_parsed.get("more_about", "")),
                "prevention": translated.get("prevention", english_parsed.get("prevention", [])),
                "status": status,
            }
        else:
            print(f"Warning: translation to {language} failed — using English text as fallback.")
            recommendations[language] = {**english_parsed}

    return recommendations


def get_recommendation(crop, disease, confidence, status):
    """Cache-first lookup; falls back to live bilingual generation for unseen classes."""
    cache_key = f"{crop}_{disease}"
    cached = RECOMMENDATION_CACHE.get(cache_key)
    if cached is not None:
        return cached

    return generate_bilingual_recommendation(crop, disease, confidence, status)




def predict_disease(image_bytes: bytes):
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    results = DETECTION_MODEL.predict(image, conf=CONFIDENCE_THRESHOLD, verbose=False)
    result = results[0]
    boxes = result.boxes

    annotated_frame = result.plot()

    max_dim = 800
    h, w = annotated_frame.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        annotated_frame = cv2.resize(annotated_frame, (int(w * scale), int(h * scale)))

    success, buffer = cv2.imencode(".jpg", annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
    annotated_b64 = base64.b64encode(buffer).decode("utf-8") if success else None

    if len(boxes) == 0:
        return {
            "recognized": False,
            "message": (
                "No plant disease was recognized in this image. Please make sure the "
                "photo clearly shows a plant leaf, is in focus, well lit, and fills "
                "most of the frame, then try again."
            ),
            "annotated_image": annotated_b64,
        }

    best_idx = int(boxes.conf.argmax().item())
    class_id = int(boxes.cls[best_idx].item())
    confidence = float(boxes.conf[best_idx].item())
    class_name = result.names[class_id]

    crop, disease = split_crop_disease(class_name)
    disease = disease or "Unknown"

    status = "healthy" if "healthy" in disease.lower() else "diseased"

    return {
        "recognized": True,
        "crop": crop,
        "disease": disease,
        "confidence": round(confidence, 4),
        "detections_count": len(boxes),
        "annotated_image": annotated_b64,
        "status": status,
    }




class DetectionRequest(BaseModel):
    crop: str
    disease: str
    confidence: float
    status: str = "diseased"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    image_bytes = await file.read()
    return predict_disease(image_bytes)


@app.post("/recommend")
def recommend(req: DetectionRequest):
    return {"RESULT": get_recommendation(req.crop, req.disease, req.confidence, req.status)}


@app.post("/diagnose")
async def diagnose(file: UploadFile = File(...)):
    image_bytes = await file.read()
    prediction = predict_disease(image_bytes)

    if (not prediction["recognized"]) or (prediction["status"] == "healthy"):
        return prediction

    llm_result = get_recommendation(
        prediction["crop"], prediction["disease"], prediction["confidence"], prediction["status"]
    )

    return {
        **prediction,
        "RESULT": llm_result,
    }