from main import TREATMENT_KB, generate_bilingual_recommendation
import json

def build_recommendation_cache():
    cache = {}
    total = len(TREATMENT_KB)

    for i, (crop, disease) in enumerate(TREATMENT_KB.keys(), start=1):
        print(f"[{i}/{total}] Generating: {crop} {disease}...")

        # no rush here — this runs once, offline, so take as long as needed
        result = generate_bilingual_recommendation(crop, disease, confidence=0.95, status="diseased")
        cache[f"{crop}_{disease}"] = result

    with open("recommendation_cache.json", "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

    print(f"\nDone. Cached {len(cache)} entries to recommendation_cache.json")

if __name__ == "__main__":
    build_recommendation_cache()