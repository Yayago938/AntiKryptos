# import io
# from pathlib import Path
# from typing import Any, Dict, List

# _pipeline = None


# def _get_pipeline():
#     global _pipeline
#     if _pipeline is None:
#         from transformers import pipeline
#         print("Loading deepfake model (downloads ~500MB on first run)...")
#         _pipeline = pipeline(
#             "image-classification",
#             model="prithivMLmods/Deep-Fake-Detector-Model",
#         )
#         print("Deepfake model ready.")
#     return _pipeline


# def _map_risk(label: str, score: float) -> str:
#     label_lower = label.lower()
#     if "fake" in label_lower or "deepfake" in label_lower:
#         if score >= 0.80:
#             return "Deepfake Likely"
#         elif score >= 0.55:
#             return "Deepfake Suspected"
#         else:
#             return "Uncertain"
#     else:
#         if score >= 0.75:
#             return "Likely Real"
#         else:
#             return "Uncertain"


# def _build_result(filename: str, predictions: List[Dict]) -> Dict[str, Any]:
#     fake_score = 0.0
#     real_score = 0.0
#     top_label  = predictions[0]["label"]
#     top_score  = predictions[0]["score"]

#     for p in predictions:
#         lbl = p["label"].lower()
#         if "fake" in lbl or "deepfake" in lbl:
#             fake_score = p["score"]
#         elif "real" in lbl:
#             real_score = p["score"]

#     if fake_score == 0.0 and real_score > 0.0:
#         fake_score = 1.0 - real_score
#     if real_score == 0.0 and fake_score > 0.0:
#         real_score = 1.0 - fake_score

#     indicators: List[str] = []
#     if fake_score >= 0.80:
#         indicators.append("model confidence: high deepfake probability")
#     if fake_score >= 0.55:
#         indicators.append(f"deepfake classifier score: {fake_score:.2f}")
#     if real_score >= 0.75:
#         indicators.append(f"authenticity score: {real_score:.2f}")

#     return {
#         "image":           filename,
#         "deepfake_score":  round(fake_score, 4),
#         "real_score":      round(real_score, 4),
#         "risk_level":      _map_risk(top_label, top_score),
#         "indicators":      indicators,
#         "raw_predictions": predictions,
#     }


# def analyze_image_bytes(image_bytes: bytes, filename: str) -> Dict[str, Any]:
#     from PIL import Image
#     try:
#         img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
#     except Exception as e:
#         return {"image": filename, "error": f"Could not read image: {e}"}
#     try:
#         predictions = _get_pipeline()(img)
#     except Exception as e:
#         return {"image": filename, "error": f"Model inference failed: {e}"}
#     return _build_result(filename, predictions)


# def analyze_image_path(image_path: Path) -> Dict[str, Any]:
#     from PIL import Image
#     try:
#         img = Image.open(str(image_path)).convert("RGB")
#     except Exception as e:
#         return {"image": image_path.name, "error": f"Could not open image: {e}"}
#     try:
#         predictions = _get_pipeline()(img)
#     except Exception as e:
#         return {"image": image_path.name, "error": f"Model inference failed: {e}"}
#     return _build_result(image_path.name, predictions)


# def analyze_images_in_folder(folder: Path) -> List[Dict[str, Any]]:
#     supported = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
#     results   = []
#     for path in sorted(folder.iterdir()):
#         if path.suffix.lower() in supported and path.is_file():
#             results.append(analyze_image_path(path))
#     return results