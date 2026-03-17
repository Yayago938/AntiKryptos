"""
kill_chain_mapper.py
SENTINEL-X — Adversarial Intent Graph Cyber Defense System
Maps 12-dimensional intent vectors to Lockheed Martin Cyber Kill Chain stages.
"""

from typing import List, Dict, Any


# ---------------------------------------------------------------------------
# Stage definitions: each entry lists the primary dimensions that vote for it
# and a human-readable description used in evidence strings.
# ---------------------------------------------------------------------------
STAGE_RULES = [
    # ── Reconnaissance ──────────────────────────────────────────────────────
    {
        "stage": "Reconnaissance",
        "primary_dims": ["recon_probing"],
        "secondary_dims": ["identity_spoofing"],
        "threshold": 0.30,
        "description": "Attacker is gathering information about the target environment",
    },
    # ── Weaponization ───────────────────────────────────────────────────────
    {
        "stage": "Weaponization",
        "primary_dims": ["payload_delivery", "instruction_hijacking"],
        "secondary_dims": ["redirect_chaining"],
        "threshold": 0.40,
        "description": "Malicious payload or exploit is being crafted or embedded",
    },
    # ── Delivery ────────────────────────────────────────────────────────────
    {
        "stage": "Delivery",
        "primary_dims": ["redirect_chaining", "payload_delivery"],
        "secondary_dims": ["urgency_induction", "authority_spoofing", "scarcity_signaling"],
        "threshold": 0.35,
        "description": "Attack is being transmitted to the victim",
    },
    # ── Exploitation ────────────────────────────────────────────────────────
    {
        "stage": "Exploitation",
        "primary_dims": ["credential_harvesting", "instruction_hijacking"],
        "secondary_dims": ["data_exfiltration", "identity_spoofing"],
        "threshold": 0.35,
        "description": "Attacker is exploiting trust or credentials to gain access",
    },
    # ── Actions on Objectives ───────────────────────────────────────────────
    {
        "stage": "Actions on Objectives",
        "primary_dims": ["data_exfiltration"],
        "secondary_dims": ["credential_harvesting", "instruction_hijacking"],
        "threshold": 0.30,
        "description": "Attacker is completing their final goal: data theft or system compromise",
    },
]

# ---------------------------------------------------------------------------
# Multi-dimension composite rules (override or augment single-dim scoring)
# ---------------------------------------------------------------------------
COMPOSITE_RULES = [
    {
        "label": "Social Engineering Delivery",
        "stage": "Delivery",
        "conditions": [("urgency_induction", 0.70), ("authority_spoofing", 0.70)],
        "confidence_bonus": 0.15,
        "evidence": (
            "Message combines urgency pressure with authority impersonation — "
            "classic social-engineering delivery pattern."
        ),
    },
    {
        "label": "Phishing Credential Attack",
        "stage": "Exploitation",
        "conditions": [("credential_harvesting", 0.60), ("fear_amplification", 0.40)],
        "confidence_bonus": 0.12,
        "evidence": (
            "Fear-driven messaging combined with credential harvesting signals "
            "a targeted phishing attack."
        ),
    },
    {
        "label": "Identity-Fraud Recon",
        "stage": "Reconnaissance",
        "conditions": [("identity_spoofing", 0.50), ("recon_probing", 0.30)],
        "confidence_bonus": 0.10,
        "evidence": (
            "Identity spoofing used alongside reconnaissance — attacker may be "
            "building a target profile."
        ),
    },
    {
        "label": "Scarcity-Driven Redirect",
        "stage": "Delivery",
        "conditions": [("scarcity_signaling", 0.55), ("redirect_chaining", 0.35)],
        "confidence_bonus": 0.10,
        "evidence": (
            "Scarcity pressure combined with redirect chaining — victim is being "
            "driven to a malicious landing page."
        ),
    },
]


# ---------------------------------------------------------------------------
# Helper: compute a weighted confidence score for a single stage rule
# ---------------------------------------------------------------------------
def _score_stage(intent_vector: Dict[str, float], rule: Dict[str, Any]) -> float:
    """
    Returns a 0–1 confidence float for how strongly the intent vector
    matches this kill-chain stage rule.
    """
    primary_scores = [
        intent_vector.get(d, 0.0) for d in rule["primary_dims"]
    ]
    secondary_scores = [
        intent_vector.get(d, 0.0) for d in rule["secondary_dims"]
    ]

    if not primary_scores:
        return 0.0

    primary_avg = sum(primary_scores) / len(primary_scores)

    secondary_avg = (
        sum(secondary_scores) / len(secondary_scores) if secondary_scores else 0.0
    )

    # Primary dimensions carry 70 % weight, secondary 30 %
    raw_score = 0.70 * primary_avg + 0.30 * secondary_avg

    # Must exceed threshold to be included
    return raw_score if raw_score >= rule["threshold"] else 0.0


