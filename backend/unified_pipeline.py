"""Unified FAVE pest and disease analysis: one image in, one JSON result out."""
import os, json
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
import numpy as np, cv2
from ultralytics import YOLO

PEST_META = {  # model label -> (crop, knowledge-base key)
    "Large cutworm": ("maize", "large_cutworm"), "Yellow cutworm": ("maize", "yellow_cutworm"),
    "Corn borer": ("maize", "corn_borer"), "Army worm": ("maize", "army_worm"), "Aphids": ("maize", "maize_aphids"),
    "Pod-borer": ("cocoa", "cocoa_pod_borer"), "Weevil": ("cocoa", "cocoa_weevil"),
    "Mirid-bug": ("cocoa", "cocoa_mirid"), "Mealybug": ("cocoa", "cocoa_mealybug"),
}
_reg = os.getenv("PEST_REGISTRY_PATH")            # optional: extra crops added via class_registry.json
if _reg and os.path.exists(_reg):
    PEST_META.update({k: tuple(v) for k, v in json.load(open(_reg)).get("pest_meta", {}).items()})

DISEASE_RULES = [("black", "cocoa", "cocoa_black_pod", "disease"), ("frosty", "cocoa", "cocoa_frosty_pod", "disease"),
                 ("mirid", "cocoa", "cocoa_mirid", "pest"), ("rust", "maize", "maize_common_rust", "disease"),
                 ("gray", "maize", "maize_gray_leaf_spot", "disease"), ("grey", "maize", "maize_gray_leaf_spot", "disease")]
DISEASE_OVERRIDES = {}   # exact model class name -> (type, crop, label_key)
DETECTION_MODES = ("crop", "pest", "both")

def classify_disease_name(name):
    if name in DISEASE_OVERRIDES: return DISEASE_OVERRIDES[name]
    n = name.lower().replace("_", " ").replace("-", " ")
    if "healthy" in n:
        return ("healthy", "cocoa" if "cocoa" in n else "maize" if ("maize" in n or "corn" in n) else None, "healthy")
    for kw, crop, key, typ in DISEASE_RULES:
        if kw in n: return (typ, crop, key)
    return ("disease", None, n.strip().replace(" ", "_"))

