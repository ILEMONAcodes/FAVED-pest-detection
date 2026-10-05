# FAVE: Farm AI Vision and Recommendation for Early Disease and Pest Detection

FAVE is an improved, research-stage crop-screening application for smallholder farmers. It combines photo-based pest and disease detection for **cocoa and maize** with cautious, knowledge-base-grounded guidance. The web interface supports **English, Hausa, Igbo, and Yoruba**.

**Important:** FAVE is a screening and educational aid, not a confirmed diagnosis or a replacement for an agronomist or agricultural extension officer. Model and language output can be wrong. Verify important decisions locally, especially before applying any treatment.

## Project Description

A farmer uploads or captures one crop photo, chooses **Crop disease**, **Pest**, or **Pest + disease**, and receives detected findings with confidence scores and practical follow-up guidance. The vision system uses separate pest and disease models; the selected mode avoids running an unneeded detector. The application maps detections to local knowledge-base records and asks the N-ATLaS language model to produce guidance. Non-English recommendations are generated from the English advice through a separate translation step.

This is an improved version of the earlier project: the frontend and backend are separated, the API proxy is lightweight, inference is deployed independently, detection mode is selectable, recommendations are grounded in local records, and translations can be retried rather than silently shown as English.

## Deployment Stack

The production architecture uses three services:

1. **Vercel** serves the Vite + React frontend.
2. **Render** serves a lightweight FastAPI proxy. It accepts frontend requests and forwards them to Modal; it does not load the ML models.
3. **Modal** serves the inference API, YOLO models, N-ATLaS, and the knowledge-base-backed recommendation pipeline. Model files are mounted from the persistent `faved-models` Modal Volume at `/models`.

Request flow:

```text
Browser (Vercel)
  -> Render API proxy
    -> Modal inference API
      -> selected YOLO detector(s)
      -> knowledge base + N-ATLaS
    <- diagnosis / translation job result
  <- result displayed by the frontend
```

The `app.py` module is the lightweight Render proxy. `inference_app.py` is the model-serving FastAPI application used by `modal_app.py`. Do not deploy `inference_app.py` on Render using the lightweight `requirements.txt`; it requires the heavier packages in `modal-requirements.txt`.

## Repository Layout

```text
frontend/                    Vite + React + TypeScript user interface
backend/app.py               Lightweight Render API proxy
backend/inference_app.py     Modal inference API and recommendation jobs
backend/modal_app.py         Modal image, model volume, and ASGI deployment
backend/requirements.txt     Lightweight Render proxy dependencies
backend/modal-requirements.txt
                             ML dependencies installed by Modal
backend/unified_pipeline.py  Pest/disease model selection and result merging
backend/knowledge_base.py   Structured Markdown knowledge-base helpers
backend/translation_utils.py
                             Translation JSON parsing and completeness checks
backend/CROP_DISEASES/       Disease reference documents
backend/pests/               Pest and general IPM Markdown records
backend/tests/               Focused backend tests
project_files/               Research code, notebooks, and project documents
```

Model weights (`*.pt`, `*.gguf`) and local `.env` files are intentionally excluded from Git. The production Modal volume currently expects:

```text
/models/bestpest1.pt
/models/model.pt
/models/N-ATLaS.Q4_K_M.gguf
```

## API Flow

The frontend uses asynchronous jobs because model startup and generation can take time:

- `POST /diagnose/start`: accepts an image, language, and detection mode; returns a job ID.
- `GET /diagnose/status/{job_id}`: polls diagnosis or translation job status.
- `POST /recommend/translate/start`: requests a translation of an existing English recommendation.
- `POST /predict`: direct image prediction endpoint, mainly for API use.
- `GET /health`: service health check.

The Render proxy forwards these routes to Modal using `MODAL_URL`. The Vercel frontend must point `VITE_API_URL` to the Render service URL, not directly to Modal.

