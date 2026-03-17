"""
SENTINEL-X — FastAPI Backend

POST /analyze       — analyze plain text, URL, or JSON VPN log
POST /analyze/file  — analyze uploaded PDF or image
GET  /logs          — last 50 analyzed inputs
GET  /profiles      — list org profiles
GET  /health        — health check
"""

import time
import uuid
from collections import deque
from typing import Optional, Dict, Any

import random
from fastapi import UploadFile, File
from fastapi.responses import JSONResponse

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import torch
from security_gate import run_gate

from input_handlers import route_input
from policy_engine import evaluate, list_profiles
from infer import analyze_text as model_analyze_text
#from model_loader import download_model
from xai.explainability_pipeline import explain as xai_explain

#download_model()

# Load model
#model = torch.load("sentinelx_model.pt", map_location="cpu")
#model.eval()
# ---------------------------------------------------------------------------
# APP SETUP
# ---------------------------------------------------------------------------
from cors_config import setup_cors  
app = FastAPI(
    title="SENTINEL-X API",
    description="Adversarial Intent Graph — Cyber Defense Platform",
    version="1.0.0",
)

setup_cors(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

audit_log: deque = deque(maxlen=50)

origins = [
    "http://localhost:3000",  # React frontend URL
]
# ---------------------------------------------------------------------------
# RISK SCORING
# ---------------------------------------------------------------------------

RISK_WEIGHTS = {
    "urgency_induction": 1.0,
    "authority_spoofing": 1.2,
    "fear_amplification": 0.8,
    "trust_exploitation": 0.8,
    "scarcity_signaling": 0.7,
    "credential_harvesting": 1.5,
    "instruction_hijacking": 2.0,
    "data_exfiltration": 2.0,
    "identity_spoofing": 1.3,
    "redirect_chaining": 1.0,
    "payload_delivery": 1.4,
    "recon_probing": 0.9,
}

MOCK_RESULTS = [
    {
        "deepfake_score": 0.9312,
        "real_score":     0.0688,
        "risk_level":     "Deepfake Likely",
        "indicators":     [
            "model confidence: high deepfake probability",
            "deepfake classifier score: 0.93",
        ],
        "raw_predictions": [
            {"label": "Deepfake", "score": 0.9312},
            {"label": "Real",     "score": 0.0688},
        ],
    },
    {
        "deepfake_score": 0.6741,
        "real_score":     0.3259,
        "risk_level":     "Deepfake Suspected",
        "indicators":     [
            "deepfake classifier score: 0.67",
        ],
        "raw_predictions": [
            {"label": "Deepfake", "score": 0.6741},
            {"label": "Real",     "score": 0.3259},
        ],
    },
    {
        "deepfake_score": 0.4102,
        "real_score":     0.5898,
        "risk_level":     "Uncertain",
        "indicators":     [],
        "raw_predictions": [
            {"label": "Real",     "score": 0.5898},
            {"label": "Deepfake", "score": 0.4102},
        ],
    },
    {
        "deepfake_score": 0.0821,
        "real_score":     0.9179,
        "risk_level":     "Likely Real",
        "indicators":     [
            "authenticity score: 0.92",
        ],
        "raw_predictions": [
            {"label": "Real",     "score": 0.9179},
            {"label": "Deepfake", "score": 0.0821},
        ],
    },
]

def compute_risk(intent_vector: Dict[str, float]):

    filtered = {
        dim: score if score >= 0.4 else 0.0
        for dim, score in intent_vector.items()
    }

    if sum(filtered.values()) == 0:
        return 0, "low"

    weighted_sum = 0

    for dim, score in filtered.items():
        weight = RISK_WEIGHTS.get(dim, 1.0)
        weighted_sum += score * weight

    max_possible = sum(RISK_WEIGHTS.values())

    risk_score = round((weighted_sum / max_possible) * 100)

    if risk_score < 15:
        severity = "low"
    elif risk_score < 35:
        severity = "medium"
    elif risk_score < 60:
        severity = "high"
    else:
        severity = "critical"

    return risk_score, severity


def get_top_threats(intent_vector: Dict[str, float], n: int = 3):

    active = {
        dim: score
        for dim, score in intent_vector.items()
        if score >= 0.4
    }

    sorted_dims = sorted(active.items(), key=lambda x: x[1], reverse=True)

    results = []

    for dim, score in sorted_dims[:n]:
        results.append({
            "dimension": dim,
            "score": round(score, 4),
            "label": dim.replace("_", " ").title()
        })

    return results


# ---------------------------------------------------------------------------
# SCHEMAS
# ---------------------------------------------------------------------------

class AnalyzeTextRequest(BaseModel):
    text: str
    org_profile: Optional[str] = "general_consumer"


class AnalyzeResponse(BaseModel):

    request_id: str
    timestamp: float
    input_type: str

    risk_score: int
    severity: str

    intent_vector: Dict[str, float]

    action: str
    action_label: str

    top_threats: list
    gate_flags: list
    gate_blocked: bool

    per_dimension: dict
    meta: dict

    explanation: str
    kill_chain: list
    token_attributions: list
    dlp_scan: dict

    mitre_techniques: list
    attack_pattern: Optional[dict]

    risk_breakdown: dict
    dimension_severity: dict

    recommended_action: str
    final_explanation_report: str


# ---------------------------------------------------------------------------
# CORE ANALYSIS PIPELINE
# ---------------------------------------------------------------------------

def _run_analysis(
    raw: str = "",
    file_bytes: bytes = None,
    filename: str = None,
    org_profile: str = "general_consumer",
) -> Dict[str, Any]:

    request_id = str(uuid.uuid4())[:8]
    ts = time.time()

    # Step 1 — Input Routing
    handler_result = route_input(
        raw=raw,
        file_bytes=file_bytes,
        filename=filename
    )

    content = handler_result["content"]
    input_type = handler_result["type"]
    meta = handler_result.get("meta", {})

    # Step 2 — Security Gate
    gate_result = run_gate(content)

    clean_text = gate_result["clean_text"]

    # Step 3 — ML Intent Detection
    intent_vector = model_analyze_text(clean_text)

    if not isinstance(intent_vector, dict):
        intent_vector = {}

    if gate_result["block"]:
        intent_vector["instruction_hijacking"] = 0.99

    # Step 4 — Risk Scoring
    risk_score, severity = compute_risk(intent_vector)

    top_threats = get_top_threats(intent_vector)

    # Step 5 — Policy Engine
    policy = evaluate(
        intent_vector=intent_vector,
        org_profile=org_profile,
        gate_flags=gate_result["flags"],
        risk_score=risk_score,
        severity=severity,
    )

    # Step 6 — XAI Pipeline
    xai_result = xai_explain(
        text=clean_text,
        intent_vector=intent_vector,
    )

    # Step 7 — Build Response

    response = {

        "request_id": request_id,
        "timestamp": ts,

        "input_type": input_type,
        "meta": meta,

        "gate_flags": gate_result.get("flags", []),
        "gate_blocked": gate_result.get("block", False),

        "per_dimension": policy.get("per_dimension", {}),
        "action": policy.get("action", "allow"),
        "action_label": policy.get("action_label", "Allow"),

        "top_threats": top_threats,

        "intent_vector": intent_vector,

        "risk_score": xai_result.get("risk_score", risk_score),
        "severity": xai_result.get("severity", severity),

        "risk_breakdown": xai_result.get("risk_breakdown", {}),
        "dimension_severity": xai_result.get("dimension_severity", {}),

        "kill_chain": xai_result.get("kill_chain", []),
        "token_attributions": xai_result.get("token_attributions", []),

        "dlp_scan": xai_result.get("dlp_scan", {}),

        "mitre_techniques": xai_result.get("mitre_techniques", []),
        "attack_pattern": xai_result.get("attack_pattern"),

        "explanation": xai_result.get("explanation", ""),
        "recommended_action": xai_result.get("recommended_action", ""),

        "final_explanation_report":
            xai_result.get("final_explanation_report", "")
    }

    # -----------------------------------------------------------------------
    # AUDIT LOG
    # -----------------------------------------------------------------------

    audit_log.appendleft({

        "request_id": request_id,
        "timestamp": ts,

        "input_type": input_type,

        "input_preview": (raw or "")[:120] or f"[{filename}]",

        "risk_score": response["risk_score"],
        "severity": response["severity"],

        "action": response["action"],

        "top_intent":
            top_threats[0]["dimension"] if top_threats else "none",

        "gate_flags": gate_result.get("flags", []),
    })

    return response


# ---------------------------------------------------------------------------
# ENDPOINTS
# ---------------------------------------------------------------------------

@app.get("/health")
def health():

    return {
        "status": "ok",
        "service": "SENTINEL-X",
        "version": "1.0.0"
    }

@app.get("/")
def root():
    return {"status": "SENTINEL-X online", "version": "3.0.0"}


@app.post("/analyze_image")
async def analyze_image(file: UploadFile = File(...)):
    contents = await file.read()
    return analyze_image_bytes(contents, file.filename)

@app.get("/scan_images")
async def scan_images():
    IMAGES_FOLDER = Path("images")
    IMAGES_FOLDER.mkdir(exist_ok=True)
    return {"results": analyze_images_in_folder(IMAGES_FOLDER)}





@app.get("/profiles")
def get_profiles():

    return {
        "profiles": list_profiles()
    }


@app.get("/logs")
def get_logs():

    return {
        "count": len(audit_log),
        "logs": list(audit_log)
    }


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_text_endpoint(body: AnalyzeTextRequest):

    return _run_analysis(
        raw=body.text,
        org_profile=body.org_profile,
    )


@app.post("/analyze/file")
async def analyze_file_endpoint(
    file: UploadFile = File(...),
    org_profile: str = Form("general_consumer"),
):

    file_bytes = await file.read()

    return _run_analysis(
        raw="",
        file_bytes=file_bytes,
        filename=file.filename,
        org_profile=org_profile,
    )


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )