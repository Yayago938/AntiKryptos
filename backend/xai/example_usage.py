#!/usr/bin/env python3
"""
example_usage.py
SENTINEL-X — Adversarial Intent Graph Cyber Defense System

Demonstrates three ways to use the XAI Explainability Layer:
  1. demo_analysis()  — instant demo with built-in mock data (no model needed)
  2. explain()        — backend API integration pattern
  3. module-level     — calling individual pipeline components directly
"""

import json
import sys
import os

# Allow running from repository root without installing
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ═══════════════════════════════════════════════════════════════════════════
# Example 1 — Quick Demo (hackathon / CI mode, no GPU/model required)
# ═══════════════════════════════════════════════════════════════════════════

def example_1_quick_demo():
    """Run the built-in phishing demo with a single function call."""
    print("=" * 70)
    print("EXAMPLE 1 — Quick Demo (phishing scenario)")
    print("=" * 70)

    from xai.explainability_pipeline import demo_analysis

    result = demo_analysis(scenario="phishing")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


# ═══════════════════════════════════════════════════════════════════════════
# Example 2 — Backend API Integration Pattern
# ═══════════════════════════════════════════════════════════════════════════

def example_2_api_integration():
    """
    Shows how the FastAPI / Flask backend would call explain().
    In production, intent_vector comes from the DistilBERT model.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 2 — Backend API Integration")
    print("=" * 70)

    from xai.explainability_pipeline import explain

    # ── Simulated phishing message ────────────────────────────────────────
    incoming_text = (
        "Dear Customer,\n\n"
        "Your HDFC Bank account will be permanently blocked within 24 hours "
        "unless you verify your identity immediately. Suspicious login activity "
        "has been detected from an unknown device.\n\n"
        "Click here to secure your account: http://hdfc-secure-login.net/verify\n\n"
        "Enter your User ID, Password and OTP to restore access.\n\n"
        "Regards,\nHDFC Bank Security Team"
    )

    # ── This dict would come from the DistilBERT model in production ──────
    intent_vector_from_model = {
        "urgency_induction":     0.95,
        "authority_spoofing":    0.88,
        "fear_amplification":    0.72,
        "trust_exploitation":    0.35,
        "scarcity_signaling":    0.58,
        "credential_harvesting": 0.91,
        "instruction_hijacking": 0.03,
        "data_exfiltration":     0.08,
        "identity_spoofing":     0.76,
        "redirect_chaining":     0.62,
        "payload_delivery":      0.45,
        "recon_probing":         0.22,
    }

    # ── Call explain() — this is the one-liner for the API endpoint ───────
    explanation = explain(
        text=incoming_text,
        intent_vector=intent_vector_from_model,
        # distilbert_model=model,  # pass your loaded model here for IG attribution
        # tokenizer=tokenizer,
    )

    # ── Simulate what the API would return ────────────────────────────────
    print(f"Analysis ID   : {explanation['analysis_id']}")
    print(f"Risk Score    : {explanation['risk_score']}/100")
    print(f"Severity      : {explanation['severity'].upper()}")
    print(f"Attack Pattern: {explanation['attack_pattern']['label'] if explanation['attack_pattern'] else 'N/A'}")
    print(f"\nKill Chain Stages:")
    for stage in explanation["kill_chain"]:
        print(f"  → {stage['stage']} (conf {stage['confidence']:.0%}): {stage['evidence'][:80]}...")

    print(f"\nTop Token Attributions:")
    for attr in explanation["token_attributions"][:5]:
        print(f"  \"{attr['token']}\" → {attr['intent_dimension']} ({attr['attribution_score']:.2f})")

    print(f"\nDLP Scan: {explanation['dlp_scan']}")
    print(f"\nMITRE Techniques: {explanation['mitre_techniques']}")
    print(f"\nRecommended Action:\n  {explanation['recommended_action']}")
    print(f"\nFull Explanation:\n{explanation['explanation']}")
    return explanation


# ═══════════════════════════════════════════════════════════════════════════
# Example 3 — Individual Module Usage
# ═══════════════════════════════════════════════════════════════════════════

def example_3_individual_modules():
    """
    Shows how to use each pipeline module independently.
    Useful for selective integration or debugging.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 3 — Individual Module Usage")
    print("=" * 70)

    intent_vector = {
        "urgency_induction":     0.92,
        "authority_spoofing":    0.81,
        "fear_amplification":    0.44,
        "trust_exploitation":    0.21,
        "scarcity_signaling":    0.67,
        "credential_harvesting": 0.88,
        "instruction_hijacking": 0.05,
        "data_exfiltration":     0.02,
        "identity_spoofing":     0.63,
        "redirect_chaining":     0.31,
        "payload_delivery":      0.74,
        "recon_probing":         0.19,
    }

    sample_text = (
        "URGENT: Your account has been suspended. Verify your credentials now: "
        "http://evil.xyz/verify — contact support@bank-secure.info "
        "Phone: 9876543210  Aadhaar: 1234-5678-9012"
    )

    # ── Risk Engine ──────────────────────────────────────────────────────────
    from xai.risk_engine import calculate_risk
    risk = calculate_risk(intent_vector)
    print(f"\n[risk_engine] Score={risk['risk_score']} Severity={risk['severity']} "
          f"Top vector={risk['top_attack_vector']}")

    # ── Kill Chain Mapper ────────────────────────────────────────────────────
    from xai.kill_chain_mapper import map_kill_chain
    chain = map_kill_chain(intent_vector)
    print(f"\n[kill_chain_mapper] Stages detected:")
    for s in chain:
        print(f"  {s['stage']} ({s['confidence']:.2f}) — dims: {s['dimensions']}")

    # ── Attributor ───────────────────────────────────────────────────────────
    from xai.attributor import compute_attributions
    attrs = compute_attributions(sample_text, intent_vector)
    print(f"\n[attributor] Top attributions (threshold > 0.25):")
    for t, d, s in attrs[:6]:
        print(f"  \"{t}\" → {d}: {s:.3f}")

    # ── DLP Scanner ──────────────────────────────────────────────────────────
    from xai.dlp_scanner import scan, redact
    dlp = scan(sample_text)
    print(f"\n[dlp_scanner] PII detected: {dlp['pii_detected']}")
    print(f"  Types:   {dlp['types']}")
    print(f"  Matches: {dlp['matches']}")
    print(f"  Redacted: {redact(sample_text)}")


