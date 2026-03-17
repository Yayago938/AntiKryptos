"""
SENTINEL-X — Adversarial Intent Graph Cyber Defense System
XAI (Explainability) Layer

Public API surface:
    from xai.explainability_pipeline import explain, demo_analysis
"""

from xai.explainability_pipeline import explain, demo_analysis

__all__ = ["explain", "demo_analysis"]
__version__ = "1.0.0"