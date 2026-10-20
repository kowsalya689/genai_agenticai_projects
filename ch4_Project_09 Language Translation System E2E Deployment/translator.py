"""Translation engine for the multilingual customer-support app.

Wraps the pretrained multilingual Transformer ``facebook/nllb-200-distilled-600M``
(No Language Left Behind) with:

* automatic source-language detection (``langdetect``),
* protection of non-translatable terms (error codes, URLs, emails, SKUs),
* beam-search decoding into the requested target language, and
* light post-processing.

The heavy model is loaded lazily on first use so the web server starts instantly.
"""

from __future__ import annotations

import re
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("translator")

# ---------------------------------------------------------------------------
# Supported languages: ISO-639-1 key -> display name + NLLB (FLORES-200) code.
# The ISO key is what `langdetect` returns; the NLLB code is what the model needs.
# Extend this dict to add more languages (any of NLLB's 200 are available).
# ---------------------------------------------------------------------------
LANGUAGES: Dict[str, Dict[str, str]] = {
    "en": {"name": "English",    "nllb": "eng_Latn"},
    "fr": {"name": "French",     "nllb": "fra_Latn"},
    "es": {"name": "Spanish",    "nllb": "spa_Latn"},
    "de": {"name": "German",     "nllb": "deu_Latn"},
    "hi": {"name": "Hindi",      "nllb": "hin_Deva"},
    "ta": {"name": "Tamil",      "nllb": "tam_Taml"},
    "te": {"name": "Telugu",     "nllb": "tel_Telu"},
    "ar": {"name": "Arabic",     "nllb": "arb_Arab"},
    "zh": {"name": "Chinese",    "nllb": "zho_Hans"},
    "pt": {"name": "Portuguese", "nllb": "por_Latn"},
}

MODEL_NAME = "facebook/nllb-200-distilled-600M"

GENERATION_PARAMS = {
    "num_beams": 5,
    "max_new_tokens": 512,
    "no_repeat_ngram_size": 3,
    "length_penalty": 1.0,
    "early_stopping": True,
}
MAX_INPUT_TOKENS = 512

# ---------------------------------------------------------------------------
# Term protection: things that must survive translation verbatim.
# ---------------------------------------------------------------------------
_PROTECT_PATTERNS = [
    re.compile(r"https?://\S+"),                                        # URLs
    re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),                        # emails
    re.compile(r"\b(?:ERR|ERROR|CODE|E|SKU|ID)[-_ ]?\d{2,}\b", re.I),  # error codes
    re.compile(r"\b[A-Z]{2,}[-_]?\d+[A-Z0-9-]*\b"),                    # SKU / product ids
    re.compile(r"#\w+|@\w+"),                                           # tags / handles
]
# Pure-ASCII sentinel; NLLB copies uppercase-Latin OOV tokens through verbatim.
_SENTINEL_PREFIX = "NLLBKEEP"


def _protect_terms(text: str) -> Tuple[str, Dict[str, str]]:
    """Replace non-translatable spans with ASCII sentinel placeholders.

    Scans the original text once, drops overlaps, then substitutes right-to-left so a
    sentinel can never be re-matched by a later pattern.
    """
    spans: List[Tuple[int, int, str]] = []
    for pattern in _PROTECT_PATTERNS:
        for m in pattern.finditer(text):
            if m.group(0).strip():
                spans.append((m.start(), m.end(), m.group(0)))

    spans.sort(key=lambda s: (s[0], -(s[1] - s[0])))
    kept: List[Tuple[int, int, str]] = []
    for st, en, val in spans:
        if any(not (en <= k0 or st >= k1) for k0, k1, _ in kept):
            continue
        kept.append((st, en, val))

    ordered = sorted(kept, key=lambda s: s[0])
    idx_of = {(st, en): i for i, (st, en, _) in enumerate(ordered)}

    mapping: Dict[str, str] = {}
    for st, en, val in sorted(kept, key=lambda s: s[0], reverse=True):
        placeholder = f"{_SENTINEL_PREFIX}{idx_of[(st, en)]}"
        text = text[:st] + placeholder + text[en:]
        mapping[placeholder] = val
    return text, mapping


def _restore_terms(text: str, mapping: Dict[str, str]) -> str:
    "Reverse :func:`_protect_terms`, tolerating case/spacing the model may add."
    for placeholder, original in sorted(mapping.items(), key=lambda kv: -len(kv[0])):
        digits = placeholder[len(_SENTINEL_PREFIX):]
        pat = re.compile(re.escape(_SENTINEL_PREFIX) + r"\s*" + digits + r"(?!\d)", re.I)
        text = pat.sub(lambda _m, o=original: o, text)
    return text