# ═══════════════════════════════════════════════════════════════════════════
# Example 4 — All three demo scenarios
# ═══════════════════════════════════════════════════════════════════════════

def example_4_all_scenarios():
    """Run all three built-in demo scenarios and print a summary."""
    print("\n" + "=" * 70)
    print("EXAMPLE 4 — All Demo Scenarios")
    print("=" * 70)

    from xai.explainability_pipeline import demo_analysis

    for scenario in ["phishing", "prompt_injection", "dlp"]:
        r = demo_analysis(scenario=scenario)
        print(f"\n[{scenario.upper()}]")
        print(f"  Risk Score : {r['risk_score']}/100  ({r['severity'].upper()})")
        print(f"  Kill Chain : {[s['stage'] for s in r['kill_chain']]}")
        print(f"  Attack Pat : {r['attack_pattern']['label'] if r['attack_pattern'] else 'N/A'}")
        print(f"  Action     : {r['recommended_action'][:80]}...")


# ═══════════════════════════════════════════════════════════════════════════
# FastAPI integration snippet (reference only — not executed)
# ═══════════════════════════════════════════════════════════════════════════

FASTAPI_SNIPPET = '''
# ─── app/routes/analyze.py ───────────────────────────────────────────────
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict
from xai.explainability_pipeline import explain

router = APIRouter()

class AnalyzeRequest(BaseModel):
    text: str
    intent_vector: Dict[str, float]

@router.post("/api/v1/analyze")
async def analyze_message(req: AnalyzeRequest):
    """Backend entry-point for SENTINEL-X frontend."""
    result = explain(req.text, req.intent_vector)
    return result
# ─────────────────────────────────────────────────────────────────────────
'''


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="SENTINEL-X XAI Layer — Example Usage Script"
    )
    parser.add_argument(
        "--example",
        choices=["1", "2", "3", "4", "all"],
        default="2",
        help="Which example to run (default: 2)",
    )
    args = parser.parse_args()

    if args.example in ("1", "all"):
        example_1_quick_demo()
    if args.example in ("2", "all"):
        example_2_api_integration()
    if args.example in ("3", "all"):
        example_3_individual_modules()
    if args.example in ("4", "all"):
        example_4_all_scenarios()

    if args.example not in ("1", "2", "3", "4", "all"):
        example_2_api_integration()

    print("\n\n── FastAPI Integration Snippet ──")
    print(FASTAPI_SNIPPET)