class UnifiedDetector:
    def __init__(self, pest_model_path, disease_model_path=None, pest_conf=0.25, disease_conf=0.25, imgsz=640, review_conf=0.45):
        self.pest_model = YOLO(pest_model_path)
        self.disease_model = YOLO(disease_model_path) if disease_model_path else None
        self._pest_lock = Lock()
        self._disease_lock = Lock()
        self.pest_conf, self.disease_conf, self.imgsz, self.review_conf = pest_conf, disease_conf, imgsz, review_conf

    @classmethod
    def from_env(cls, **kw):
        return cls(os.environ["PEST_MODEL_PATH"], os.getenv("DETECTION_MODEL_PATH"), **kw)

    def _detections(self, model, source, image):
        conf = self.pest_conf if source == "pest_model" else self.disease_conf
        lock = self._pest_lock if source == "pest_model" else self._disease_lock
        with lock:
            r = model.predict(image, conf=conf, imgsz=self.imgsz, iou=0.6, verbose=False)[0]
        h, w = r.orig_shape; out = []
        def meta(name):
            if source == "pest_model":
                crop, key = PEST_META.get(name, (None, name.lower().replace(" ", "_"))); return "pest", crop, key
            return classify_disease_name(name)
        if r.boxes is not None and len(r.boxes):
            for b in r.boxes:
                class_id = b.cls[0].item() if hasattr(b.cls[0], "item") else b.cls[0]
                name = model.names[int(class_id)]; typ, crop, key = meta(name)
                coordinates = b.xyxy[0].tolist() if hasattr(b.xyxy[0], "tolist") else b.xyxy[0]
                x1, y1, x2, y2 = [float(v) for v in coordinates]
                confidence = b.conf[0].item() if hasattr(b.conf[0], "item") else b.conf[0]
                out.append(dict(type=typ, label=name, label_key=key, crop=crop, confidence=round(float(confidence), 4),
                                bbox_xyxy=[round(v, 1) for v in (x1, y1, x2, y2)],
                                bbox_xywhn=[round(v, 4) for v in ((x1+x2)/2/w, (y1+y2)/2/h, (x2-x1)/w, (y2-y1)/h)], source_model=source))
        elif getattr(r, "probs", None) is not None:      # classifier-style disease model
            c = int(r.probs.top1); name = model.names[c]; typ, crop, key = meta(name)
            out.append(dict(type=typ, label=name, label_key=key, crop=crop, confidence=round(float(r.probs.top1conf), 4),
                            bbox_xyxy=None, bbox_xywhn=None, source_model=source))
        return out

    def analyze(self, image, language="en", mode="both"):
        if mode not in DETECTION_MODES:
            raise ValueError(f"Unsupported detection mode: {mode}")
        models = []
        if mode in ("pest", "both"):
            models.append((self.pest_model, "pest_model"))
        if mode in ("crop", "both") and self.disease_model is not None:
            models.append((self.disease_model, "disease_model"))
        if not models:
            raise ValueError(f"No model is configured for detection mode: {mode}")
        with ThreadPoolExecutor(max_workers=len(models)) as executor:
            results = list(executor.map(lambda item: self._detections(item[0], item[1], image), models))
        dets = [detection for model_detections in results for detection in model_detections]
        findings = {}
        for d in dets:
            if d["type"] == "healthy": continue
            f = findings.setdefault(d["label_key"], dict(type=d["type"], label=d["label"], label_key=d["label_key"], crop=d["crop"],
                                                         count=0, max_confidence=0.0, evidence=set()))
            f["count"] += 1; f["max_confidence"] = max(f["max_confidence"], d["confidence"]); f["evidence"].add(d["source_model"])
        fl = sorted(findings.values(), key=lambda f: -f["max_confidence"])
        for f in fl: f["evidence"] = sorted(f["evidence"])
        votes = {}
        for d in dets:
            if d["crop"]: votes[d["crop"]] = votes.get(d["crop"], 0) + d["confidence"]
        crop = max(votes, key=votes.get) if votes else None
        pests = [f for f in fl if f["type"] == "pest"]; dis = [f for f in fl if f["type"] == "disease"]
        healthy = any(d["type"] == "healthy" for d in dets)
        status = "pest_and_disease" if pests and dis else "pest" if pests else "disease" if dis else "healthy" if healthy else "no_detection"
        warnings = []
        if status == "no_detection": warnings.append("Nothing detected. The crop or pest may be outside coverage, or the photo is unclear. Retake a close, well-lit photo.")
        elif fl and fl[0]["max_confidence"] < self.review_conf: warnings.append("Low confidence. Retake the photo (close-up, good light, one affected area) before acting.")
        queries = [dict(text=f"{f['label']} on {f['crop'] or crop or 'crop'}: how to identify, control and prevent it for smallholder farmers in Nigeria",
                        filters=dict(crop=f["crop"] or crop, category=f["type"], label_key=f["label_key"]), language=language) for f in fl[:3]]
        return dict(schema_version="1.0", mode=mode, crop=crop, status=status, primary_finding=(fl[0] if fl else None),
                    n_pests=len(pests), n_diseases=len(dis), findings=fl, detections=dets, warnings=warnings,
                    recognized=status != "no_detection", rag=dict(language=language, queries=queries))

def annotate_image(image, detections):
    im = image.copy()
    for d in detections:
        if d["bbox_xyxy"] is None: continue
        x1, y1, x2, y2 = map(int, d["bbox_xyxy"]); col = (0, 0, 255) if d["type"] == "pest" else (0, 140, 255) if d["type"] == "disease" else (0, 200, 0)
        cv2.rectangle(im, (x1, y1), (x2, y2), col, 3); cv2.putText(im, f"{d['type']}:{d['label']} {d['confidence']:.2f}", (x1, max(20, y1-6)), 0, 0.7, col, 2)
    return im

def annotate(image_path, result):
    return annotate_image(cv2.imread(image_path), result["detections"])

if __name__ == "__main__":
    import sys
    print(json.dumps(UnifiedDetector.from_env().analyze(sys.argv[1]), indent=2))
