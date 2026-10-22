from pprint import pprint

from pdf_reader import extract_text
from entity_extractor import extract_information
from json_builder import build_json
from table_builder import build_tables

text = extract_text("uploads/sample_medical_report.pdf")

entities = extract_information(text)

json_data = build_json(entities)

tables = build_tables(json_data)

pprint(tables)