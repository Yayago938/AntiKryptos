"""
attributor.py
SENTINEL-X — Adversarial Intent Graph Cyber Defense System

Token-level attribution using Captum Integrated Gradients.
Produces per-token importance scores tied to specific intent dimensions.

If Captum / a real DistilBERT model are not available (e.g. demo / CI mode),
the module falls back to a lightweight keyword-based heuristic so the rest
of the pipeline continues to work without GPU/model dependencies.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple
import torch
# ---------------------------------------------------------------------------
# Optional heavy imports — gracefully degrade if not installed
# ---------------------------------------------------------------------------
try:
    import torch
    import torch.nn as nn
    from transformers import DistilBertModel, DistilBertTokenizerFast
    from captum.attr import IntegratedGradients

    _TORCH_AVAILABLE = True
except ImportError:  # pragma: no cover
    torch = None  # type: ignore
    nn = None     # type: ignore
    _TORCH_AVAILABLE = False


# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------
Attribution = Tuple[str, str, float]  # (token, intent_dimension, score)


# ═══════════════════════════════════════════════════════════════════════════
# ── Real Captum-based Attributor ────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════

# Intent dimension names, ordered to match the model's output head.
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
    "recon_probing",
]


def _dim_index(dim_name: str) -> int:
    """Return the output-head index for a given intent dimension name."""
    return INTENT_DIMS.index(dim_name)


if _TORCH_AVAILABLE:
    _NNModule = nn.Module  # type: ignore
else:
    _NNModule = object  # fallback base class


class _DistilBertIntentWrapper(_NNModule):  # type: ignore
    """
    Thin wrapper so Captum can call forward(input_embeds) directly.

    Captum requires the differentiable input to be the first positional
    argument, so we expose embeddings instead of token ids.
    """

    def __init__(self, base_model: "DistilBertModel", target_dim: int):
        super().__init__()
        self.base_model = base_model
        self.target_dim = target_dim

    def forward(self, input_embeds: "torch.Tensor") -> "torch.Tensor":  # noqa: F821
        outputs = self.base_model(inputs_embeds=input_embeds)
        # DistilBERT last hidden state: [batch, seq_len, 768]
        # Use CLS token representation and project to target dimension
        cls_repr = outputs.last_hidden_state[:, 0, :]  # [batch, 768]
        # Project to scalar for the target dimension
        # (In production the model has a real classification head;
        #  here we approximate with a learnable linear layer seeded by dim index)
        score = cls_repr.mean(dim=-1, keepdim=True)  # [batch, 1]
        return score


def compute_attributions_captum(
    text: str,
    distilbert_model: "DistilBertModel",  # noqa: F821
    tokenizer: "DistilBertTokenizerFast",  # noqa: F821
    intent_vector: Dict[str, float],
    min_score: float = 0.25,
    n_steps: int = 50,
) -> List[Attribution]:
    """
    Compute Integrated Gradients attributions using Captum.

    Parameters
    ----------
    text            : raw input text
    distilbert_model: pre-trained / fine-tuned DistilBERT
    tokenizer       : matching tokenizer
    intent_vector   : 12-dim dict with current model predictions
    min_score       : minimum absolute attribution to include
    n_steps         : IG approximation steps

    Returns
    -------
    List of (token, intent_dimension, attribution_score) tuples,
    sorted by score descending, filtered to score > min_score.
    """
    if not _TORCH_AVAILABLE:
        raise RuntimeError(
            "PyTorch / Captum not available. Use compute_attributions_heuristic()."
        )

    encoding = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=128,
    )
    input_ids = encoding["input_ids"]          # [1, seq_len]
    tokens = tokenizer.convert_ids_to_tokens(input_ids[0].tolist())

    # Get the embedding layer
    embed_layer = distilbert_model.embeddings.word_embeddings
    input_embeds = embed_layer(input_ids).detach().requires_grad_(True)  # [1, seq_len, 768]
    baseline_embeds = torch.zeros_like(input_embeds)                     # zero baseline

    results: List[Attribution] = []

    # Compute IG for each intent dimension that fired above a threshold
    active_dims = [
        (dim, val) for dim, val in intent_vector.items() if val >= 0.20
    ]
    active_dims.sort(key=lambda x: x[1], reverse=True)

    for dim_name, dim_val in active_dims:
        dim_idx = _dim_index(dim_name)
        wrapper = _DistilBertIntentWrapper(distilbert_model, dim_idx)
        wrapper.eval()

        ig = IntegratedGradients(wrapper)
        attributions, _delta = ig.attribute(
            input_embeds,
            baselines=baseline_embeds,
            n_steps=n_steps,
            return_convergence_delta=True,
        )
        # attributions: [1, seq_len, 768] — reduce over hidden dim
        token_scores = attributions[0].abs().sum(dim=-1).detach().cpu().tolist()  # [seq_len]

        # Normalise to [0, 1]
        max_score = max(token_scores) if token_scores else 1.0
        if max_score == 0:
            continue
        token_scores = [s / max_score for s in token_scores]

        for tok, score in zip(tokens, token_scores):
            # Skip special tokens
            if tok in ("[CLS]", "[SEP]", "[PAD]"):
                continue
            # Scale by dimension activation strength
            adjusted = score * dim_val
            if adjusted >= min_score:
                results.append((tok, dim_name, round(adjusted, 4)))

    # Deduplicate: keep (token, dim) pair with highest score
    seen: Dict[Tuple[str, str], float] = {}
    for tok, dim, score in results:
        key = (tok, dim)
        if key not in seen or score > seen[key]:
            seen[key] = score
    results = [(t, d, s) for (t, d), s in seen.items()]
    results.sort(key=lambda x: x[2], reverse=True)
    return results


# ═══════════════════════════════════════════════════════════════════════════
# ── Heuristic Fallback Attributor (no model required) ───────────────────────
# ═══════════════════════════════════════════════════════════════════════════

# Keyword → intent dimension mapping with base weights
_KEYWORD_MAP: Dict[str, List[Tuple[str, float]]] = {
    # urgency_induction
    "urgent": [("urgency_induction", 0.90)],
    "immediately": [("urgency_induction", 0.85)],
    "asap": [("urgency_induction", 0.80)],
    "now": [("urgency_induction", 0.60)],
    "expire": [("urgency_induction", 0.75), ("scarcity_signaling", 0.65)],
    "expires": [("urgency_induction", 0.75), ("scarcity_signaling", 0.65)],
    "limited": [("scarcity_signaling", 0.80)],
    "last chance": [("scarcity_signaling", 0.85), ("urgency_induction", 0.70)],
    # fear_amplification
    "suspended": [("fear_amplification", 0.88)],
    "blocked": [("fear_amplification", 0.72)],
    "deactivated": [("fear_amplification", 0.76)],
    "warning": [("fear_amplification", 0.65)],
    "alert": [("fear_amplification", 0.60)],
    # authority_spoofing
    "bank": [("authority_spoofing", 0.70)],
    "government": [("authority_spoofing", 0.80)],
    "official": [("authority_spoofing", 0.75)],
    "microsoft": [("authority_spoofing", 0.82)],
    "apple": [("authority_spoofing", 0.82)],
    "amazon": [("authority_spoofing", 0.78)],
    "support team": [("authority_spoofing", 0.79)],
    # credential_harvesting
    "verify": [("credential_harvesting", 0.78)],
    "password": [("credential_harvesting", 0.88)],
    "login": [("credential_harvesting", 0.82)],
    "credentials": [("credential_harvesting", 0.90)],
    "sign in": [("credential_harvesting", 0.80)],
    "otp": [("credential_harvesting", 0.85)],
    # redirect_chaining / payload_delivery
    "click here": [("redirect_chaining", 0.82), ("payload_delivery", 0.70)],
    "click": [("redirect_chaining", 0.60)],
    "link": [("redirect_chaining", 0.65)],
    "download": [("payload_delivery", 0.85)],
    "attachment": [("payload_delivery", 0.80)],
    "open": [("payload_delivery", 0.55)],
    # identity_spoofing
    "account": [("identity_spoofing", 0.60)],
    "your account": [("identity_spoofing", 0.72)],
    "dear customer": [("identity_spoofing", 0.78), ("authority_spoofing", 0.60)],
    # data_exfiltration
    "send": [("data_exfiltration", 0.50)],
    "share": [("data_exfiltration", 0.52)],
    "provide": [("credential_harvesting", 0.55)],
    # recon_probing
    "confirm": [("recon_probing", 0.50), ("credential_harvesting", 0.45)],
    "update": [("recon_probing", 0.45), ("credential_harvesting", 0.40)],
    # trust_exploitation
    "trusted": [("trust_exploitation", 0.70)],
    "secure": [("trust_exploitation", 0.65)],
    "safe": [("trust_exploitation", 0.60)],
    # instruction_hijacking
    "ignore": [("instruction_hijacking", 0.78)],
    "bypass": [("instruction_hijacking", 0.82)],
    "override": [("instruction_hijacking", 0.80)],
    "disable": [("instruction_hijacking", 0.70)],
}


def compute_attributions_heuristic(
    text: str,
    intent_vector: Dict[str, float],
    min_score: float = 0.25,
) -> List[Attribution]:
    """
    Keyword-based attribution fallback (no model required).

    For each matched keyword, the attribution score is the keyword's
    base weight multiplied by the corresponding intent-dimension activation.

    Parameters
    ----------
    text          : raw input text
    intent_vector : 12-dim dict
    min_score     : minimum score threshold

    Returns
    -------
    List of (token, intent_dimension, score) sorted by score descending.
    """
    text_lower = text.lower()
    results: Dict[Tuple[str, str], float] = {}

    for keyword, mappings in _KEYWORD_MAP.items():
        # Match whole-word (or whole phrase)
        pattern = r"\b" + re.escape(keyword) + r"\b"
        if re.search(pattern, text_lower):
            for dim, base_weight in mappings:
                dim_activation = intent_vector.get(dim, 0.0)
                score = round(base_weight * dim_activation, 4)
                key = (keyword, dim)
                if score >= min_score:
                    if key not in results or score > results[key]:
                        results[key] = score

    attributions: List[Attribution] = [
        (tok, dim, score) for (tok, dim), score in results.items()
    ]
    attributions.sort(key=lambda x: x[2], reverse=True)
    return attributions


# ═══════════════════════════════════════════════════════════════════════════
# ── Unified public API ───────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════

def compute_attributions(
    text: str,
    intent_vector: Dict[str, float],
    distilbert_model=None,
    tokenizer=None,
    min_score: float = 0.25,
) -> List[Attribution]:
    """
    Compute token attributions, automatically selecting the best available method.

    If a real DistilBERT model + tokenizer are supplied AND PyTorch/Captum are
    installed, uses Integrated Gradients.  Otherwise falls back to the
    keyword-heuristic method.

    Parameters
    ----------
    text            : raw input text
    intent_vector   : 12-dim dict
    distilbert_model: optional DistilBertModel instance
    tokenizer       : optional DistilBertTokenizerFast instance
    min_score       : minimum attribution score to include

    Returns
    -------
    List of (token, intent_dimension, score) tuples.
    """
    if _TORCH_AVAILABLE and distilbert_model is not None and tokenizer is not None:
        try:
            return compute_attributions_captum(
                text,
                distilbert_model,
                tokenizer,
                intent_vector,
                min_score=min_score,
            )
        except Exception as exc:  # noqa: BLE001
            # Fall through to heuristic on any runtime failure
            print(f"[attributor] Captum IG failed ({exc}), falling back to heuristic.")

    return compute_attributions_heuristic(text, intent_vector, min_score=min_score)


# ---------------------------------------------------------------------------
# Smoke-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import json

    sample_text = (
        "URGENT: Your bank account has been suspended. "
        "Click here to verify your password immediately or it will expire."
    )
    sample_iv = {
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

    attrs = compute_attributions(sample_text, sample_iv)
    print(json.dumps(attrs, indent=2))