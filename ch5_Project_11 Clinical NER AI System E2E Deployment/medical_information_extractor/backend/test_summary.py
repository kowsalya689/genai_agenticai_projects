from pdf_reader import extract_text
from entity_extractor import extract_information
from json_builder import build_json
from summary_generator import generate_summary

text = extract_text("uploads/sample_medical_report.pdf")

entities = extract_information(text)

json_data = build_json(entities)

summary = generate_summary(json_data)

print(summary)