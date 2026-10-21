"""The model + end-to-end pipeline from the notebook (section 8):
raw text -> clean -> chunk -> summarise each chunk -> merge/dedupe -> (summarise again if long) -> tidy -> faithfulness check.

torch / transformers are imported lazily so the API (and the test-suite) can run without them installed.
"""
import logging
import re
import threading
import time
from pathlib import Path

from backend.config import Settings
from backend.services.chunking import chunk_document
from backend.services.faithfulness import faithfulness_report, report_to_warnings
from backend.services.text_utils import clean_text, split_sentences

log = logging.getLogger("lexbrief.model")

BASE_GEN = dict(num_beams=4, length_penalty=2.0, no_repeat_ngram_size=3, early_stopping=True, min_length=0)


class LegalSummarizer:
    def __init__(self, settings: Settings):
        self.s = settings
        self.tokenizer = None
        self.model = None
        self.device = None
        self.model_source = None
        self.load_error: str | None = None
        self._lock = threading.Lock()          # one model instance -> one generation at a time

    # ------------------------------------------------------------------ loading
    @property
    def is_loaded(self) -> bool:
        return self.model is not None and self.tokenizer is not None

    def load(self) -> None:
        import torch
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        local = Path(self.s.model_dir)
        source = str(local) if (local / "config.json").exists() else self.s.fallback_model
        if source == self.s.fallback_model:
            log.warning("Fine-tuned folder not found at %s - falling back to '%s' (downloads on first run).", local, source)
        device = self.s.device
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        log.info("Loading model from %s on %s ...", source, device)
        t0 = time.time()
        self.tokenizer = AutoTokenizer.from_pretrained(source)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(source).to(device).eval()
        self.device, self.model_source, self.load_error = device, source, None
        log.info("Model ready in %.1fs", time.time() - t0)

    def info(self) -> dict:
        d = {"loaded": self.is_loaded, "source": self.model_source, "device": self.device,
             "target_compression": self.s.target_compression, "final_cap_tokens": self.s.final_cap_tokens}
        if self.is_loaded:
            c = self.model.config
            d.update(parameters_millions=round(sum(p.numel() for p in self.model.parameters()) / 1e6, 1),
                     encoder_layers=c.encoder_layers, decoder_layers=c.decoder_layers,
                     attention_heads=c.encoder_attention_heads, d_model=c.d_model,
                     max_positions=c.max_position_embeddings)
        return d

    # ------------------------------------------------------------------ helpers
    def _n_tokens(self, text: str) -> int:
        return len(self.tokenizer(text, add_special_tokens=False)["input_ids"])

    @staticmethod
    def _length_budget(n_in: int, compression: float) -> tuple[int, int]:
        target = int(round(compression * n_in))
        max_new = int(min(max(target * 1.25, 24), 200))
        min_new = int(min(max(target * 0.5, 8), max_new - 8))
        return min_new, max_new

    def _generate(self, text: str, gen_kwargs: dict) -> str:
        import torch
        enc = self.tokenizer(text, max_length=self.s.max_source_tokens, truncation=True, return_tensors="pt").to(self.model.device)
        use_amp = self.model.device.type == "cuda"
        with torch.inference_mode(), torch.autocast(device_type=self.model.device.type, dtype=torch.float16, enabled=use_amp):
            out = self.model.generate(**enc, **gen_kwargs)
        return self.tokenizer.batch_decode(out, skip_special_tokens=True)[0].strip()

    @staticmethod
    def _finalize(text: str) -> str:
        """Drop near-duplicate sentences (from chunk overlap) and a dangling half-finished last sentence."""
        kept, kept_sets = [], []
        for s in split_sentences(text):
            toks = set(re.findall(r"\w+", s.lower()))
            if not toks:
                continue
            if any(len(toks & k) / max(1, len(toks | k)) >= 0.8 for k in kept_sets):
                continue
            kept.append(s)
            kept_sets.append(toks)
        out = " ".join(kept)
        if out and out[-1] not in ".!?\"')" and len(kept) > 1:
            out = " ".join(kept[:-1])
        return out.strip()

    def _trim_to_tokens(self, text: str, max_tokens: int) -> str:
        out: list[str] = []
        for s in split_sentences(text):
            if self._n_tokens(" ".join(out + [s])) > max_tokens:
                break
            out.append(s)
        return " ".join(out) if out else text

    # ------------------------------------------------------------------ public API
    def summarize(self, text: str, compression: float | None = None, max_summary_tokens: int | None = None,
                  num_beams: int | None = None) -> dict:
        if not self.is_loaded:
            raise RuntimeError("Model is not loaded")
        compression = compression or self.s.target_compression
        cap = max_summary_tokens or self.s.final_cap_tokens
        beams = num_beams or self.s.num_beams

        source = clean_text(text)
        if not source:
            raise ValueError("The document is empty after cleaning.")

        t0 = time.perf_counter()
        with self._lock:
            src_tok = self._n_tokens(source)
            level_text, trace, merged = source, [], ""
            for level in range(self.s.max_levels):
                chunks = chunk_document(level_text, self.tokenizer, self.s.chunk_tokens, 1 if level == 0 else 0)
                pieces = []
                for c in chunks:
                    mn, mx = self._length_budget(self._n_tokens(c), compression)
                    gen = dict(BASE_GEN, num_beams=beams, min_new_tokens=mn, max_new_tokens=mx)
                    pieces.append(self._generate(c, gen))
                merged = self._finalize(" ".join(pieces))
                trace.append({"level": level + 1, "chunks": len(chunks), "summary_tokens": self._n_tokens(merged)})
                if len(chunks) == 1 or self._n_tokens(merged) <= cap:
                    break
                level_text = merged                         # still too long: summarise the summaries
            if self._n_tokens(merged) > cap:
                merged = self._trim_to_tokens(merged, cap)
            s_tok = self._n_tokens(merged)

        report = faithfulness_report(source, merged)
        return {
            "summary": merged,
            "source_tokens": src_tok,
            "summary_tokens": s_tok,
            "source_words": len(source.split()),
            "summary_words": len(merged.split()),
            "compression_ratio": round(s_tok / max(1, src_tok), 4),
            "passes": trace,
            "warnings": report_to_warnings(report),
            "faithfulness": report,
            "model": self.model_source or "unknown",
            "elapsed_ms": int((time.perf_counter() - t0) * 1000),
        }
