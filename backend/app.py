import os

import httpx
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response

app = FastAPI(title="FAVE API Proxy", version="1.0.0")
MODAL_URL = os.getenv("MODAL_URL", "https://your-modal-app-url.modal.run").rstrip("/")
PROXY_TIMEOUT_SECONDS = float(os.getenv("PROXY_TIMEOUT_SECONDS", "60"))

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


async def _forward(method: str, path: str, **kwargs) -> Response:
    try:
        async with httpx.AsyncClient(timeout=PROXY_TIMEOUT_SECONDS) as client:
            upstream = await client.request(method, f"{MODAL_URL}{path}", **kwargs)
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="The inference service is unavailable.") from exc

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        media_type=upstream.headers.get("content-type"),
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    content = await file.read()
    files = {"file": (file.filename or "upload", content, file.content_type or "application/octet-stream")}
    return await _forward("POST", "/predict", files=files)


@app.post("/diagnose/start")
async def diagnose_start(
    file: UploadFile = File(...),
    language: str = Form("English"),
    mode: str = Form("both"),
):
    content = await file.read()
    files = {"file": (file.filename or "upload", content, file.content_type or "application/octet-stream")}
    data = {"language": language, "mode": mode}
    return await _forward("POST", "/diagnose/start", files=files, data=data)


@app.get("/diagnose/status/{job_id}")
async def diagnose_status(job_id: str):
    return await _forward("GET", f"/diagnose/status/{job_id}")


@app.post("/recommend/translate/start")
async def translate_recommendation(request: Request):
    body = await request.json()
    return await _forward("POST", "/recommend/translate/start", json=body)
