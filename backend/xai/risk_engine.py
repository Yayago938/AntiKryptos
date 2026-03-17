"""
risk_engine.py
SENTINEL-X — Adversarial Intent Graph Cyber Defense System

Composite threat-score calculator.
Translates a 12-dimensional intent vector into a 0-100 risk score,
a severity band, and the most dangerous identified attack vector.
"""

from __future__ import annotations

from typing import Dict, List, Tuple


# ===========================================================================
# Weight Table
# ===========================================================================
# Raw weights reflect the relative danger of each intent dimension.
# Normalised internally so a fully-saturated vector scores 100.

_RAW_WEIGHTS: Dict[str, float] = {
    "credential_harvesting":  10.0,   # direct account takeover risk
    "instruction_hijacking":  10.0,   # AI/system prompt injection
    "identity_spoofing":       8.0,   # impersonation / fraud
    "urgency_induction":       7.0,   # manipulation pressure
    "payload_delivery":        7.0,   # malware delivery
    "authority_spoofing":      6.0,   # trust manipulation
    "data_exfiltration":       6.0,   # data breach risk
    "fear_amplification":      5.0,   # psychological coercion
    "redirect_chaining":       5.0,   # drive-by / watering-hole
    "scarcity_signaling":      4.0,   # social engineering pressure
    "trust_exploitation":      4.0,   # relationship abuse
    "recon_probing":           3.0,   # information gathering
}

# Severity thresholds
_SEVERITY_BANDS: List[Tuple[int, str]] = [
    (85, "critical"),
    (65, "high"),
    (40, "medium"),
    (20, "low"),
    (0,  "informational"),
]

# Recommended actions per severity
_SEVERITY_ACTIONS: Dict[str, str] = {
    "critical": (
        "Block this message immediately. Do NOT click any links or download attachments. "
        "Report to your security team and change any credentials mentioned in the message."
    ),
    "high": (
        "Do not click links or provide personal information. "
        "Verify the sender through an independent trusted channel before taking any action."
    ),
    "medium": (
        "Treat with caution. Verify the sender's identity before responding. "
        "Do not provide sensitive information."
    ),
    "low": (
        "Exercise caution. If unexpected, confirm legitimacy through a known-good contact."
    ),
    "informational": (
        "Low risk detected. Normal monitoring applies."
    ),
}

# ---------------------------------------------------------------------------
# Normalised weight map (each value = percentage-point contribution per unit
# activation; Sigma over all dims at activation=1.0 equals exactly 100).
# ---------------------------------------------------------------------------
_TOTAL_WEIGHT: float = sum(_RAW_WEIGHTS.values())   # 75.0
WEIGHTS: Dict[str, float] = {
    dim: (w / _TOTAL_WEIGHT) * 100.0
    for dim, w in _RAW_WEIGHTS.items()
}


# ===========================================================================
# Co-activation bonus table
# ===========================================================================
# Bonus points added when specific combinations of dimensions fire together.
# Each rule is (list_of_dims, min_activation_each, bonus_points).
# Bonuses stack but the total bonus is capped at 40.0 points.

_COACTIVATION_RULES: List[Tuple[List[str], float, float]] = [
    # Social-engineering credential attack
    (["urgency_induction", "authority_spoofing", "credential_harvesting"], 0.70, 12.0),
    # Fear + credential harvesting (phishing)
    (["fear_amplification", "credential_harvesting"], 0.40, 6.0),
    # Payload with redirect (drive-by delivery)
    (["payload_delivery", "redirect_chaining"], 0.50, 5.0),
    # Identity fraud
    (["identity_spoofing", "authority_spoofing"], 0.60, 5.0),
    # Data exfil with identity spoofing
    (["data_exfiltration", "identity_spoofing"], 0.50, 5.0),
    # Prompt injection
    (["instruction_hijacking", "data_exfiltration"], 0.55, 8.0),
    # Urgency + scarcity double-pressure
    (["urgency_induction", "scarcity_signaling"], 0.60, 4.0),
    # Full social engineering stack
    (["urgency_induction", "authority_spoofing", "fear_amplification",
      "credential_harvesting", "identity_spoofing"], 0.40, 15.0),
]

_MAX_COACTIVATION_BONUS: float = 35.0


# ===========================================================================
# Public API
# ===========================================================================

