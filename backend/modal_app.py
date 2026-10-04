import os
from pathlib import Path

import modal

BACKEND_DIR = Path(__file__).resolve().parent
APP_NAME = "faved-api"
MODEL_VOLUME_NAME = "faved-models"
MODEL_MOUNT_PATH = "/models"
FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "").strip()

if not FRONTEND_ORIGIN:
    raise RuntimeError(
        "Set FRONTEND_ORIGIN to the deployed frontend origin before deploying, "
        "for example FRONTEND_ORIGIN=https://your-app.vercel.app."
    )

app = modal.App(APP_NAME)
model_volume = modal.Volume.from_name(MODEL_VOLUME_NAME, create_if_missing=False)

image = (
    modal.Image.debian_slim(python_version="3.10")
    .apt_install("libgl1", "libglib2.0-0", "libgomp1", "libopenblas0")
    .pip_install_from_requirements(str(BACKEND_DIR / "modal-requirements.txt"))
    .env(
        {
            "PEST_MODEL_PATH": f"{MODEL_MOUNT_PATH}/bestpest1.pt",
            "DETECTION_MODEL_PATH": f"{MODEL_MOUNT_PATH}/model.pt",
            "LLM_MODEL_PATH": f"{MODEL_MOUNT_PATH}/N-ATLaS.Q4_K_M.gguf",
            "HF_HOME": "/root/.cache/huggingface",
            "FRONTEND_ORIGIN": FRONTEND_ORIGIN,
            "CORS_ORIGINS": FRONTEND_ORIGIN,
            "PYTHONUNBUFFERED": "1",
        }
    )
    .add_local_dir(str(BACKEND_DIR / "CROP_DISEASES"), remote_path="/root/CROP_DISEASES")
    .add_local_dir(str(BACKEND_DIR / "pests"), remote_path="/root/pests")
    .add_local_file(str(BACKEND_DIR / "inference_app.py"), remote_path="/root/inference_app.py")
    .add_local_file(str(BACKEND_DIR / "unified_pipeline.py"), remote_path="/root/unified_pipeline.py")
    .add_local_file(str(BACKEND_DIR / "knowledge_base.py"), remote_path="/root/knowledge_base.py")
)


@app.function(
    image=image,
    volumes={MODEL_MOUNT_PATH: model_volume},
    scaledown_window=300,
    timeout=900,
    cpu=4,
    memory=16384,
)
@modal.asgi_app()
def serve():
    import inference_app as fastapi_app

    return fastapi_app.app
