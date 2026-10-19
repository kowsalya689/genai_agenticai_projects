"""OPTIONAL: DistilGPT2 transformer comparison (beyond the brief).

The assessment (NX-NLP-2026-014, 4.3) requires a recurrent architecture —
that requirement is satisfied by the RNN/GRU/LSTM models in train_models.py.
This script adds a modern-transformer reference point for the explanation
video, showing where the field moved after RNNs:

  * No vanishing gradient problem at all: self-attention connects every
    position to every other position directly — no gradient path through T
    recurrent steps.
  * Subword (BPE) tokenisation: out-of-vocabulary words are impossible by
    construction (brief 4.5) — any string decomposes into known subwords.
  * Pretrained on a large corpus, so it generalises to unseen phrasing far
    better than a from-scratch 5k-vocab model.

Run in Colab (needs internet for the HuggingFace download):

    pip install transformers torch
    python notebooks/distilgpt2_compare.py --text "the stock market"

Disclosure: uses HuggingFace Transformers and the pretrained ``distilgpt2``
checkpoint (82M params, distilled from GPT-2 124M).
"""

import argparse


def predict_next_words(text: str, top_k: int = 5):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tok = AutoTokenizer.from_pretrained("distilgpt2")
    model = AutoModelForCausalLM.from_pretrained("distilgpt2")
    model.eval()

    ids = tok(text, return_tensors="pt").input_ids
    with torch.no_grad():
        logits = model(ids).logits[0, -1]
    probs = torch.softmax(logits, dim=-1)
    top = torch.topk(probs, top_k)

    print(f"\nSeed: {text!r}")
    print(f"{'token':<15} probability")
    for p, i in zip(top.values, top.indices):
        print(f"{tok.decode(int(i))!r:<15} {float(p):.4f}")
    return [(tok.decode(int(i)), float(p)) for p, i in zip(top.values, top.indices)]


def generate(text: str, num_words: int = 15, temperature: float = 0.8):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tok = AutoTokenizer.from_pretrained("distilgpt2")
    model = AutoModelForCausalLM.from_pretrained("distilgpt2")
    model.eval()

    ids = tok(text, return_tensors="pt").input_ids
    out = model.generate(
        ids,
        max_new_tokens=num_words,
        do_sample=temperature > 0,
        temperature=max(temperature, 1e-3),
        top_k=50,
        pad_token_id=tok.eos_token_id,
    )
    print("\nGenerated:", tok.decode(out[0], skip_special_tokens=True))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--text", default="the stock market")
    ap.add_argument("--top_k", type=int, default=5)
    ap.add_argument("--num_words", type=int, default=15)
    args = ap.parse_args()
    predict_next_words(args.text, args.top_k)
    generate(args.text, args.num_words)
