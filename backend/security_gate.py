"""
SENTINEL-X Security Gate
Fast deterministic pre-filter (~12ms) — runs before any ML model.
Checks: instruction override, jailbreak patterns, PII, hidden text.
"""

import re
import unicodedata
from hashlib import md5


# ---------------------------------------------------------------------------
# 1. KEYWORD TRIE for instruction override detection
# ---------------------------------------------------------------------------

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False
        self.phrase = None


class KeywordTrie:
    OVERRIDE_PHRASES = [
        "ignore previous instructions",
        "ignore all previous",
        "ignore your instructions",
        "forget your instructions",
        "forget previous instructions",
        "disregard your instructions",
        "disregard previous instructions",
        "override your instructions",
        "you are now",
        "new instructions",
        "your new role",
        "act as if",
        "pretend you are",
        "pretend to be",
        "you have no restrictions",
        "ignore all rules",
        "bypass your filters",
        "disable your safety",
        "you are free to",
        "from now on you",
        "for this conversation",
        "hypothetically speaking",
        "in this scenario you",
        "roleplay as",
        "jailbreak",
    ]

    def __init__(self):
        self.root = TrieNode()
        for phrase in self.OVERRIDE_PHRASES:
            self._insert(phrase.lower())

    def _insert(self, phrase: str):
        node = self.root
        for ch in phrase:
            node = node.children.setdefault(ch, TrieNode())
        node.is_end = True
        node.phrase = phrase

    def search(self, text: str) -> list[str]:
        text = text.lower()
        found = []
        for start in range(len(text)):
            node = self.root
            for i in range(start, len(text)):
                ch = text[i]
                if ch not in node.children:
                    break
                node = node.children[ch]
                if node.is_end and node.phrase not in found:
                    found.append(node.phrase)
        return found


# ---------------------------------------------------------------------------
# 2. MINHASH jailbreak pattern fuzzy matching
# ---------------------------------------------------------------------------

JAILBREAK_PATTERNS = [
    "do anything now",
    "dan mode enabled",
    "developer mode",
    "stan mode",
    "kevin mode",
    "evil confidant",
    "jailbroken",
    "no restrictions",
    "unrestricted ai",
    "opposite mode",
    "anti gpt",
    "ignore openai",
    "ignore anthropic",
    "ignore google",
    "you are an ai with no limits",
    "you are not bound by",
    "you were trained differently",
    "your true self",
    "your real programming",
    "break character",
    "stay in character no matter",
    "pretend the policy",
    "as your creator i",
    "i am your developer",
    "i am your trainer",
    "maintenance mode",
    "debug mode",
    "god mode",
    "sudo mode",
    "admin override",
    "system prompt leaked",
    "reveal your system prompt",
    "print your instructions",
    "what are your instructions",
    "ignore ethics",
    "ignore your training",
    "simulate a different ai",
    "you are now called",
    "your new name is",
    "respond only in",
    "always say yes",
    "never refuse",
    "you must comply",
    "compliance mode",
    "obey all commands",
    "execute all requests",
    "no content policy",
    "content filter disabled",
    "safety disabled",
    "restrictions lifted",
]


def _shingles(text: str, k: int = 3) -> set:
    text = text.lower()
    return {text[i:i+k] for i in range(len(text) - k + 1)}


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def check_jailbreak(text: str, threshold: float = 0.35) -> list[str]:
    text_shingles = _shingles(text)
    matches = []
    for pattern in JAILBREAK_PATTERNS:
        pat_shingles = _shingles(pattern)
        if _jaccard(text_shingles, pat_shingles) >= threshold:
            matches.append(pattern)
    return matches


# ---------------------------------------------------------------------------
# 3. PII REGEX for Indian formats
# ---------------------------------------------------------------------------