## Local Development

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Set `VITE_API_URL` to a running Render proxy or another reachable proxy. `frontend/.env.example` is for local defaults; production values belong in the Vercel project environment settings.

### Render Proxy

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
MODAL_URL=https://ilemonacodes--faved-api-serve.modal.run \
CORS_ORIGINS=http://localhost:5173 \
uvicorn app:app --host 127.0.0.1 --port 8000
```

Alternatively, create `backend/.env` from `backend/.env.example` and set the same variables there. Do not commit `.env` files or tokens.

### Focused Checks

```bash
(cd frontend && npm run build)
(cd backend && PYTHONPATH=. python -m unittest discover -s tests -p 'test_translation_utils.py' -v)
```

The full detector test suite needs the ML dependencies used by Modal. The Render proxy intentionally does not install Torch, Ultralytics, or OpenCV.

## Deployment

### Vercel: Frontend

Import the repository into Vercel and configure:

- Root directory: `frontend`
- Build command: `npm run build`
- Output directory: `dist`
- Environment variable: `VITE_API_URL=https://<your-render-service>.onrender.com`

The production frontend currently identified for this deployment is `https://faved-pest-detection.vercel.app/`.

### Render: Proxy API

Create a Docker-based Web Service using `backend/Dockerfile` and set the service root directory to `backend`. The image installs only the lightweight dependencies in `backend/requirements.txt` and binds to Render's `$PORT`.

Configure the Render service environment:

```text
MODAL_URL=https://ilemonacodes--faved-api-serve.modal.run
CORS_ORIGINS=https://faved-pest-detection.vercel.app
PROXY_TIMEOUT_SECONDS=60
```

Use the actual Render service URL as the frontend's `VITE_API_URL`. Configure the matching Vercel origin in Render CORS if the frontend domain changes.

### Modal: Inference API

The Modal app definition is `backend/modal_app.py`. It installs `backend/modal-requirements.txt`, mounts the `faved-models` volume at `/models`, and packages the disease/pest knowledge files. Deploy from the repository root:

```bash
FRONTEND_ORIGIN=https://faved-pest-detection.vercel.app \
  ./.venv/bin/python -m modal deploy backend/modal_app.py
```

The deployed endpoint used by this project is:

```text
https://ilemonacodes--faved-api-serve.modal.run
```

The model volume must contain the three files listed above. Since the current deployment stores the model files in that volume, it does not need a Hugging Face token to load them. If model downloading from a private Hugging Face repository is configured in the future, use a Modal Secret; never put access tokens in source files, README examples, or committed `.env` files.

The Modal function needs enough memory and CPU for the YOLO weights and 4.6 GB quantized language model. The image currently allocates 4 CPUs and 16 GB RAM. Modal may scale down after inactivity, so the first request can have a cold-start delay.

## Language and Model Limitations

