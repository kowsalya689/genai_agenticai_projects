from pprint import pprint

from pdf_reader import extract_text
from entity_extractor import extract_information
from json_builder import build_json

text = extract_text("uploads/sample_medical_report.pdf")

entities = extract_information(text)

result = build_json(entities)

pprint(result)