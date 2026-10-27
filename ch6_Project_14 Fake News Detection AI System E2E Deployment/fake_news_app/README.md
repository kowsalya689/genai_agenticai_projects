# Fake News Detection System

A simple, modular web app that classifies a news headline or article as
**REAL** or **FAKE** using a fine-tuned **DistilBERT** model. Built with FastAPI.

It loads the model you trained in the Colab notebook and serves it through:

- a small web page (paste text, get a result), and
- a REST API (`POST /predict`).

## Project structure

```
fake_news_app/
├── app/
│   ├── __init__.py
│   ├── config.py          # settings (model path, max length, host, port)
│   ├── preprocessing.py    # clean_text() - same cleaning as training
│   ├── detector.py        # loads the model once, makes predictions
│   ├── schemas.py         # request/response shapes
│   └── main.py            # FastAPI app + routes
├── static/
│   └── index.html         # the web page
├── fake_news_model/       # <-- put your trained model here (not in git)
├── requirements.txt
├── run.py                 # start the server: python run.py
└── README.md
```

## Quick start

1. Put your trained model in place. Unzip `fake_news_model.zip` inside this
   folder so that `fake_news_model/` sits next to `run.py`.
2. Create a virtual environment and install dependencies:
   ```
   python -m venv .venv
   # Windows:  .venv\Scripts\activate
   # Mac/Linux: source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Start the app:
   ```
   python run.py
   ```
4. Open http://127.0.0.1:8000 in your browser.

See **Execution_Guide.docx** for a step-by-step version with pictures of the
commands and common fixes.

## API

`POST /predict`

Request:
```json
{ "text": "The central bank raised interest rates after its policy meeting." }
```

Response:
```json
{
  "label": "REAL",
  "confidence": 0.885,
  "probabilities": { "FAKE": 0.115, "REAL": 0.885 }
}
```

Interactive API docs are available at http://127.0.0.1:8000/docs

## Notes

- The app cleans text exactly like the training notebook (including removing the
  "(Reuters)" dateline), so predictions match what you saw in Colab.
- The model runs on CPU by default and uses a GPU automatically if one is present.
- The model files are large (~250 MB) and are excluded from git via `.gitignore`.
