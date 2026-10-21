from backend.services.chunking import chunk_document
from backend.services.text_utils import clean_text, split_sentences


class WordTokenizer:
    """Tiny stand-in tokenizer: one token per whitespace-separated word."""
    def __call__(self, texts, add_special_tokens=False):
        return {"input_ids": [[hash(w) for w in t.split()] for t in texts]}

    def decode(self, ids):
        return " ".join(f"w{i}" for i in ids)


def test_clean_text_normalises_quotes_and_whitespace():
    assert clean_text("``Term''\r\n  means   two\tyears. ") == '"Term" means two years.'


def test_sentence_split_protects_abbreviations_and_list_numbers():
    t = 'Under Sec. 4 of the Act, Acme Pvt. Ltd. shall pay Rs. 5,000 (see 42 U.S.C. 1396). The fee is 1.5% per month. "Term" means two years. 2. Payment is due.'
    s = split_sentences(t)
    assert len(s) == 4
    assert s[0].startswith("Under Sec. 4") and s[0].endswith("1396).")


def test_chunking_respects_limit_and_overlaps():
    text = " ".join(f"Sentence number {i} has exactly eight words here." for i in range(40))
    chunks = chunk_document(text, WordTokenizer(), max_tokens=50, overlap_sentences=1)
    assert len(chunks) > 1
    assert all(len(c.split()) <= 50 for c in chunks)
    # overlap: the last sentence of chunk 1 reappears at the start of chunk 2
    last = split = chunks[0].split(". ")[-1].strip(". ")
    assert last in chunks[1]


def test_oversized_sentence_is_hard_split():
    chunks = chunk_document("word " * 130, WordTokenizer(), max_tokens=50, overlap_sentences=0)
    assert len(chunks) == 3
