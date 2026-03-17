import os
import torch
import requests

MODEL_URL = "https://huggingface.co/yashchauhan20/sentinelx-model"
MODEL_PATH = "sentinelx_model.pt"

model = None


def download_model():
    """Download model from HuggingFace if not present"""
    if not os.path.exists(MODEL_PATH):
        print("Downloading model from HuggingFace...")

        response = requests.get(MODEL_URL, stream=True)
        response.raise_for_status()

        with open(MODEL_PATH, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        print("Model downloaded successfully.")


def load_model():
    """Load model into memory"""
    global model

    if model is None:
        download_model()

        print("Loading model...")
        model = torch.load(MODEL_PATH, map_location=torch.device("cpu"))
        model.eval()

        print("Model loaded successfully.")

    return model