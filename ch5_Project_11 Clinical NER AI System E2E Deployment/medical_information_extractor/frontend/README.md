# Medical Information Extractor — Frontend (Dark Neon Dashboard)

A premium, portfolio-ready **Streamlit** dashboard for the *Medical Information
Extractor using NLP* project. Dark neon healthcare theme, no sidebar, a two-pane
landing page (input on the left, results slide in on the right), and two ways to
provide a report: **upload a PDF** or **paste text**.

> Frontend only. The FastAPI backend (PDF reader, NLP pipeline, entity
> extraction, summary/JSON/table builders) is **unchanged**.

---

## What's new in this version

- 🎨 Dark neon theme (black `#0B0B0B`, neon blue `#00E5FF`, electric blue
  `#3B82F6`, cyan `#22D3EE`) with glowing borders, soft shadows and rounded cards
- 🧭 Sidebar removed — full-width, two-pane layout
- 📄 **Upload PDF** *or* 📝 **Paste medical text** (both feed the same endpoint)
- ⏳ Neon loading animation while extracting
- ✨ Results slide in on the right with a smooth card animation
- 🧾 Five result cards: Patient, Disease, Medications, Laboratory, Summary
- ⬇️ Download **JSON**, download **CSV**, **Clear Results**

### How "Paste Text" works without touching the backend
The backend only exposes `POST /extract`, which accepts a **PDF upload**. When
you paste text, the frontend renders it into an in-memory PDF (via `fpdf2`) and
sends that to the same endpoint. Same API, same response, zero backend changes.

---

## Project structure

```
frontend/
├── app.py                      # two-pane orchestrator (no sidebar)
├── .streamlit/config.toml      # native dark theme for widgets
├── components/
│   ├── header.py               # hero / landing header
│   ├── input_section.py        # Upload PDF / Paste Text tabs + Extract button
│   ├── patient_card.py
│   ├── disease_card.py
│   ├── medication_table.py
│   ├── lab_table.py
│   ├── summary_card.py
│   └── download_section.py     # JSON / CSV / Clear
├── utils/
│   ├── api.py                  # the only place that talks to the backend
│   ├── text_pdf.py             # pasted text -> in-memory PDF
│   └── styles.py               # neon theme + animations
├── requirements.txt
└── README.md
```

---

## Setup & run

```bash
cd frontend
python -m venv venv
# Windows: venv\Scripts\activate   |   macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
```

Start the backend (separate terminal):

```bash
cd backend
uvicorn app:app --reload          # http://localhost:8000
```

Start the frontend:

```bash
cd frontend
streamlit run app.py              # http://localhost:8501
```

If the backend runs elsewhere, set the URL before launching:
`FASTAPI_URL=http://127.0.0.1:8000 streamlit run app.py`.

---

## Backend endpoints used (unchanged)

| Endpoint        | Use                                 |
|-----------------|-------------------------------------|
| `POST /extract` | Multipart PDF upload → returns JSON |

Response shape consumed exactly as produced by the backend:
`summary`, `entities.{patient_information, clinical_information,
laboratory_information, medications}`, and
`tables.{patient_table, disease_table, medication_table, lab_table}`.

> **CORS:** not needed — Streamlit calls FastAPI server-side with Python
> `requests`, so there is no browser cross-origin request.