- **Four interface/output languages:** English, Hausa, Igbo, and Yoruba. Other languages and dialects are not supported by the current UI/API configuration.
- **Translation quality varies:** Hausa, Igbo, and Yoruba content is generated by N-ATLaS, not written or verified by professional translators. Fluency, spelling, terminology, and meaning can vary across languages and requests. Do not treat a successful response as proof of linguistic correctness.
- **Translations can fail or be incomplete:** outputs are parsed and checked for required advice sections. If generation is invalid or incomplete, the UI may remain in a translating state until polling completes, or show a retry option after failure. Retrying may produce a different result; it is not a guarantee.
- **Advice is generated in English then translated** when the user selects a non-English language. Translation is a separate model call and adds latency and another possible failure point.
- **Language labels do not guarantee equal model competence.** N-ATLaS may perform unevenly across Hausa, Igbo, and Yoruba, particularly for long technical advice. Fluent-speaker and agronomist review is needed before relying on translations in the field.
- **Coverage is limited to the classes represented by the shipped pest and disease weights and mappings**, currently targeting cocoa and maize. Unknown crops, pests, diseases, mixed symptoms, uncommon cultivars, and out-of-distribution images may be missed or mislabeled.
- **A confidence score is not diagnostic certainty.** Lighting, focus, distance, background, growth stage, symptom similarity, image quality, and training-data coverage affect predictions. Multiple findings may be merged by label mapping.
- **Boxes are detections, not segmentation.** They do not precisely trace affected tissue or measure disease severity.
- **One image per diagnosis.** There is no batch workflow, temporal tracking, farm history, or offline mode.
- **Recommendations are bounded by the local knowledge base and prompt.** A record may be missing, incomplete, or marked draft. Draft entries require agronomist review. Local registration, product availability, label instructions, crop stage, and regional conditions may differ.
- **No pesticide prescription:** the system is instructed not to invent product names, doses, or action thresholds. Follow locally approved labels and consult an extension officer.
- **Not emergency or autonomous decision support.** It does not replace scouting, laboratory confirmation, professional advice, or local regulatory guidance.
- **Infrastructure adds latency and failure modes.** Modal cold starts, model initialization, serialized language-model access, proxy/network timeouts, service restarts, and in-memory job state can delay or interrupt a request. A restart can lose a job that was still being processed.
- **Requires internet access** between the browser, Render, and Modal. Availability and cost depend on the hosting providers and selected service plans.

Treat outputs as preliminary guidance. Confirm uncertain findings with an agricultural extension officer, and have local-language advice reviewed by fluent speakers and subject-matter experts before operational use.

## Evaluation

The original disease-model evaluation recorded the following scores on its held-out test set:

| Metric | Reported score |
| --- | ---: |
| Precision | 86% |
| Recall | 86% |
| mAP@50 | 92% |
| mAP@50–95 | 74% |

These are model-evaluation metrics for that dataset and test setup, not guarantees of real-world accuracy. They do not measure translation quality, recommendation safety, or performance on every farm, region, device, crop variety, or field condition. See the training/evaluation notebook in `backend/` for experiment details.

## Research and Demo Materials

Research notebooks, training materials, and project documents are in `backend/` and `project_files/`. The web demo is available at [faved-pest-detection.vercel.app](https://faved-pest-detection.vercel.app/). Model outputs should still be interpreted with the limitations above.

## Project Teams and Contributions

### Team 1: Dataset and Preprocessing

- **Prosper Ekechukwu, Team Lead**
- Banmen Akuso
- Chigozirim Oduche

Responsibilities included identifying target pest classes, sourcing and cleaning datasets, annotating images where needed, preparing YOLO-format data, creating train/validation/test splits, applying augmentation, addressing class imbalance, and documenting sources and preparation.

**Main output:** a clean, structured, YOLO-ready pest dataset.

### Team 2: YOLO Model Training

- **Muhammad Omeiza, Team Lead**
- Ekene Nwakonobi
- Farhan Mashood

Responsibilities included selecting the YOLO model, setting up transfer learning and training, experimenting with hyperparameters, comparing runs, managing checkpoints, selecting the best model, and testing it on new images.

**Main output:** a trained pest-detection model, such as `best.pt`.

### Team 3: Evaluation, Integration, and Existing Disease Model

- **Oluwatonilola Sodimu, Team Lead**
- Dan Cornelius
- Chukwudi Iroegbulem
- Solomon Samuel

Responsibilities included evaluating the trained model with precision, recall, mAP@50, mAP@50–95, and F1-score; analyzing errors, false positives, and false negatives; testing unseen images; reviewing the existing FAVED disease model; integrating pest and disease detection; unifying outputs; and preparing model results for the knowledge-grounded recommendation pipeline.

**Main output:** a tested pest/disease pipeline that supplies unified findings to the recommendation system.

## Version Note

This repository is an improved engineering and deployment version of the FAVE crop-screening project. It adds a selectable detection pipeline, separated frontend/proxy/inference services, knowledge-base-backed recommendations, and explicit translation failure handling. Research notebooks and project materials remain available for context; this README describes the current application architecture and its limitations.