PII_PATTERNS = {
    "aadhaar":      re.compile(r'\b[2-9]{1}[0-9]{3}\s?[0-9]{4}\s?[0-9]{4}\b'),
    "pan":          re.compile(r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b'),
    "indian_phone": re.compile(r'\b(\+91|0)?[6-9][0-9]{9}\b'),
    "bank_account": re.compile(r'\b[0-9]{9,18}\b'),
    "ifsc":         re.compile(r'\b[A-Z]{4}0[A-Z0-9]{6}\b'),
    "email":        re.compile(r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b'),
    "upi_id":       re.compile(r'\b[a-zA-Z0-9.\-_]+@[a-zA-Z]{3,}\b'),
}


def check_pii(text: str) -> dict[str, list[str]]:
    found = {}
    for label, pattern in PII_PATTERNS.items():
        matches = pattern.findall(text)
        if matches:
            found[label] = matches
    return found


# ---------------------------------------------------------------------------
# 4. UNICODE hidden text scanner
# ---------------------------------------------------------------------------

ZERO_WIDTH_CHARS = {
    '\u200b': 'ZERO WIDTH SPACE',
    '\u200c': 'ZERO WIDTH NON-JOINER',
    '\u200d': 'ZERO WIDTH JOINER',
    '\u2060': 'WORD JOINER',
    '\ufeff': 'ZERO WIDTH NO-BREAK SPACE (BOM)',
    '\u00ad': 'SOFT HYPHEN',
    '\u034f': 'COMBINING GRAPHEME JOINER',
    '\u115f': 'HANGUL CHOSEONG FILLER',
}

# Common homoglyph substitutions (Cyrillic/Greek chars that look Latin)
HOMOGLYPHS = {
    'а': 'a', 'е': 'e', 'о': 'o', 'р': 'p', 'с': 'c',
    'х': 'x', 'у': 'y', 'і': 'i', 'ї': 'i', 'ѕ': 's',
    'ո': 'n', 'ս': 'u', 'ⅼ': 'l', 'ℓ': 'l',
}


def check_hidden_text(text: str) -> dict:
    result = {"zero_width_chars": [], "homoglyphs_found": [], "normalized_text": text}

    for char, name in ZERO_WIDTH_CHARS.items():
        if char in text:
            result["zero_width_chars"].append(name)

    homoglyphs_found = []
    normalized = []
    for ch in text:
        if ch in HOMOGLYPHS:
            homoglyphs_found.append(f"U+{ord(ch):04X} → '{HOMOGLYPHS[ch]}'")
            normalized.append(HOMOGLYPHS[ch])
        else:
            normalized.append(ch)

    result["homoglyphs_found"] = homoglyphs_found
    result["normalized_text"] = "".join(normalized)
    return result


# ---------------------------------------------------------------------------
# 5. MAIN GATE RUNNER
# ---------------------------------------------------------------------------

def run_gate(text: str) -> dict:
    """
    Run all four gate checks. Returns:
    {
        "block": bool,          # True = block immediately, don't call model
        "escalate": bool,       # True = send to ML model for deep analysis
        "flags": list[str],     # Which checks fired
        "details": dict,        # Raw findings per check
        "clean_text": str,      # Normalized text for downstream use
    }
    """
    flags = []
    details = {}
    block = False

    # Check 1: instruction override (trie)
    trie = KeywordTrie()
    override_matches = trie.search(text)
    if override_matches:
        flags.append("instruction_override")
        details["instruction_override"] = override_matches
        block = True  # Hard block on override detection

    # Check 2: jailbreak fuzzy match
    jailbreak_matches = check_jailbreak(text)
    if jailbreak_matches:
        flags.append("jailbreak_pattern")
        details["jailbreak_pattern"] = jailbreak_matches

    # Check 3: PII markers
    pii_found = check_pii(text)
    if pii_found:
        flags.append("pii_detected")
        details["pii_detected"] = pii_found

    # Check 4: hidden text / homoglyphs
    hidden = check_hidden_text(text)
    if hidden["zero_width_chars"] or hidden["homoglyphs_found"]:
        flags.append("hidden_text")
        details["hidden_text"] = {
            "zero_width_chars": hidden["zero_width_chars"],
            "homoglyphs": hidden["homoglyphs_found"],
        }

    clean_text = hidden["normalized_text"]
    # Strip zero-width characters from clean text
    for char in ZERO_WIDTH_CHARS:
        clean_text = clean_text.replace(char, "")

    escalate = bool(flags) and not block

    return {
        "block": block,
        "escalate": escalate,
        "flags": flags,
        "details": details,
        "clean_text": clean_text,
    }
