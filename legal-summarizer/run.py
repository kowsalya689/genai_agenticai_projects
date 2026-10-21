"""Start the web app:  python run.py   ->  http://127.0.0.1:8000  (API docs at /docs)"""
import uvicorn

from backend.config import get_settings

if __name__ == "__main__":
    s = get_settings()
    uvicorn.run("backend.main:app", host=s.host, port=s.port, reload=not s.is_production, reload_dirs=["backend"])
