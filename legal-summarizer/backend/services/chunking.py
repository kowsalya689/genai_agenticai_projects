"""Sentence-aware chunking with overlap so documents longer than BART's 1,024-token window can be summarised."""
from backend.services.text_utils import split_sentences


def chunk_document(text, tokenizer, max_tokens: int = 900, overlap_sentences: int = 1) -> list[str]:
    sents = split_sentences(text)
    if not sents:
        return [text]
    ids = tokenizer(sents, add_special_tokens=False)["input_ids"]

    # 1) split any single over-long sentence into token windows
    pieces: list[tuple[str, int]] = []
    for s, tok_ids in zip(sents, ids):
        if len(tok_ids) <= max_tokens:
            pieces.append((s, len(tok_ids)))
        else:
            for i in range(0, len(tok_ids), max_tokens):
                part = tok_ids[i:i + max_tokens]
                pieces.append((tokenizer.decode(part), len(part)))

    # 2) greedy packing with sentence overlap
    chunks, cur, cur_len = [], [], 0
    for s, n in pieces:
        if cur and cur_len + n > max_tokens:
            chunks.append(" ".join(p for p, _ in cur))
            carry = cur[-overlap_sentences:] if overlap_sentences > 0 else []
            if sum(m for _, m in carry) + n > max_tokens:
                carry = []
            cur = list(carry)
            cur_len = sum(m for _, m in cur)
        cur.append((s, n))
        cur_len += n
    if cur:
        chunks.append(" ".join(p for p, _ in cur))
    return chunks
