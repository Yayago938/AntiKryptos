import torch
import torch.nn as nn
import re
import random
from transformers import AutoTokenizer, DistilBertModel

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

INTENT_DIMS = [
    "urgency_induction",
    "authority_spoofing",
    "fear_amplification",
    "trust_exploitation",
    "scarcity_signaling",
    "credential_harvesting",
    "instruction_hijacking",
    "data_exfiltration",
    "identity_spoofing",
    "redirect_chaining",
    "payload_delivery",
    "recon_probing"
]

# ---------------------------
# MODEL ARCHITECTURE
# ---------------------------
class IntentModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder    = DistilBertModel.from_pretrained("distilbert-base-uncased")
        self.dropout    = nn.Dropout(0.3)
        self.classifier = nn.Linear(768, 12)

    def forward(self, input_ids, attention_mask):
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        pooled  = outputs.last_hidden_state[:, 0]
        pooled  = self.dropout(pooled)
        return self.classifier(pooled)

# ---------------------------
# LOAD TOKENIZER
# ---------------------------
try:
    tokenizer = AutoTokenizer.from_pretrained("./tokenizer")
    print("✅ Tokenizer loaded")
except:
    tokenizer = None
    print("⚠️ Tokenizer not found — using heuristic mode")

# ---------------------------
# LOAD MODEL
# ---------------------------
try:
    model      = IntentModel()
    state_dict = torch.load("sentinelx_model.pt", map_location=DEVICE)
    new_state_dict = {}
    for key in state_dict:
        new_key = key.replace("bert.", "encoder.")
        new_state_dict[new_key] = state_dict[key]
    model.load_state_dict(new_state_dict, strict=False)
    model.to(DEVICE)
    model.eval()
    print("✅ Model loaded")
except:
    model = None
    print("⚠️ Model not found — using heuristic mode")

# ---------------------------
# HEURISTIC FALLBACK
# ---------------------------
def heuristic_scores(text: str) -> dict:
    random.seed(hash(text) % 9999)
    scores = {dim: round(random.uniform(0.0, 0.15), 3) for dim in INTENT_DIMS}
    t = text.lower()
    if re.search(r"urgent|suspend|expire|immediate|act now|last chance", t):
        scores["urgency_induction"]     = round(random.uniform(0.75, 0.95), 3)
    if re.search(r"password|otp|login|verify|username|pin|account number", t):
        scores["credential_harvesting"] = round(random.uniform(0.75, 0.95), 3)
    if re.search(r"ignore|forget|override|jailbreak|dan|disregard|new persona", t):
        scores["instruction_hijacking"] = round(random.uniform(0.75, 0.95), 3)
    if re.search(r"bank|rbi|sebi|official|security team|it department|government", t):
        scores["authority_spoofing"]    = round(random.uniform(0.65, 0.85), 3)
    if re.search(r"summarize all|list all|reveal|export all|send me the|confidential", t):
        scores["data_exfiltration"]     = round(random.uniform(0.65, 0.85), 3)
    if re.search(r"permanently deleted|legal action|arrested|penalt|account closed", t):
        scores["fear_amplification"]    = round(random.uniform(0.65, 0.85), 3)
    if re.search(r"your colleague|as discussed|referred by|following up|as per our", t):
        scores["trust_exploitation"]    = round(random.uniform(0.65, 0.85), 3)
    if re.search(r"bit\.ly|tinyurl|click here|follow this link|short url", t):
        scores["redirect_chaining"]     = round(random.uniform(0.65, 0.85), 3)
    if re.search(r"download|attachment|enable macros|install|zip file|pdf attached", t):
        scores["payload_delivery"]      = round(random.uniform(0.65, 0.85), 3)
    if re.search(r"who is your|what system|which software|it contact|what version", t):
        scores["recon_probing"]         = round(random.uniform(0.65, 0.85), 3)
    if re.search(r"noreply@|support@|security@|admin@|\.ru|\.xyz", t):
        scores["identity_spoofing"]     = round(random.uniform(0.65, 0.85), 3)
    if re.search(r"limited time|only \d+ left|exclusive|offer ends|running out", t):
        scores["scarcity_signaling"]    = round(random.uniform(0.65, 0.85), 3)
    return scores

# ---------------------------
# MAIN ANALYSIS FUNCTION
# ---------------------------
def analyze_text(text: str) -> dict:
    if model is None or tokenizer is None:
        return heuristic_scores(text)

    encoding = tokenizer(
        text,
        max_length=128,
        padding="max_length",
        truncation=True,
        return_tensors="pt"
    )
    input_ids      = encoding["input_ids"].to(DEVICE)
    attention_mask = encoding["attention_mask"].to(DEVICE)

    with torch.no_grad():
        logits = model(input_ids, attention_mask)
        probs  = torch.sigmoid(logits).cpu().numpy()[0]

    return {dim: round(float(p), 4) for dim, p in zip(INTENT_DIMS, probs)}

# ---------------------------
# RISK SCORING
# ---------------------------
def get_risk_score(intent_vector: dict) -> tuple:
    weights = {
        "urgency_induction":     1.0,
        "authority_spoofing":    1.2,
        "fear_amplification":    0.8,
        "trust_exploitation":    0.8,
        "scarcity_signaling":    0.7,
        "credential_harvesting": 1.5,
        "instruction_hijacking": 2.0,
        "data_exfiltration":     2.0,
        "identity_spoofing":     1.3,
        "redirect_chaining":     1.0,
        "payload_delivery":      1.4,
        "recon_probing":         0.9
    }

    filtered = {
        dim: (score if score >= 0.4 else 0.0)
        for dim, score in intent_vector.items()
    }

    if sum(filtered.values()) == 0:
        return 0, "low"

    weighted_sum = sum(filtered[d] * weights[d] for d in INTENT_DIMS)
    max_possible = sum(weights.values())
    risk_score   = round((weighted_sum / max_possible) * 100)

    if risk_score < 15:   severity = "low"
    elif risk_score < 35: severity = "medium"
    elif risk_score < 60: severity = "high"
    else:                 severity = "critical"

    return risk_score, severity

# ---------------------------
# TOP DIMENSIONS HELPER
# ---------------------------
def get_top_dims(intent_vector: dict, n: int = 3) -> list:
    """Returns top n activated dimensions above 0.4 threshold."""
    active      = {dim: score for dim, score in intent_vector.items() if score >= 0.4}
    sorted_dims = sorted(active.items(), key=lambda x: x[1], reverse=True)
    return sorted_dims[:n]