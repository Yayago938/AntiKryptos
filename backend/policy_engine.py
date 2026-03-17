"""
SENTINEL-X Policy Engine
"""

INTENT_DIMENSIONS = [
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
    "recon_probing",
]

ORG_PROFILES = {
    "general_consumer": {
        "description": "Default consumer-facing product",
        "thresholds": {
            "urgency_induction":     [0.4, 0.7, 0.9],
            "authority_spoofing":    [0.4, 0.7, 0.9],
            "fear_amplification":    [0.4, 0.7, 0.9],
            "trust_exploitation":    [0.4, 0.7, 0.9],
            "scarcity_signaling":    [0.4, 0.7, 0.9],
            "credential_harvesting": [0.3, 0.6, 0.85],
            "instruction_hijacking": [0.3, 0.6, 0.85],
            "data_exfiltration":     [0.3, 0.6, 0.85],
            "identity_spoofing":     [0.4, 0.7, 0.9],
            "redirect_chaining":     [0.4, 0.7, 0.9],
            "payload_delivery":      [0.3, 0.6, 0.85],
            "recon_probing":         [0.4, 0.7, 0.9],
        },
        "actions": {
            "low":      "log_silently",
            "medium":   "warn_user",
            "high":     "block_and_alert",
            "critical": "block_log_alert",
        },
    },
    "bank": {
        "description": "Banking / financial institution",
        "thresholds": {
            "urgency_induction":     [0.35, 0.6,  0.8],
            "authority_spoofing":    [0.3,  0.55, 0.75],
            "fear_amplification":    [0.35, 0.6,  0.8],
            "trust_exploitation":    [0.3,  0.55, 0.75],
            "scarcity_signaling":    [0.35, 0.6,  0.8],
            "credential_harvesting": [0.2,  0.45, 0.65],
            "instruction_hijacking": [0.2,  0.4,  0.6],
            "data_exfiltration":     [0.2,  0.45, 0.65],
            "identity_spoofing":     [0.25, 0.5,  0.7],
            "redirect_chaining":     [0.3,  0.55, 0.75],
            "payload_delivery":      [0.25, 0.5,  0.7],
            "recon_probing":         [0.3,  0.55, 0.75],
        },
        "actions": {
            "low":      "log_silently",
            "medium":   "warn_user_and_log",
            "high":     "block_and_notify_soc",
            "critical": "block_log_incident_report",
        },
    },
    "hospital": {
        "description": "Healthcare — prioritise patient data protection",
        "thresholds": {
            "urgency_induction":     [0.4,  0.65, 0.85],
            "authority_spoofing":    [0.35, 0.6,  0.8],
            "fear_amplification":    [0.4,  0.65, 0.85],
            "trust_exploitation":    [0.35, 0.6,  0.8],
            "scarcity_signaling":    [0.4,  0.65, 0.85],
            "credential_harvesting": [0.25, 0.5,  0.7],
            "instruction_hijacking": [0.2,  0.45, 0.65],
            "data_exfiltration":     [0.15, 0.35, 0.55],
            "identity_spoofing":     [0.3,  0.55, 0.75],
            "redirect_chaining":     [0.35, 0.6,  0.8],
            "payload_delivery":      [0.25, 0.5,  0.7],
            "recon_probing":         [0.3,  0.55, 0.75],
        },
        "actions": {
            "low":      "log_silently",
            "medium":   "warn_and_log",
            "high":     "block_and_alert_compliance",
            "critical": "block_full_incident_response",
        },
    },
}

ACTION_LABELS = {
    "log_silently":                 "Input logged for monitoring. No user action required.",
    "warn_user":                    "Warning shown to user. Proceed with caution advised.",
    "warn_user_and_log":            "Warning shown to user. Event logged for security review.",
    "block_and_alert":              "Input blocked. User alerted. Security team notified.",
    "block_and_notify_soc":         "Input blocked. SOC team notified for immediate review.",
    "block_log_alert":              "Input blocked. Full audit log created. Incident alert raised.",
    "block_log_incident_report":    "Input blocked. Incident report generated. Compliance team notified.",
    "block_and_alert_compliance":   "Input blocked. Compliance officer alerted per HIPAA/DPDP protocol.",
    "block_full_incident_response": "Input blocked. Full incident response protocol activated.",
}


def classify_severity(score: float, thresholds: list) -> str:
    if score >= thresholds[2]:
        return "critical"
    elif score >= thresholds[1]:
        return "high"
    elif score >= thresholds[0]:
        return "medium"
    else:
        return "low"


def compute_risk_score(intent_vector: dict) -> int:
    weights = {
        "urgency_induction":     0.07,
        "authority_spoofing":    0.09,
        "fear_amplification":    0.07,
        "trust_exploitation":    0.07,
        "scarcity_signaling":    0.06,
        "credential_harvesting": 0.12,
        "instruction_hijacking": 0.12,
        "data_exfiltration":     0.12,
        "identity_spoofing":     0.09,
        "redirect_chaining":     0.06,
        "payload_delivery":      0.08,
        "recon_probing":         0.05,
    }
    weighted = sum(intent_vector.get(dim, 0.0) * w for dim, w in weights.items())
    return min(100, round(weighted * 100))


def evaluate(
    intent_vector: dict,
    org_profile:   str  = "general_consumer",
    gate_flags:    list = None,
    risk_score:    int  = None,
    severity:      str  = None,
) -> dict:
    gate_flags = gate_flags or []
    profile    = ORG_PROFILES.get(org_profile, ORG_PROFILES["general_consumer"])

    if "instruction_override" in gate_flags:
        return {
            "risk_score":    100,
            "severity":      "critical",
            "action":        "block_log_alert",
            "action_label":  ACTION_LABELS["block_log_alert"],
            "top_threats":   [{"dimension": "instruction_hijacking", "score": 1.0, "severity": "critical"}],
            "per_dimension": {dim: {"score": intent_vector.get(dim, 0.0), "severity": "low"} for dim in INTENT_DIMENSIONS},
        }

    if risk_score is None:
        risk_score = compute_risk_score(intent_vector)

    per_dimension  = {}
    worst_severity = "low"
    severity_order = ["low", "medium", "high", "critical"]

    for dim in INTENT_DIMENSIONS:
        score      = intent_vector.get(dim, 0.0)
        thresholds = profile["thresholds"].get(dim, [0.4, 0.7, 0.9])
        sev        = classify_severity(score, thresholds)
        per_dimension[dim] = {"score": round(score, 4), "severity": sev}
        if severity_order.index(sev) > severity_order.index(worst_severity):
            worst_severity = sev

    if severity is not None:
        worst_severity = severity

    if "jailbreak_pattern" in gate_flags and worst_severity in ("low", "medium"):
        worst_severity = "high"

    action_code = profile["actions"].get(worst_severity, "log_silently")

    top_threats = sorted(
        [
            {"dimension": d, "score": v["score"], "severity": v["severity"]}
            for d, v in per_dimension.items()
            if v["score"] >= 0.4
        ],
        key=lambda x: x["score"],
        reverse=True,
    )[:5]

    return {
        "risk_score":   risk_score,
        "severity":     worst_severity,
        "action":       action_code,
        "action_label": ACTION_LABELS.get(action_code, action_code),
        "top_threats":  top_threats,
        "per_dimension":per_dimension,
    }


def list_profiles() -> list:
    return [
        {"id": k, "description": v["description"]}
        for k, v in ORG_PROFILES.items()
    ]