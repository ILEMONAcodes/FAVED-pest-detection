from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from llama_cpp import Llama
import glob, os, docx

from ultralytics import YOLO
from PIL import Image
from fastapi import UploadFile, File
import io

import cv2
import base64

import json
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to your Vercel domain once live
    allow_methods=["*"],
    allow_headers=["*"],
)




def build_recommendation_cache():
    cache = {}
    for (crop, disease), facts in TREATMENT_KB.items():
        print(f"Generating: {crop} {disease}...")
        messages = build_prompt(crop, disease, confidence=0.95, facts=facts, status="diseased")
        result = call_llm(messages, max_new_tokens=1200)  # no rush here, run it once, take your time
        cache[f"{crop}_{disease}"] = result

    with open("recommendation_cache.json", "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

    print(f"Done. Cached {len(cache)} entries.")

if __name__ == "__main__":
    build_recommendation_cache()
    
    
    

# with open("recommendation_cache.json", "r", encoding="utf-8") as f:
#    RECOMMENDATION_CACHE = json.load(f)

# --- load model ONCE at startup, not per-request ---
llm = Llama.from_pretrained(
    repo_id="QuantFactory/N-ATLaS-GGUF",
    filename="N-ATLaS.Q4_K_M.gguf",
    n_ctx=2048,
    n_threads=4,
    n_batch=512,
    verbose=False,
)



# --- load knowledge base from docx files shipped in the repo ---
DOCS_FOLDER = "CROP_DISEASES"

def load_kb_from_documents(folder):
    kb = {}
    for filepath in glob.glob(os.path.join(folder, "**", "*.docx"), recursive=True):
        filename = os.path.splitext(os.path.basename(filepath))[0]
        if "_" not in filename:
            continue
        crop, _, disease = filename.partition("_")
        document = docx.Document(filepath)
        paragraphs = [p.text.strip() for p in document.paragraphs if p.text.strip()]
        kb[(crop, disease)] = " ".join(paragraphs)
    return kb

TREATMENT_KB = load_kb_from_documents(DOCS_FOLDER)

def retrieve_facts(crop, disease):
    return TREATMENT_KB.get((crop, disease)) or (
        "No verified record found for this specific crop/disease pair in the knowledge base. "
        "Answer using general, widely-accepted plant pathology practice, and clearly tell the "
        "farmer this is general guidance and to confirm with a local agricultural extension officer."
    )
    
def split_crop_disease(class_name: str):
    crop, _, disease = class_name.strip().partition(" ")
    return crop, disease

def build_prompt(crop, disease, confidence, facts, status):   
   
    system_message = (
        "You are an agricultural assistant that writes short, clear, practical treatment "
        f"advice for farmers. Reply in both English and Hausa, one after the other. Respond with ONLY a valid JSON object with two keys: English and Hausa, where their contents are exactly the same just in the respective languages "
        "matching the exact schema given — no markdown, no code fences, no commentary before "
        "or after the JSON. Use ONLY the verified facts provided; do not invent facts not "
        "supported by them. If the facts don't cover something (e.g. the pathogen's scientific "
        "name), make a clearly-labeled best-effort general answer rather than fabricating a "
        "precise fact."
    )

   
    user_message = f"""
A crop disease detection system has produced this result:
- Crop: {crop}
- Detected condition: {disease}
- Model confidence: {confidence:.0%}

Verified facts about this condition:
\"\"\"{facts}\"\"\"

Respond with ONLY a valid JSON object with exactly this structure — two top-level keys,
"English" and "Hausa", each containing the same fields translated into that language:
{{
  "English": {{
    "pathogen": "scientific name of the causal organism, or empty string if unknown",
    "description": "2-3 sentence summary of what this disease is and its typical symptoms",
    "cause": "1-2 sentence summary of what are the most likely causes of this disease",
    "steps": ["3-5 short imperative treatment steps, most urgent first"],
    "more_about": "2-3 sentences with additional detail: how it spreads, conditions it thrives in, how quickly it progresses",
    "prevention": ["3-5 short imperative steps to prevent this disease in future seasons"],
    "status": "{status}"
  }},
  "Hausa": {{
    "pathogen": "scientific name of the causal organism, or empty string if unknown",
    "description": "2-3 sentence summary of what this disease is and its typical symptoms",
    "cause": "1-2 sentence summary of what are the most likely causes of this disease",
    "steps": ["3-5 short imperative treatment steps, most urgent first"],
    "more_about": "2-3 sentences with additional detail: how it spreads, conditions it thrives in, how quickly it progresses",
    "prevention": ["3-5 short imperative steps to prevent this disease in future seasons"],
    "status": "{status}"
  }}
}}
"""

    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]

