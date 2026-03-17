import os
import requests

MODEL_URL = "https://drive.google.com/file/d/1Qp4ZcV6FY5-QUwI-yMg8kiU7f_oHgcyv/view?usp=sharing"
MODEL_PATH = "sentinelx_model.pt"

def download_model():
    if not os.path.exists(MODEL_PATH):
        print("Downloading model...")
        r = requests.get(MODEL_URL)
        with open(MODEL_PATH, "wb") as f:
            f.write(r.content)
        print("Model downloaded.")