def calculate_risk(intent_vector: Dict[str, float]) -> Dict:
    """
    Calculate a composite threat score from an intent vector.

    Algorithm
    ---------
    1. Weighted sum : score = Sigma (weight_i * activation_i)
    2. Co-activation bonus: additional points when multiple threat
       dimensions fire simultaneously (sophisticated multi-vector attacks).
    3. Clamp result to [0, 100].

    Parameters
    ----------
    intent_vector : dict
        12-dimensional float dict (values 0-1).

    Returns
    -------
    dict:
        {
            "risk_score":           int   (0-100),
            "severity":             str,
            "top_attack_vector":    str,
            "weighted_breakdown":   dict  {dim: contribution},
            "dimension_severity":   dict  {dim: severity_label},
            "co_activation_bonus":  float,
            "recommended_action":   str
        }
    """
    # --- Step 1: Weighted sum -------------------------------------------
    breakdown: Dict[str, float] = {}
    raw_score: float = 0.0

    for dim, weight in WEIGHTS.items():
        activation = float(intent_vector.get(dim, 0.0))
        # Clamp activation to [0, 1] defensively
        activation = max(0.0, min(1.0, activation))
        contribution = weight * activation
        breakdown[dim] = round(contribution, 3)
        raw_score += contribution

    # --- Step 2: Co-activation bonus ------------------------------------
    total_bonus: float = 0.0
    triggered_rules: List[str] = []

    for dims, threshold, bonus in _COACTIVATION_RULES:
        if all(intent_vector.get(d, 0.0) >= threshold for d in dims):
            total_bonus += bonus
            triggered_rules.append(
                f"{'+'.join(d[:4] for d in dims)}>{threshold:.0%} (+{bonus:.0f}pt)"
            )

    co_activation_bonus = min(total_bonus, _MAX_COACTIVATION_BONUS)

    # --- Step 3: Final score -------------------------------------------
    final_score = min(100.0, raw_score + co_activation_bonus)
    final_score_int = round(final_score)

    # --- Step 4: Severity band -----------------------------------------
    severity = "informational"
    for threshold, label in _SEVERITY_BANDS:
        if final_score_int >= threshold:
            severity = label
            break

    # --- Step 5: Top attack vector (highest weighted contribution) -----
    ranked = sorted(breakdown.items(), key=lambda x: x[1], reverse=True)
    top_attack_vector = ranked[0][0] if ranked else "unknown"

    # --- Step 6: Per-dimension severity flags --------------------------
    dim_flags: Dict[str, str] = {}
    for dim, activation in intent_vector.items():
        v = float(activation)
        if v >= 0.80:
            dim_flags[dim] = "critical"
        elif v >= 0.60:
            dim_flags[dim] = "high"
        elif v >= 0.40:
            dim_flags[dim] = "medium"
        elif v >= 0.20:
            dim_flags[dim] = "low"
        else:
            dim_flags[dim] = "negligible"

    return {
        "risk_score": final_score_int,
        "severity": severity,
        "top_attack_vector": top_attack_vector,
        "weighted_breakdown": breakdown,
        "dimension_severity": dim_flags,
        "co_activation_bonus": round(co_activation_bonus, 2),
        "co_activation_rules_triggered": triggered_rules,
        "recommended_action": _SEVERITY_ACTIONS[severity],
    }


def get_severity_label(score: int) -> str:
    """Utility: return severity label for a raw integer risk score."""
    for threshold, label in _SEVERITY_BANDS:
        if score >= threshold:
            return label
    return "informational"


