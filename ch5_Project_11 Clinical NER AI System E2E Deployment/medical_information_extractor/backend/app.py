from fastapi import FastAPI, UploadFile, File
import shutil
import os

from pdf_reader import extract_text
from entity_extractor import extract_information
from json_builder import build_json
from summary_generator import generate_summary
from table_builder import build_tables

app = FastAPI(
    title="Medical Information Extractor",
    version="1.0"
)

UPLOAD_FOLDER = "uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.get("/")
def home():

    return {
        "message": "Medical Information Extractor API is Running"
    }


@app.post("/extract")

async def extract(file: UploadFile = File(...)):

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)

    with open(filepath, "wb") as buffer:

        shutil.copyfileobj(file.file, buffer)

    text = extract_text(filepath)

    entities = extract_information(text)

    json_result = build_json(entities)
    tables = build_tables(json_result)

    summary = generate_summary(json_result)

    return {

    "summary": summary,

    "entities": json_result,

    "tables": tables

}