FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 ENVIRONMENT=production HOST=0.0.0.0
COPY requirements.txt .
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu && pip install -r requirements.txt
COPY backend ./backend
COPY frontend ./frontend
COPY run.py .
# put the fine-tuned model in ./model/bart_legal_final and mount it:  -v $(pwd)/model:/app/model
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
