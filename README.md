# FAVE: Farm AI Vision and Recommendation for Early Disease and Pest Detection

FAVE helps smallholder farmers identify crop pests and diseases from a single photo and get plain-language, cautious prevention and response guidance in **English, Hausa, Igbo, or Yoruba**. A farmer photographs an affected cocoa or maize crop; pest and disease vision models analyze it, and a language model grounds practical guidance in the local knowledge base.

The project pairs two systems:

- **Frontend** : a React + TypeScript web app for capturing/uploading photos and displaying diagnosis results.
- **Backend** : a Python service that runs the vision model and language model locally, with an optional ngrok tunnel for remote access. Two versions exist (see [Backend Versions](#backend-versions) below).

---

## Table of Contents

- [How It Works](#how-it-works)
- [Project Structure](#project-structure)
- [Backend Versions](#backend-versions)
    - [`app2.py` — Cached Backend](#apppy--cached-backend)
    - [`app.py` — Live Backend](#app2py--live-backend)
- [Tech Stack](#tech-stack)
- [Model Results](#model-results)
- [Getting Started](#getting-started)
    - [Frontend Setup](#frontend-setup)
    - [Backend Setup](#backend-setup)
    - [Environment Variables](#environment-variables)
    - [Generating the Recommendation Cache Ahead of Time](#generating-the-recommendation-cache-ahead-of-time)
    - [Connecting Frontend to Backend](#connecting-frontend-to-backend)
- [Project Scope & Limitations](#project-scope--limitations)
- [Contributors](#contributors)

---

## How It Works

The full pipeline is: **photo in → diagnosis + recommendation out**, in four hand-offs:

1. **Farmer takes a photo** of the affected leaf (maize) or pod/crop (cocoa).
2. **Vision models read it in parallel** one YOLO11 model detects pests and the existing FAVED YOLO model detects disease; the backend merges overlapping labels such as Cocoa Mirid into one finding.
3. **Language model explains it** a second model takes that raw label and writes it up the way a human adviser would: cause, treatment, and prevention.
4. **Farmer gets the answer** clear guidance delivered in the selected language.

On the frontend, this maps to `DataContext`:

```
uploadImage()        → user selects/captures a photo, stored as an object URL
DiagnoseCrop()        → sends the photo to the backend and awaits a diagnosis
  ├─ startDiagnosisJob()  → POST the image, backend returns a job_id
  └─ pollDiagnosisJob()   → polls job status every few seconds until "done"
setResult()            → diagnosis stored in context
navigate("/result")    → user is routed to the results page
```

The frontend is written to talk to a **job-based, asynchronous** backend (start a job, then poll for its status), which is how the live model (`app.py`) is designed to work, since real inference takes longer than an instant request/response cycle. Diagnosis generates the English recommendation and the selected language. When a farmer changes language after diagnosis, the frontend starts `/recommend/translate/start` and polls `/diagnose/status/{job_id}`; it shows a localized translation-in-progress or retry message instead of presenting English as translated text.

---

## Project Structure

```
FAVE Farm AI Vision and Recommendation for Early Disease and Pest Detection/
├── frontend/              # Vite + React + TypeScript app (deploy to Vercel)
│   ├── src/
│   │   ├── context/       # DataContext : image upload, diagnosis, polling
│   │   ├── types/         # ResultType, LanguageType, etc.
│   │   └── ...
│   └── package.json
│
├── backend/               # FastAPI + YOLO + N-ATLaS (deploy to Render)
│   ├── app.py             # Live FastAPI entrypoint used by the frontend
│   ├── unified_pipeline.py # Concurrent pest + disease inference and merge
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── tests/              # Pipeline unit tests
│   ├── CROP_DISEASES/      # Disease knowledge documents
│   ├── pests/              # Pest/disease Markdown KB keyed by label_key
│   ├── bestpest1.pt        # Local pest model (ignored by Git)
│   ├── model.pt            # Local disease model (ignored by Git)
│   └── N-ATLaS.Q4_K_M.gguf # Local recommendation model (ignored by Git)
│
├── project_files/         # Research scripts, notebooks, and project documents
└── README.md
```

The directory move from the original layout was done with `git mv crop-predict frontend`, which preserves tracked history and local files. The existing `backend/` and `backend/CROP_DISEASES/` were already in the correct locations, so they were not copied or renamed. `backend/model.pt` was removed from Git's index with `git rm --cached backend/model.pt`; its local copy is retained and all `*.pt`/`*.gguf` files are now ignored.

To repeat the layout migration from the repository root on a fresh checkout, use:

```bash
git mv crop-predict frontend
git rm --cached --ignore-unmatch backend/model.pt backend/pest_best.pt backend/faved_disease_model.pt
mkdir -p backend/CROP_DISEASES
git status --short
```

`git rm --cached` only removes weights from Git's index; it does not delete local files. If a required weight is already tracked under a different name/path, add that exact path to the `git rm --cached` command. Keep locally useful models outside Git and upload deployment weights to Hugging Face or another artifact store. Do not run `mv`, `rm`, or `git clean` against the existing model/data directories as part of the migration.

Run local checks from the correct package directories:

```bash
(cd frontend && npm install && npm run build && npm run lint)
(cd backend && python -m uvicorn app:app --host 127.0.0.1 --port 8000)
```

---

## Backend Versions

The `backend/` folder ships with **two** entry points. Only run one at a time. Pick whichever fits what you're testing.

### `app2.py` : Cached Backend

Serves **precomputed / cached** diagnosis results instead of running the vision and language models live on every request.

**Why it exists:** it's fast, doesn't need the model runtime warmed up, and is resilient during demos, presentations, or low-connectivity situations where a live inference call might time out.

**Limitations:**

- Does **not** perform real inference on the image you upload. It maps requests to a fixed set of pre-generated results.
- Not suitable for production use or real farmer deployment : It exists for reliable demos and frontend development without depending on a live model server.
- Response shape may differ slightly from `app.py` (e.g. a single synchronous `/diagnose` call rather than a job you poll), so the frontend's polling logic may need adjusting to point at this backend.

### `app.py` : Live Backend

Runs the **actual trained models** end-to-end: the YOLOv11-based vision model detects the crop and disease from the uploaded photo, then the language model generates the cause/treatment/prevention write-up in the selected language.

**Limitations (from current project scope):**

- **Four languages supported**: English, Hausa, Igbo, and Yoruba (AI-generated translations should be reviewed by fluent speakers).
- **Two crops covered**: cocoa and maize. The disease detector has seven labels (five disease/pest labels plus one healthy label per crop); the pest detector has nine labels (five maize and four cocoa pest classes).
- **Bounding boxes are detections, not segmentation**: they localize model findings but do not outline the exact affected leaf/pod area.
- **Single image only**: no batch or multi-image upload in one request.
- **Slower and less predictable response times** than the cached backend, since it depends on live model inference. This is why the frontend uses job polling (`/diagnose/start` + `/diagnose/status/{job_id}`) with a timeout, rather than a single blocking request.
- **Needs a reachable backend URL**: set `VITE_API_URL` in the frontend environment to the deployed Render service URL.
- Requires the host machine running the model (e.g. a Colab session or local GPU machine) to stay online for the tunnel to work.

---

## Tech Stack

**Frontend:**

- React + TypeScript
- Vite
- React Router

**Backend:**

- Python
- YOLOv11 (computer-vision detection, via transfer learning)
- N-ATLAS language model for recommendation generation (cause, treatment, prevention text)
- ngrok (tunnels the local backend to a public URL for the frontend to call)


**Tooling:**

- Roboflow: image dataset sourcing/labeling
- Google Colab / VS Code: training and experimentation
- GitHub & Google Drive: version control and collaboration

---

## Model Results

The vision model was evaluated on unseen test images across all 7 classes:

| Metric    | Score |
| --------- | ----- |
| Precision | 86%   |
| Recall    | 86%   |
| mAP@50    | 92%   |
| mAP@50–95 | 74%   |

The full pipeline (photo in, diagnosis and recommendation out) has been tested end-to-end on real photos and works.

---

## Getting Started

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

This starts the Vite dev server (typically at `http://localhost:5173`).

### Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate   # on Windows: venv\Scripts\activate
python -m pip install -r requirements.txt
```

If `backend/.env` does not exist, create it from `.env.example`. Model paths can point to local files, or the backend downloads missing weights from the configured Hugging Face repositories. Start Uvicorn from `backend/` for local development.

```bash
cp .env.example .env
```

Run **one** backend. Use the live backend for the frontend's asynchronous diagnosis flow:

```bash
cd backend
python -m unittest discover -s tests -v
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

The cached backend can also be started with `python -m uvicorn app2:app --host 127.0.0.1 --port 8000`. For remote access, expose port 8000 with ngrok; a tunnel is not needed for local use.

For local frontend development, `frontend/.env.example` sets the API URL to `http://127.0.0.1:8000`. Copy it to `frontend/.env` if you need an explicit setting; the frontend uses this same URL by default.

### Environment Variables

The backend reads these paths from `backend/.env`, relative to the backend directory:

```
LLM_MODEL_PATH=N-ATLaS.Q4_K_M.gguf
LLM_MODEL_REPO_ID=QuantFactory/N-ATLaS-GGUF
LLM_MODEL_FILENAME=N-ATLaS.Q4_K_M.gguf
DETECTION_MODEL_PATH=model.pt
DETECTION_MODEL_REPO_ID=<your-private-or-public-yolo-model-repository>
DETECTION_MODEL_FILENAME=model.pt
PEST_MODEL_PATH=bestpest1.pt
PEST_MODEL_REPO_ID=<your-private-or-public-pest-model-repository>
PEST_MODEL_FILENAME=bestpest1.pt
PEST_CONFIDENCE_THRESHOLD=0.25
DISEASE_CONFIDENCE_THRESHOLD=0.5
YOLO_IMAGE_SIZE=640
YOLO_REVIEW_CONFIDENCE=0.45
DOCUMENTS_FOLDER_PATH=CROP_DISEASES
PEST_KB_FOLDER_PATH=pests
CACHE_PATH=recommendation_cache.json
HF_HOME=/var/data/huggingface
CORS_ORIGINS=https://your-frontend.vercel.app
```

The `.env` file is not committed because it is machine-local. Change these values only if you store the model or knowledge-base assets elsewhere.

### Generating the Recommendation Cache Ahead of Time

The cached backend (`app2.py`) reads its results from `recommendation_cache.json`. Rather than generating this file by hand, you can build it ahead of time by running `generate_cache.py`, which loops through every crop/disease pair in the knowledge base and generates localized recommendations, then writes the results to `recommendation_cache.json`.

To run it:

```bash
cd backend
python generate_cache.py
```

This uses the same models and prompts as the live backend, so each entry can take a while to generate. Since this is a one-time, offline step, there is no need to rush it: let it run to completion so every crop/disease pair has a cached entry.

Once complete, `recommendation_cache.json` will exist in the backend folder and `app2.py` can be run to serve fast, precomputed results without needing the models warmed up on every request.

### Connecting Frontend to Backend

The frontend reads `VITE_API_URL` and defaults to the local backend URL:

```ts
// frontend/src/context/DataContext.tsx
const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
```

For remote use, set `VITE_API_URL` to the public backend URL in Vercel's project environment variables. The live backend exposes `/diagnose/start`, `/diagnose/status/{job_id}`, and `/recommend/translate/start` for asynchronous diagnosis and on-demand translations.

### Deploying the Vite Frontend to Vercel

This repository currently uses Vite + React, not Next.js. Vercel can deploy it directly without a framework migration:

1. Import the repository into Vercel and set **Root Directory** to `frontend`.
2. Use build command `npm run build` and output directory `dist` (install command `npm install`).
3. Set `VITE_API_URL` to the deployed Render service URL, then deploy.

`frontend/.env.production.example` is a placeholder example; set the real URL in Vercel rather than committing a deployment-specific `.env.production`.

### Deploying the Backend to Render

Create a Render **Web Service** using the repository's Dockerfile and set its root directory to `backend`. The container binds to Render's `PORT` and exposes `/health`. `unified_pipeline.py` runs pest and disease inference concurrently, combines results using `label_key`, then `app.py` loads matching disease DOCX or pest/disease Markdown facts for one grounded N-ATLaS recommendation.

Configure these Render environment variables:

- `DETECTION_MODEL_REPO_ID`: Hugging Face repository containing the existing disease weights, with `DETECTION_MODEL_FILENAME=model.pt`.
- `PEST_MODEL_REPO_ID`: Hugging Face repository containing `bestpest1.pt`, with `PEST_MODEL_FILENAME=bestpest1.pt`.
- `LLM_MODEL_REPO_ID=QuantFactory/N-ATLaS-GGUF` and `LLM_MODEL_FILENAME=N-ATLaS.Q4_K_M.gguf`.
- `HF_HOME=/var/data/huggingface`, with a Render persistent disk mounted at `/var/data` (recommend at least 10 GB).
- `CORS_ORIGINS=https://<your-vercel-domain>` (comma-separated if more than one frontend origin is needed).

N-ATLaS is several gigabytes and is downloaded on first startup; persistent storage prevents downloading it again after restarts. The service also loads PyTorch and the GGUF into memory, so choose a Render instance with substantial RAM (16 GB recommended); a small/free instance is not suitable. The original `NCAIR1/N-ATLaS` repository contains gated BF16 Transformers weights, not the GGUF format this app's `llama-cpp-python` runtime can load. The configured QuantFactory repository is the compatible GGUF source.

Model weights are ignored by Git. Both model files are present locally, but must be uploaded to Hugging Face (or another artifact store) before Render can download them; set both model repository IDs above. The `backend/pests/` Markdown entries are currently marked draft and need agronomist review. The result screen will show a review notice, and prompts explicitly prohibit inventing product names or application rates.

---

## Project Scope & Limitations

**Covered:**

- 2 crops: cocoa and maize
- 9 pest classes and 7 disease-detector labels
- Live camera/photo-based detection
- Recommendations in English, Hausa, Igbo, and Yoruba

**Not yet covered:**

- Additional crops or languages beyond the above
- Affected-area segmentation (bounding-box detection only)
- Multiple image uploads in a single request
- Offline / low-connectivity operation (both backends currently depend on a live server connection)

---

### Demo Video

https://github.com/user-attachments/assets/ee3bf0f2-01c9-4630-9191-ab1964fa747b


---

# Acknowledgement

A huge thanks to the people behind this project:

## Contributors

Adeoluwa Ajayi · Esther Udom · Favour Ibitolu · Alli David · Emmanuel Fasina · Dan Cornellius · David Inyang · Mariya Isa · Adamu Aishat · Asenath Adama

## Facilitators

Mr. Ayuba Stephen

Mr. Rizama Victor

## Organization

National Center for Artificial Intelligence and Robotics(NCAIR)

---

_FAVE pairs computer-vision screening with knowledge-grounded language support to help farmers respond earlier. Model output is a screening aid, not a confirmed diagnosis; draft knowledge-base records require agronomist review._





