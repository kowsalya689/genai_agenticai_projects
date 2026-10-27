"""
Start the app.

Run this from the project folder:

    python run.py

Then open http://127.0.0.1:8000 in your browser.
"""
import uvicorn

from app.config import HOST, PORT

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=False)