# ---------------------------------------------------------------------------
# Smoke-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import json

    sample = {
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

    result = calculate_risk(sample)
    print(json.dumps(result, indent=2))
    print(f"\nExpected: ~87 | Got: {result['risk_score']}")


# ===========================================================================
# Final Human-Readable Explanation Generator
# ===========================================================================

# Per-dimension narrative sentences, keyed by intent dimension name.
_DIM_NARRATIVES: Dict[str, str] = {
    "urgency_induction": (
        "The message artificially manufactures a time-pressure crisis to override "
        "rational decision-making and force an immediate, unthinking response."
    ),
    "authority_spoofing": (
        "The sender falsely impersonates a trusted institution — such as a bank, "
        "government body, or technology company — to suppress the recipient's scepticism."
    ),
    "fear_amplification": (
        "Threatening language (account suspension, legal action, permanent block) is "
        "used to induce fear and panic, making the victim more likely to comply without verifying."
    ),
    "trust_exploitation": (
        "The attacker exploits an implied or existing relationship to lower the "
        "recipient's guard and bypass normal security instincts."
    ),
    "scarcity_signaling": (
        "A false sense of scarcity or expiry ('limited time', 'expires in 2 hours') "
        "is injected to prevent the victim from pausing to think critically."
    ),
    "credential_harvesting": (
        "The core goal of this message is to steal authentication credentials — "
        "username, password, OTP, or PIN — to gain unauthorised account access."
    ),
    "instruction_hijacking": (
        "Embedded override commands attempt to hijack AI system instructions, "
        "bypass safety filters, or redirect automated workflows to attacker-controlled behaviour."
    ),
    "data_exfiltration": (
        "The message is designed to transfer sensitive data — personal records, "
        "financial details, or organisational information — to an external attacker."
    ),
    "identity_spoofing": (
        "A forged sender identity (spoofed email domain, cloned display name, or "
        "fake brand) is used to make the message appear legitimate."
    ),
    "redirect_chaining": (
        "The message routes the victim through one or more intermediate URLs — often "
        "shortened or legitimate-looking — before landing on a malicious destination."
    ),
    "payload_delivery": (
        "This message serves as the delivery vehicle for a malicious file, executable, "
        "macro-embedded document, or drive-by download exploit."
    ),
    "recon_probing": (
        "The message probes for information about the target's environment, credentials, "
        "or relationships to fuel a more refined follow-up attack."
    ),
}

# Intent-stage labels for each dimension
_DIM_INTENT_STAGE: Dict[str, str] = {
    "urgency_induction":     "Social Engineering — Psychological Pressure",
    "authority_spoofing":    "Social Engineering — Identity Deception",
    "fear_amplification":    "Social Engineering — Emotional Manipulation",
    "trust_exploitation":    "Social Engineering — Relationship Abuse",
    "scarcity_signaling":    "Social Engineering — Artificial Scarcity",
    "credential_harvesting": "Exploitation — Credential Theft",
    "instruction_hijacking": "Exploitation — AI/System Prompt Injection",
    "data_exfiltration":     "Actions on Objectives — Data Theft",
    "identity_spoofing":     "Delivery — Identity Forgery",
    "redirect_chaining":     "Delivery — Malicious Redirect",
    "payload_delivery":      "Delivery — Malware/Payload Drop",
    "recon_probing":         "Reconnaissance — Target Intelligence Gathering",
}

# Severity-specific closing advisory
_FINAL_ADVISORY: Dict[str, str] = {
    "critical": (
        "IMMEDIATE ACTION REQUIRED: This message is a confirmed multi-vector cyber attack. "
        "Do not interact with any link, attachment, or phone number contained in it. "
        "Quarantine the message, reset any credentials you may have already entered, "
        "and report the incident to your security team or CERT-In (cert-in.org.in)."
    ),
    "high": (
        "HIGH RISK: Strong adversarial signals detected. Treat this message as hostile "
        "until independently verified. Do not provide any personal or organisational "
        "information. Contact the purported sender through a known-good, official channel."
    ),
    "medium": (
        "CAUTION: Multiple suspicious patterns detected. Do not act on instructions "
        "in this message before verifying the sender's identity through an official source. "
        "When in doubt, delete and report."
    ),
    "low": (
        "LOW RISK: Minor suspicious signals present. Exercise normal vigilance and "
        "confirm legitimacy before responding or clicking any links."
    ),
    "informational": (
        "INFORMATIONAL: No significant threat signals detected. Continue with standard "
        "security awareness practices."
    ),
}


def generate_final_explanation(intent_vector: Dict[str, float]) -> str:
    """
    Generate a structured, human-readable final explanation that answers:

      1. What is the overall threat assessment?
      2. Which intent dimensions fired and what does each mean?
      3. What is the attacker's goal / intent stage?
      4. What concrete action should the user take?

    Parameters
    ----------
    intent_vector : dict
        12-dimensional float dict (values 0-1).

    Returns
    -------
    str — multi-line plain-text explanation suitable for display in a
          security dashboard, email alert, or API response body.
    """
    risk = calculate_risk(intent_vector)
    score      = risk["risk_score"]
    severity   = risk["severity"]
    top_vector = risk["top_attack_vector"]
    bonus      = risk["co_activation_bonus"]

    # ── Section 1: Headline ──────────────────────────────────────────────────
    divider = "=" * 68
    lines: List[str] = [
        divider,
        "  SENTINEL-X  |  THREAT EXPLANATION REPORT",
        divider,
        f"  Risk Score   : {score} / 100",
        f"  Severity     : {severity.upper()}",
        f"  Primary Vec  : {top_vector.replace('_', ' ').title()}",
        f"  Co-Act Bonus : +{bonus:.1f} pts  "
        f"(multi-vector co-activation penalty)",
        divider,
    ]

    # ── Section 2: Active intent dimensions ─────────────────────────────────
    active = sorted(
        [(d, v) for d, v in intent_vector.items() if v >= 0.30],
        key=lambda x: x[1],
        reverse=True,
    )

    lines.append("")
    lines.append("  DETECTED INTENT SIGNALS")
    lines.append("  " + "-" * 64)

    for dim, val in active:
        stage    = _DIM_INTENT_STAGE.get(dim, "Unknown Stage")
        narrative = _DIM_NARRATIVES.get(dim, "Adversarial signal detected.")
        bar_len  = int(val * 20)          # 20-char bar
        bar      = "█" * bar_len + "░" * (20 - bar_len)
        flag     = risk["dimension_severity"].get(dim, "").upper()

        lines.append(f"\n  [{flag:11}]  {dim.replace('_', ' ').upper():<28}  {val:.2f}  |{bar}|")
        lines.append(f"  Stage    :  {stage}")
        lines.append(f"  Meaning  :  {narrative}")

    # ── Section 3: Co-activation rules that fired ────────────────────────────
    if risk["co_activation_rules_triggered"]:
        lines.append("")
        lines.append("  " + "-" * 64)
        lines.append("  MULTI-VECTOR ATTACK COMBINATIONS DETECTED")
        lines.append("  " + "-" * 64)
        for rule in risk["co_activation_rules_triggered"]:
            lines.append(f"    •  {rule}")
        lines.append(
            "\n  Multiple high-confidence dimensions firing together indicate a"
            "\n  sophisticated, coordinated attack rather than a single isolated signal."
        )

    # ── Section 4: Attacker Goal Summary ────────────────────────────────────
    lines.append("")
    lines.append("  " + "-" * 64)
    lines.append("  ATTACKER INTENT & GOAL ASSESSMENT")
    lines.append("  " + "-" * 64)

    # Determine dominant intent category
    social_eng_score = sum(
        intent_vector.get(d, 0.0)
        for d in ["urgency_induction", "authority_spoofing", "fear_amplification",
                  "trust_exploitation", "scarcity_signaling"]
    )
    exploitation_score = sum(
        intent_vector.get(d, 0.0)
        for d in ["credential_harvesting", "instruction_hijacking", "identity_spoofing"]
    )
    delivery_score = sum(
        intent_vector.get(d, 0.0)
        for d in ["payload_delivery", "redirect_chaining"]
    )
    exfil_score = sum(
        intent_vector.get(d, 0.0)
        for d in ["data_exfiltration", "recon_probing"]
    )

    goal_map = {
        "Social Engineering (Manipulation)": social_eng_score,
        "Exploitation (Credential / System Access)": exploitation_score,
        "Delivery (Malware / Redirect)": delivery_score,
        "Intelligence Gathering / Data Theft": exfil_score,
    }
    sorted_goals = sorted(goal_map.items(), key=lambda x: x[1], reverse=True)

    lines.append("")
    lines.append("  Attacker goal ranking (by signal strength):")
    for rank, (goal, gscore) in enumerate(sorted_goals, 1):
        bar_len = int(min(gscore / 3.0, 1.0) * 20)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        lines.append(f"    {rank}. {goal:<46}  |{bar}|  ({gscore:.2f})")

    primary_goal = sorted_goals[0][0]
    lines.append(f"\n  PRIMARY ATTACKER GOAL:  {primary_goal}")
    lines.append(
        f"\n  The dominant intent pattern is '{top_vector.replace('_', ' ')}' "
        f"(activation {intent_vector.get(top_vector, 0.0):.2f}). "
        f"This message most likely represents a {sorted_goals[0][0].lower()} "
        f"attack targeting the recipient's "
        + (
            "authentication credentials and account access."
            if "Exploitation" in primary_goal
            else "psychological state to drive unsafe behaviour."
            if "Social" in primary_goal
            else "system via a malicious payload or link."
            if "Delivery" in primary_goal
            else "personal or organisational data."
        )
    )

    # ── Section 5: Recommended Action ────────────────────────────────────────
    lines.append("")
    lines.append("  " + "-" * 64)
    lines.append("  RECOMMENDED ACTION")
    lines.append("  " + "-" * 64)
    lines.append(f"\n  {_FINAL_ADVISORY[severity]}")

    lines.append("")
    lines.append(divider)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Extended smoke-test — run the new explainer
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import json

    sample = {
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

    result = calculate_risk(sample)
    print(json.dumps(result, indent=2))
    print(f"\nExpected: ~87 | Got: {result['risk_score']}\n")
    print(generate_final_explanation(sample))