# ---------------------------------------------------------------------------
# Helper: collect the contributing dimensions above a minimum contribution
# ---------------------------------------------------------------------------
def _active_dims(
    intent_vector: Dict[str, float],
    primary: List[str],
    secondary: List[str],
    min_val: float = 0.25,
) -> List[str]:
    active = []
    for d in primary + secondary:
        if intent_vector.get(d, 0.0) >= min_val:
            active.append(d)
    return active


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def map_kill_chain(intent_vector: Dict[str, float]) -> List[Dict[str, Any]]:
    """
    Map an intent vector to one or more Cyber Kill Chain stages.

    Parameters
    ----------
    intent_vector : dict
        12-dimensional float dict (values 0–1).

    Returns
    -------
    list of dicts, sorted by descending confidence:
        [
            {
                "stage": str,
                "confidence": float,
                "dimensions": [str, ...],
                "evidence": str
            },
            ...
        ]
    """
    results: List[Dict[str, Any]] = []

    # ── 1. Score each base stage rule ────────────────────────────────────────
    for rule in STAGE_RULES:
        confidence = _score_stage(intent_vector, rule)
        if confidence == 0.0:
            continue

        active = _active_dims(
            intent_vector,
            rule["primary_dims"],
            rule["secondary_dims"],
        )
        if not active:
            continue

        # Build evidence string from active dimension values
        dim_summary = ", ".join(
            f"{d}={intent_vector.get(d, 0):.2f}" for d in active
        )
        evidence = f"{rule['description']}. Active signals: {dim_summary}."

        results.append(
            {
                "stage": rule["stage"],
                "confidence": round(confidence, 4),
                "dimensions": active,
                "evidence": evidence,
            }
        )

    # ── 2. Apply composite (multi-dimension) rules ───────────────────────────
    for crule in COMPOSITE_RULES:
        if all(
            intent_vector.get(dim, 0.0) >= threshold
            for dim, threshold in crule["conditions"]
        ):
            # Find if this stage already exists; if so, boost confidence
            existing = next(
                (r for r in results if r["stage"] == crule["stage"]), None
            )
            triggered_dims = [d for d, _ in crule["conditions"]]

            if existing:
                existing["confidence"] = min(
                    1.0, existing["confidence"] + crule["confidence_bonus"]
                )
                # Merge evidence
                existing["evidence"] += f" [{crule['label']}: {crule['evidence']}]"
                for td in triggered_dims:
                    if td not in existing["dimensions"]:
                        existing["dimensions"].append(td)
            else:
                results.append(
                    {
                        "stage": crule["stage"],
                        "confidence": round(
                            min(1.0, 0.50 + crule["confidence_bonus"]), 4
                        ),
                        "dimensions": triggered_dims,
                        "evidence": f"[{crule['label']}] {crule['evidence']}",
                    }
                )

    # ── 3. Deduplicate by stage (keep highest confidence) ────────────────────
    deduped: Dict[str, Dict[str, Any]] = {}
    for entry in results:
        stage = entry["stage"]
        if stage not in deduped or entry["confidence"] > deduped[stage]["confidence"]:
            deduped[stage] = entry

    # ── 4. Sort and return ───────────────────────────────────────────────────
    sorted_results = sorted(
        deduped.values(), key=lambda x: x["confidence"], reverse=True
    )
    return sorted_results


# ---------------------------------------------------------------------------
# Quick smoke-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import json

    sample = {
        "urgency_induction": 0.92,
        "authority_spoofing": 0.81,
        "fear_amplification": 0.44,
        "trust_exploitation": 0.21,
        "scarcity_signaling": 0.67,
        "credential_harvesting": 0.88,
        "instruction_hijacking": 0.05,
        "data_exfiltration": 0.02,
        "identity_spoofing": 0.63,
        "redirect_chaining": 0.31,
        "payload_delivery": 0.74,
        "recon_probing": 0.19,
    }

    chain = map_kill_chain(sample)
    print(json.dumps(chain, indent=2))