# SENTINEL-X Backend

Adversarial Intent Graph — Cyber Defense Platform  
IndiaNext Hackathon 2026 | K.E.S. Shroff College, Mumbai

---

## Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API docs auto-generated at: http://localhost:8000/docs

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/analyze` | Analyze text / URL / VPN log (JSON body) |
| POST | `/analyze/file` | Analyze PDF or image (multipart upload) |
| GET | `/logs` | Last 50 analyzed inputs |
| GET | `/profiles` | List org profiles |
| GET | `/health` | Health check |

### POST /analyze — Request body

```json
{
  "text": "Your account has been suspended. Click here to verify immediately.",
  "org_profile": "bank"
}
```

`org_profile` options: `general_consumer` | `bank` | `hospital`

---

## Swapping in the Real Model (Person 1 Handoff — Hour 5)

Once `infer.py` is ready, drop it into the `backend/` folder.  
`main.py` will automatically detect and import it:

```python
# infer.py must export this function:
def analyze_text(text: str) -> dict:
    # Returns: {dimension_name: float, ...} — 12 keys, values 0.0–1.0
    ...
```

No other changes needed. The mock will be silently replaced.

---

## File Structure

```
backend/
├── main.py            # FastAPI app, endpoints, orchestration
├── security_gate.py   # Trie + MinHash + PII + hidden text checks
├── input_handlers.py  # URL / PDF / image / VPN log handlers
├── policy_engine.py   # Org profiles, thresholds, action mapping
├── infer.py           # (Person 1 delivers at Hour 5 — drop in here)
└── requirements.txt
```

---

## Railway Deployment

```bash
# In project root
railway init
railway up
```

Set env var if needed: `PORT=8000`  
Live URL shared with Person 4 at Hour 13.