def call_llm(messages, max_new_tokens=900):
    output = llm.create_chat_completion(
        messages=messages, max_tokens=max_new_tokens,
        temperature=0.1, top_p=0.9, repeat_penalty=1.1,
    )
    
    raw = output["choices"][0]["message"]["content"].strip()
    
     # models sometimes wrap JSON in ```json fences despite instructions — strip if present
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
    
    try:
       return json.loads(raw)
    except json.JSONDecodeError:
       fallback = {"pathogen": "", "description": raw[:300], "cause": "", "steps": [], "more_about": "", "prevention": [], "status": ""}
    return {"English": fallback, "Hausa": fallback}


    

SUPPORTED_LANGUAGES = ("English", "Hausa")

class DetectionRequest(BaseModel):
    crop: str
    disease: str
    confidence: float
    language: str = "English"
    
    
    
    

# --- load detection model ONCE at startup, alongside the LLM ---
DETECTION_MODEL = YOLO("best.pt")
CONFIDENCE_THRESHOLD = 0.6  # tune this based on your model's real-world behavior

def predict_disease(image_bytes: bytes):
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    results = DETECTION_MODEL.predict(image, conf=CONFIDENCE_THRESHOLD, verbose=False)
    result = results[0]
    boxes = result.boxes
    
     # result.plot() draws the boxes/labels and returns a BGR numpy array
    annotated_frame = result.plot()

    # optional: resize so the payload isn't huge over a mobile connection / ngrok
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
            "annotated_image": annotated_b64
        }

    # take the single most confident detection as the primary diagnosis
    best_idx = int(boxes.conf.argmax().item())
    class_id = int(boxes.cls[best_idx].item())
    confidence = float(boxes.conf[best_idx].item())
    class_name = result.names[class_id]  
        
    crop, disease = split_crop_disease(class_name)
    if not disease:
       disease = "Unknown"

        
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



@app.post("/recommend")
def recommend(req: DetectionRequest):
   #  if req.language not in SUPPORTED_LANGUAGES:
   #      return {"error": f"Language must be one of {SUPPORTED_LANGUAGES}"}
    facts = retrieve_facts(req.crop, req.disease)
    messages = build_prompt(req.crop, req.disease, req.confidence, facts, req.status)
    return {"RESULT": call_llm(messages)}

@app.get("/health")
def health():
    return {"status": "ok"}
 
@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    image_bytes = await file.read()
    return predict_disease(image_bytes)
 
 

@app.post("/diagnose")
async def diagnose(file: UploadFile = File(...)):
    image_bytes = await file.read()
    prediction = predict_disease(image_bytes)

    if (not prediction["recognized"]) or (prediction['status'] == "healthy"):
        return prediction  # nothing to recommend on, e.g. no leaf detected

    facts = retrieve_facts(prediction["crop"], prediction["disease"])
    messages = build_prompt(
        prediction["crop"], prediction["disease"], prediction["confidence"], facts, prediction['status']
    )
    llm_result = call_llm(messages)

    return {
        **prediction,       # crop, disease, confidence, status, annotated_image, detections_count
        "RESULT": llm_result,  # your English/Hausa recommendation object
    }



# @app.post("/diagnose")
# async def diagnose(file: UploadFile = File(...)):
    image_bytes = await file.read()
    prediction = predict_disease(image_bytes)

    if not prediction["recognized"]:
        return prediction

    cache_key = f"{prediction['crop']}_{prediction['disease']}"
    llm_result = RECOMMENDATION_CACHE.get(cache_key)

    if llm_result is None:
        # unseen class — fall back to live generation as a safety net
        facts = retrieve_facts(prediction["crop"], prediction["disease"])
        messages = build_prompt(prediction["crop"], prediction["disease"], prediction["confidence"], facts, prediction["status"])
        llm_result = call_llm(messages)

    return {
        **prediction,
        "RESULT": llm_result,
    }