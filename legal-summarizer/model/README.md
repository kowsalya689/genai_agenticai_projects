# Model folder

Put your fine-tuned model here so the final layout is:

```
model/bart_legal_final/
    config.json
    generation_config.json
    model.safetensors
    tokenizer.json  (plus vocab.json, merges.txt, tokenizer_config.json)
```

How to get it: run `notebooks/legal_summarization_bart.ipynb` on Colab. Section 14 saves and downloads
`bart_legal_final.zip`. Unzip it into this folder (the files must sit directly inside `bart_legal_final/`).

No fine-tuned folder yet? The app automatically falls back to the public `facebook/bart-large-cnn`
checkpoint (about 1.6 GB, downloaded once on first start, internet required).
