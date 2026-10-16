# MNIST Autoencoder — AI Image Reconstruction

A production-grade Flask web application that serves an existing, already-trained
MNIST Autoencoder for inference only. Upload any image, and the app preprocesses
it to a 28×28 grayscale tensor, runs it through your trained model, and displays
the original and reconstructed images side by side.

**This app never trains or fine-tunes a model.** Bring your own trained Keras
Autoencoder (`.keras` or `.h5`) and drop it into `models/`.

---

## 1. Features

- Drag-and-drop image upload with live preview (PNG, JPG, JPEG, WEBP, JFIF)
- Automatic preprocessing: grayscale conversion, 28×28 resize, `[0, 1]` normalization
- Model input shape auto-detection (`(28,28)`, `(28,28,1)`, or flattened `(784,)`)
- Single model load at startup — never reloaded per request
- Side-by-side original vs. reconstructed comparison, enlarged with crisp pixel
  rendering
- Download button for the reconstructed image
- `/api/health` endpoint reporting live model status
- Friendly, safe error messages; full errors logged server-side only
- Modern, responsive, glassmorphism-influenced dashboard UI (desktop → mobile)
- Modular architecture: config, services, routes, templates, static assets, tests

---

## 2. Folder structure

```
autoencoder_webapp/
│
├── app.py                     # Application factory / entry point
├── config.py                  # Centralized configuration
├── requirements.txt
├── README.md
├── .gitignore
│
├── models/                    # Place your trained model here
│   └── (your_model.keras or .h5)
│
├── services/
│   ├── __init__.py
│   ├── model_manager.py       # Loads the model once, runs predictions
│   └── image_processor.py     # Pre/post-processing (Pillow + NumPy)
│
├── routes/
│   ├── __init__.py
│   └── api.py                 # Flask routes: /, /api/health, /api/reconstruct
│
├── templates/
│   ├── base.html
│   └── index.html
│
├── static/
│   ├── css/style.css
│   ├── js/script.js
│   └── images/
│
└── tests/
    └── test_app.py
```

---

## 3. Prerequisites

- Python 3.10–3.12 (TensorFlow 2.16 requires this range)
- A trained MNIST Autoencoder saved as `.keras` or `.h5`

---

## 4. Setup

### 4.1 Create and activate a virtual environment

**Windows:**
```bat
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4.2 Install dependencies

```bash
pip install -r requirements.txt
```

### 4.3 Add your trained model

Copy your trained Autoencoder file into the `models/` folder:

```
autoencoder_webapp/models/autoencoder.keras
```

or

```
autoencoder_webapp/models/autoencoder.h5
```

The app auto-discovers the first supported model file in `models/`. To pin a
specific filename instead, set the `MODEL_FILENAME` environment variable:

**Windows:**
```bat
set MODEL_FILENAME=autoencoder.keras
```

**macOS / Linux:**
```bash
export MODEL_FILENAME=autoencoder.keras
```

### 4.4 Run the Flask server

```bash
python app.py
```

You should see log output confirming the model loaded, e.g.:

```
Model loaded successfully. input_shape=(None, 28, 28, 1) output_shape=(None, 28, 28, 1)
Autoencoder model ready for inference.
```

### 4.5 Open the application

Visit **http://127.0.0.1:5000** in your browser.

---

## 5. Supported image formats

- PNG
- JPG / JPEG
- WEBP
- JFIF

Maximum upload size: **8 MB** (configurable in `config.py` via `MAX_CONTENT_LENGTH`).

Any image you upload is automatically converted to grayscale and resized to
28×28 before being sent to the model — you don't need to pre-process anything
yourself.

---

## 6. Running tests

```bash
pip install pytest
pytest tests/
```

The test suite exercises routing, validation, and the preprocessing /
postprocessing pipeline. If no model is present in `models/`, the
model-dependent happy-path test is skipped gracefully (the API correctly
returns `503` instead of crashing).

---

## 7. API reference

### `GET /`
Renders the main application page.

### `GET /api/health`
```json
{
  "success": true,
  "status": "ok",
  "model_loaded": true,
  "model": {
    "filename": "autoencoder.keras",
    "input_shape": [null, 28, 28, 1],
    "output_shape": [null, 28, 28, 1]
  }
}
```

### `POST /api/reconstruct`
Multipart form field: `image` (file).

Success response:
```json
{
  "success": true,
  "original_image": "data:image/png;base64,...",
  "reconstructed_image": "data:image/png;base64,...",
  "dimensions": { "width": 28, "height": 28 }
}
```

Error response:
```json
{
  "success": false,
  "error": "Invalid image file."
}
```

---

## 8. Troubleshooting

**"No trained model file was found in the models/ directory."**
Make sure your `.keras` or `.h5` file is directly inside `autoencoder_webapp/models/`
(not a subfolder), and restart the server after adding it — the model is only
loaded once, at startup.

**"The loaded model's input shape ... does not look compatible with 28x28 grayscale ... images."**
Your model's input layer doesn't match an MNIST-style shape. The app accepts
`(28, 28)`, `(28, 28, 1)`, and flattened `(784,)` inputs. If your model uses a
different shape, adjust `DEFAULT_IMAGE_SIZE` in `config.py` and the shape
handling in `services/image_processor.py` accordingly.

**Model loads but predictions look wrong / noisy.**
Double-check that your model was trained on inputs normalized to `[0, 1]`
(this app normalizes with `pixel / 255.0`) and that its output activation
(e.g. sigmoid) also produces values in `[0, 1]`.

**Server starts but `/api/reconstruct` always returns 503.**
This means the model failed to load. Check the server console/log for the
full error (`Model load error: ...`) — the browser only ever sees a safe,
generic message.

**"This TensorFlow binary is optimized to use available CPU instructions..." / oneDNN messages.**
These are informational TensorFlow log lines, not errors — the app is working
normally.

**Port 5000 already in use.**
Stop whatever else is using port 5000, or run:
```bash
python app.py --port 5050
```
(or edit the `app.run(...)` call in `app.py` directly).

---

## 9. Production notes

- The bundled `app.run()` uses Flask's development server — fine for local
  use, but for production deployment use the included `gunicorn`:

  ```bash
  gunicorn -w 2 -b 0.0.0.0:8000 app:app
  ```

- Set `FLASK_ENV=production` to disable debug mode.
- Rotate `SECRET_KEY` via an environment variable in production.
