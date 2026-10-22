"""
utils/styles.py
---------------
Dark neon design system for the Medical Information Extractor dashboard.

Everything visual lives here: the color palette, the global stylesheet
(glowing borders, soft shadows, rounded cards, slide-in animations, a neon
loader) and small HTML helpers used by the card components.

Purely presentation — no data or backend logic.
"""

# ---------------------------------------------------------------------------
# Color theme (dark neon)
# ---------------------------------------------------------------------------
COLORS = {
    "background": "#0B0B0B",   # black
    "primary": "#00E5FF",      # neon blue
    "secondary": "#3B82F6",    # electric blue
    "accent": "#22D3EE",       # cyan
    "card": "#0F1621",         # dark card surface
    "card_alt": "#0C121B",
    "border": "rgba(0, 229, 255, 0.22)",
    "text": "#E6F7FF",
    "text_muted": "#8AA0B4",
    "danger": "#FF5A78",
    "success": "#22D3EE",
}


def inject_global_styles() -> str:
    """Return the full <style> block used across the app."""
    c = COLORS
    # Small f-string ONLY for the CSS custom properties, so the large
    # stylesheet below can use normal single braces (no escaping needed).
    root = (
        ":root {"
        f"--bg:{c['background']};"
        f"--primary:{c['primary']};"
        f"--secondary:{c['secondary']};"
        f"--accent:{c['accent']};"
        f"--card:{c['card']};"
        f"--card-alt:{c['card_alt']};"
        f"--border:{c['border']};"
        f"--text:{c['text']};"
        f"--muted:{c['text_muted']};"
        f"--danger:{c['danger']};"
        "}"
    )

    css = """
    /* ---- Base ----------------------------------------------------------- */
    .stApp {
        background:
            radial-gradient(1200px 600px at 15% -10%, rgba(0,229,255,0.08), transparent 60%),
            radial-gradient(1000px 500px at 100% 0%, rgba(59,130,246,0.08), transparent 55%),
            var(--bg);
        color: var(--text);
    }
    .block-container {
        padding-top: 1.4rem;
        padding-bottom: 3rem;
        max-width: 1320px;
    }
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI',
                     Roboto, Helvetica, Arial, sans-serif;
        color: var(--text);
    }
    /* hide default streamlit chrome for a cleaner product feel */
    #MainMenu, header[data-testid="stHeader"], footer { visibility: hidden; }

    /* ---- Hero ----------------------------------------------------------- */
    .hero {
        text-align: center;
        padding: 30px 20px 14px 20px;
        margin-bottom: 10px;
    }
    .hero .badge {
        display: inline-flex; align-items: center; gap: 8px;
        font-size: 12px; letter-spacing: 1.4px; text-transform: uppercase;
        color: var(--accent);
        border: 1px solid var(--border);
        background: rgba(0,229,255,0.05);
        padding: 6px 14px; border-radius: 999px; margin-bottom: 18px;
    }
    .hero h1 {
        font-size: 42px; font-weight: 800; margin: 0; letter-spacing: -0.5px;
        color: #ffffff;
        text-shadow: 0 0 18px rgba(0,229,255,0.55), 0 0 44px rgba(0,229,255,0.25);
    }
    .hero h1 .pin { -webkit-text-fill-color: initial; }
    .hero p {
        margin: 12px 0 0 0; font-size: 16px; color: var(--muted); font-weight: 400;
    }
    .hero .rule {
        width: 120px; height: 3px; margin: 20px auto 0 auto; border-radius: 3px;
        background: linear-gradient(90deg, transparent, var(--primary), transparent);
        box-shadow: 0 0 14px var(--primary);
    }

    /* ---- Cards ---------------------------------------------------------- */
    .neon-card {
        position: relative;
        background: linear-gradient(180deg, var(--card) 0%, var(--card-alt) 100%);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 22px 24px;
        margin-bottom: 20px;
        box-shadow: 0 0 0 1px rgba(0,229,255,0.04),
                    0 18px 40px rgba(0,0,0,0.45),
                    inset 0 1px 0 rgba(255,255,255,0.03);
        animation: cardIn 0.55s cubic-bezier(0.22, 1, 0.36, 1) both;
    }
    .neon-card::before {
        content: ""; position: absolute; inset: 0; border-radius: 18px;
        padding: 1px; pointer-events: none;
        background: linear-gradient(120deg, rgba(0,229,255,0.5), rgba(59,130,246,0.15), rgba(34,211,238,0.4));
        -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
        -webkit-mask-composite: xor; mask-composite: exclude; opacity: 0.6;
    }
    .card-title {
        display: flex; align-items: center; gap: 10px;
        font-size: 16px; font-weight: 700; color: #ffffff;
        margin: 0 0 16px 0; padding-bottom: 12px;
        border-bottom: 1px solid var(--border);
    }
    .card-title .dot {
        width: 9px; height: 9px; border-radius: 50%; display: inline-block;
        box-shadow: 0 0 10px currentColor;
    }

    @keyframes cardIn {
        from { opacity: 0; transform: translateX(26px) translateY(8px); filter: blur(2px); }
        to   { opacity: 1; transform: translateX(0) translateY(0); filter: blur(0); }
    }

    /* ---- Patient info grid --------------------------------------------- */
    .info-grid {
        display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 12px;
    }
    .info-item {
        background: rgba(255,255,255,0.02);
        border: 1px solid var(--border);
        border-radius: 12px; padding: 12px 14px;
    }
    .info-item .label {
        font-size: 10.5px; text-transform: uppercase; letter-spacing: 0.8px;
        color: var(--muted); font-weight: 600; margin-bottom: 5px;
    }
    .info-item .value { font-size: 15px; font-weight: 600; color: var(--text); word-break: break-word; }
    .info-item .value.empty { color: var(--muted); font-weight: 400; font-style: italic; }

    /* ---- Disease list --------------------------------------------------- */
    .disease-list { list-style: none; padding: 0; margin: 0; }
    .disease-list li {
        display: flex; align-items: center; gap: 12px;
        background: rgba(255,90,120,0.05);
        border: 1px solid rgba(255,90,120,0.25);
        border-left: 3px solid var(--danger);
        border-radius: 12px; padding: 12px 16px; margin-bottom: 10px;
        font-size: 15px; font-weight: 500; color: var(--text);
    }
    .disease-list li .pill-icon { font-size: 17px; }

    /* ---- Tables --------------------------------------------------------- */
    .data-table {
        width: 100%; border-collapse: separate; border-spacing: 0;
        border-radius: 12px; overflow: hidden; border: 1px solid var(--border);
    }
    .data-table thead th {
        background: linear-gradient(90deg, rgba(0,229,255,0.16), rgba(59,130,246,0.16));
        color: #ffffff; text-align: left; font-size: 12.5px; font-weight: 700;
        padding: 12px 16px; letter-spacing: 0.4px;
        border-bottom: 1px solid var(--border);
    }
    .data-table tbody td {
        padding: 12px 16px; font-size: 14px; color: var(--text);
        border-top: 1px solid rgba(255,255,255,0.05);
        background: rgba(255,255,255,0.01);
    }
    .data-table tbody tr:nth-child(even) td { background: rgba(0,229,255,0.03); }
    .data-table .muted { color: var(--muted); font-style: italic; }

    /* ---- Summary -------------------------------------------------------- */
    .summary-box {
        background: linear-gradient(120deg, rgba(0,229,255,0.08), rgba(59,130,246,0.06));
        border: 1px solid var(--border);
        border-left: 4px solid var(--primary);
        border-radius: 14px; padding: 18px 22px;
        font-size: 15px; line-height: 1.75; color: var(--text);
        box-shadow: inset 0 0 30px rgba(0,229,255,0.05);
    }
    .summary-box p { margin: 0 0 12px 0; }
    .summary-box p:last-child { margin-bottom: 0; }

    /* ---- Empty state (right pane before extraction) --------------------- */
    .empty-state {
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        text-align: center; min-height: 360px;
        border: 1.5px dashed var(--border); border-radius: 18px;
        background: rgba(255,255,255,0.015); color: var(--muted); padding: 30px;
    }
    .empty-state .glyph {
        font-size: 46px; margin-bottom: 14px;
        filter: drop-shadow(0 0 16px rgba(0,229,255,0.5));
    }
    .empty-state h3 { color: var(--text); margin: 0 0 6px 0; font-size: 17px; }

    /* ---- Neon loader ---------------------------------------------------- */
    .loader-wrap {
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        min-height: 360px; gap: 18px;
    }
    .neon-ring {
        width: 64px; height: 64px; border-radius: 50%;
        border: 4px solid rgba(0,229,255,0.15);
        border-top-color: var(--primary);
        box-shadow: 0 0 22px rgba(0,229,255,0.55);
        animation: spin 0.9s linear infinite;
    }
    .loader-wrap .txt { color: var(--accent); font-size: 14px; letter-spacing: 0.6px; }
    @keyframes spin { to { transform: rotate(360deg); } }

    /* ---- Input pane hint ------------------------------------------------ */
    .pane-title {
        font-size: 13px; text-transform: uppercase; letter-spacing: 1px;
        color: var(--accent); font-weight: 700; margin: 2px 0 12px 2px;
    }
    .hint { color: var(--muted); font-size: 12.5px; margin: 6px 0 2px 2px; }

    /* ---- Widgets: buttons, uploader, textarea --------------------------- */
    .stButton > button, .stDownloadButton > button {
        border-radius: 12px; font-weight: 700; letter-spacing: 0.3px;
        border: 1px solid var(--border);
        background: rgba(0,229,255,0.06); color: var(--text);
        transition: all 0.18s ease;
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        border-color: var(--primary);
        box-shadow: 0 0 18px rgba(0,229,255,0.35);
        transform: translateY(-1px);
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(90deg, var(--primary), var(--secondary));
        color: #041018; border: none;
        box-shadow: 0 0 22px rgba(0,229,255,0.45);
    }
    div[data-testid="stFileUploaderDropzone"] {
        border-radius: 14px; border: 1.5px dashed var(--primary);
        background: rgba(0,229,255,0.04);
    }
    .stTextArea textarea {
        background: rgba(255,255,255,0.02) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important; color: var(--text) !important;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 6px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px 10px 0 0; color: var(--muted);
    }
    .stTabs [aria-selected="true"], .stTabs [aria-selected="true"] p { color: var(--primary) !important; }

    /* ---- Force readable text on native widgets -------------------------- */
    /* Guarantees light text on the black background even when the dark
       config.toml theme is not picked up (e.g. app launched from another
       directory). Without this, Streamlit keeps light-theme (dark) text,
       which is invisible on the black canvas. */
    .stApp, .stApp p, .stApp li, .stApp label, .stApp span,
    .stMarkdown, .stMarkdown p, .stText,
    [data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] * ,
    [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * ,
    .stTabs [data-baseweb="tab"] p,
    [data-testid="stFileUploaderDropzoneInstructions"],
    [data-testid="stFileUploaderDropzoneInstructions"] * ,
    .stTextArea label, .stTextInput label,
    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] summary p {
        color: var(--text) !important;
    }
    [data-testid="stExpander"] summary svg { fill: var(--text) !important; }

    /* placeholder text a touch dimmer, still readable */
    .stTextArea textarea::placeholder { color: var(--muted) !important; }

    /* "Browse files" button inside the uploader */
    [data-testid="stFileUploader"] button,
    [data-testid="baseButton-secondary"] {
        color: var(--text) !important;
        border-color: var(--border) !important;
        background: rgba(0,229,255,0.06) !important;
    }

    /* Alerts (success / error / info): dark tinted surface + light text so
       they stay legible on black regardless of the active theme. */
    [data-testid="stAlert"], [data-testid="stAlertContainer"] {
        background: rgba(0,229,255,0.07) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
    }
    [data-testid="stAlert"] *, [data-testid="stAlertContainer"] * {
        color: var(--text) !important;
    }

    /* ---- Responsive ----------------------------------------------------- */
    @media (max-width: 900px) {
        .hero h1 { font-size: 32px; }
    }
    """
    return "<style>" + root + css + "</style>"


def card_open(title: str, icon: str, dot_color: str, delay: float = 0.0) -> str:
    """Opening HTML for a neon card. Pair with `card_close()`."""
    return (
        f'<div class="neon-card" style="animation-delay:{delay}s">'
        f'<div class="card-title">'
        f'<span class="dot" style="color:{dot_color}"></span>'
        f"<span>{icon} {title}</span>"
        f"</div>"
    )


def card_close() -> str:
    """Closing tag for a card opened with `card_open()`."""
    return "</div>"


def neon_loader(message: str = "Analyzing report…") -> str:
    """Return HTML for the neon loading animation."""
    return (
        '<div class="loader-wrap">'
        '<div class="neon-ring"></div>'
        f'<div class="txt">{message}</div>'
        "</div>"
    )


def empty_state() -> str:
    """Return HTML for the right-pane placeholder shown before extraction."""
    return (
        '<div class="empty-state">'
        '<div class="glyph">🧬</div>'
        "<h3>Results will appear here</h3>"
        "<div>Upload a medical PDF or paste report text, then click "
        "<b>Extract Information</b>.</div>"
        "</div>"
    )
