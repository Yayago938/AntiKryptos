"""
dlp_scanner.py
SENTINEL-X — Adversarial Intent Graph Cyber Defense System

Data Loss Prevention (DLP) scanner.
Detects Indian PII patterns in message text using compiled regex rules.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ═══════════════════════════════════════════════════════════════════════════
# PII Pattern Definitions
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class _PiiPattern:
    """Represents a single PII detection rule."""
    name: str                       # Human-readable label (used as key in output)
    pattern: re.Pattern             # Compiled regex
    description: str                # Plain-English description


# ---------------------------------------------------------------------------
# Pattern library — ordered from most specific to least specific
# ---------------------------------------------------------------------------
_PII_PATTERNS: List[_PiiPattern] = [
    # ── Aadhaar ──────────────────────────────────────────────────────────────
    # 12-digit number, optionally space- or hyphen-separated in groups of 4
    _PiiPattern(
        name="aadhaar",
        pattern=re.compile(
            r"\b(\d{4}[\s\-]?\d{4}[\s\-]?\d{4})\b"
        ),
        description="Indian Aadhaar identity number (12 digits, optionally hyphen/space separated)",
    ),

    # ── PAN ──────────────────────────────────────────────────────────────────
    # Format: ABCDE1234F  (5 alpha + 4 digit + 1 alpha, uppercase)
    _PiiPattern(
        name="pan",
        pattern=re.compile(
            r"\b([A-Z]{5}[0-9]{4}[A-Z])\b"
        ),
        description="Indian Permanent Account Number (PAN) — income-tax identifier",
    ),

    # ── Indian phone number ──────────────────────────────────────────────────
    # 10-digit mobile, optionally prefixed by +91 / 0 / 91
    _PiiPattern(
        name="phone",
        pattern=re.compile(
            r"(?<!\d)(\+91[\s\-]?|91[\s\-]?|0)?([6-9]\d{9})(?!\d)"
        ),
        description="Indian mobile phone number (10 digits, starting 6–9)",
    ),

    # ── Email ────────────────────────────────────────────────────────────────
    _PiiPattern(
        name="email",
        pattern=re.compile(
            r"\b([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})\b"
        ),
        description="Email address",
    ),

    # ── Bank account number ───────────────────────────────────────────────────
    # Indian bank account numbers are typically 9–18 digits
    # Use context words to reduce false positives
    _PiiPattern(
        name="bank_account",
        pattern=re.compile(
            r"(?i)(?:account|acc|a\/c|bank)[\s:\.#]*(\d{9,18})"
        ),
        description="Indian bank account number (9–18 digits, with account context keyword)",
    ),

    # ── IFSC code ────────────────────────────────────────────────────────────
    # Format: ABCD0123456  (4 alpha + 0 + 6 alphanumeric)
    _PiiPattern(
        name="ifsc",
        pattern=re.compile(
            r"\b([A-Z]{4}0[A-Z0-9]{6})\b"
        ),
        description="Indian Financial System Code (IFSC) for bank branch identification",
    ),

    # ── Passport ─────────────────────────────────────────────────────────────
    # Indian passport: 1 letter + 7 digits
    _PiiPattern(
        name="passport",
        pattern=re.compile(
            r"\b([A-Z][0-9]{7})\b"
        ),
        description="Indian passport number (1 letter + 7 digits)",
    ),

    # ── Driving licence (common DL format) ───────────────────────────────────
    # State code (2 alpha) + RTO code (2 digit) + year (4 digit) + seq (7 digit)
    _PiiPattern(
        name="driving_licence",
        pattern=re.compile(
            r"\b([A-Z]{2}[\s\-]?\d{2}[\s\-]?\d{4}[\s\-]?\d{7})\b"
        ),
        description="Indian driving licence number",
    ),

    # ── UPI ID ───────────────────────────────────────────────────────────────
    _PiiPattern(
        name="upi_id",
        pattern=re.compile(
            r"\b([a-zA-Z0-9._\-]+@[a-zA-Z]{3,})\b"
        ),
        description="UPI payment address (VPA — Virtual Payment Address)",
    ),

    # ── Credit / debit card number ────────────────────────────────────────────
    # 16-digit (or 4×4) Visa/Mastercard/RuPay pattern
    _PiiPattern(
        name="card_number",
        pattern=re.compile(
            r"\b(\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4})\b"
        ),
        description="Payment card number (16-digit Visa/Mastercard/RuPay)",
    ),
]


# ═══════════════════════════════════════════════════════════════════════════
# Scanner
# ═══════════════════════════════════════════════════════════════════════════

def scan(text: str) -> Dict:
    """
    Scan text for Indian PII data.

    Parameters
    ----------
    text : str
        Raw message content to scan.

    Returns
    -------
    dict:
        {
            "pii_detected": bool,
            "types": [str, ...],         # unique PII type names found
            "matches": [str, ...],       # raw matched strings (normalised)
            "details": [
                {
                    "type": str,
                    "match": str,
                    "description": str
                },
                ...
            ]
        }
    """
    types_found: List[str] = []
    matches_found: List[str] = []
    details: List[Dict] = []

    for pii in _PII_PATTERNS:
        for m in pii.pattern.finditer(text):
            # Use group(1) if present (capture group), else full match
            raw = m.group(1) if m.lastindex and m.lastindex >= 1 else m.group(0)
            raw = raw.strip()

            # Normalise: strip separators for display
            normalised = re.sub(r"[\s\-]", "", raw)

            if pii.name not in types_found:
                types_found.append(pii.name)
            if normalised not in matches_found:
                matches_found.append(normalised)

            details.append(
                {
                    "type": pii.name,
                    "match": normalised,
                    "description": pii.description,
                    "position": {"start": m.start(), "end": m.end()},
                }
            )

    return {
        "pii_detected": bool(types_found),
        "types": types_found,
        "matches": matches_found,
        "details": details,
        "pii_count": len(matches_found),
    }


def redact(text: str, replacement: str = "[REDACTED]") -> str:
    """
    Return a copy of *text* with all detected PII replaced by *replacement*.

    Useful for safe logging.
    """
    redacted = text
    for pii in _PII_PATTERNS:
        redacted = pii.pattern.sub(replacement, redacted)
    return redacted


# ---------------------------------------------------------------------------
# Smoke-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import json

    sample = (
        "Dear customer, your Aadhaar 1234-5678-9012 and PAN ABCDE1234F are "
        "required. Call us at +91 9876543210 or email support@evil-bank.com. "
        "Transfer ₹50,000 to account 123456789012 (IFSC: SBIN0001234). "
        "Your card 4111-1111-1111-1111 has been flagged."
    )

    result = scan(sample)
    print(json.dumps(result, indent=2))

    print("\nRedacted version:")
    print(redact(sample))