def _postprocess(text: str) -> str:
    "Collapse repeated whitespace and trim."
    return re.sub(r"\s+", " ", text).strip()


# ---------------------------------------------------------------------------
# Language detection.
# ---------------------------------------------------------------------------
@dataclass
class DetectionResult:
    iso: Optional[str]
    confidence: float
    supported: bool
    candidates: List[Tuple[str, float]] = field(default_factory=list)


def detect_language(text: str, default_iso: str = "en") -> DetectionResult:
    "Detect the source language of ``text``; never raises for bad input."
    from langdetect import detect_langs, DetectorFactory, LangDetectException

    DetectorFactory.seed = 42  # deterministic
    if not text or not text.strip():
        return DetectionResult(default_iso, 0.0, True)
    try:
        ranked = detect_langs(text)
    except LangDetectException:
        return DetectionResult(default_iso, 0.0, True)

    candidates = [(c.lang, float(c.prob)) for c in ranked]
    top_iso, top_prob = candidates[0]
    if top_iso not in LANGUAGES:
        return DetectionResult(default_iso, top_prob, False, candidates)
    return DetectionResult(top_iso, top_prob, True, candidates)


# ---------------------------------------------------------------------------
# Lazy-loaded model singleton.
# ---------------------------------------------------------------------------
class Translator:
    """Singleton wrapper around the NLLB tokenizer + model."""

    _instance: Optional["Translator"] = None

    def __init__(self) -> None:
        import torch
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info("Loading %s on %s (first run downloads ~2.5 GB)...", MODEL_NAME, self.device)
        dtype = torch.float16 if self.device == "cuda" else torch.float32
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME, torch_dtype=dtype)
        self.model.to(self.device)
        self.model.eval()
        self._torch = torch
        logger.info("Model ready.")

    @classmethod
    def get(cls) -> "Translator":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _nllb_code(self, iso: str) -> str:
        if iso not in LANGUAGES:
            raise KeyError(f"Unsupported language '{iso}'.")
        return LANGUAGES[iso]["nllb"]

    def _target_bos_id(self, tgt_iso: str) -> int:
        token = self._nllb_code(tgt_iso)
        tok_id = self.tokenizer.convert_tokens_to_ids(token)
        if tok_id is None or tok_id == self.tokenizer.unk_token_id:
            raise ValueError(f"Could not resolve NLLB token id for '{token}'.")
        return tok_id

    def translate(
        self,
        text: str,
        tgt_iso: str,
        src_iso: Optional[str] = None,
        protect: bool = True,
    ) -> Dict[str, object]:
        """Translate ``text`` into ``tgt_iso``; auto-detect the source if not given.

        Returns a JSON-serialisable dict with the translation and metadata.
        """
        t0 = time.perf_counter()
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Input text is empty.")
        if tgt_iso not in LANGUAGES:
            raise ValueError(f"Unsupported target language '{tgt_iso}'.")

        if src_iso in (None, "", "auto"):
            det = detect_language(text)
            src_iso = det.iso
            confidence = det.confidence
        else:
            confidence = 1.0
        if src_iso not in LANGUAGES:
            src_iso = "en"

        self.tokenizer.src_lang = self._nllb_code(src_iso)
        masked, mapping = _protect_terms(text) if protect else (text, {})

        enc = self.tokenizer(
            masked, return_tensors="pt", truncation=True, max_length=MAX_INPUT_TOKENS
        ).to(self.device)

        with self._torch.inference_mode():
            generated = self.model.generate(
                **enc,
                forced_bos_token_id=self._target_bos_id(tgt_iso),
                **GENERATION_PARAMS,
            )
        decoded = self.tokenizer.batch_decode(generated, skip_special_tokens=True)[0]
        if protect:
            decoded = _restore_terms(decoded, mapping)
        output = _postprocess(decoded)

        return {
            "translation": output,
            "source_text": text.strip(),
            "src_iso": src_iso,
            "src_name": LANGUAGES[src_iso]["name"],
            "tgt_iso": tgt_iso,
            "tgt_name": LANGUAGES[tgt_iso]["name"],
            "confidence": round(float(confidence), 3),
            "latency_ms": round((time.perf_counter() - t0) * 1000.0, 1),
        }
