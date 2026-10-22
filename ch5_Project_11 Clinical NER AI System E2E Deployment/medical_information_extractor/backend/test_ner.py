from pdf_reader import extract_text
from ner_engine import extract_entities

text = extract_text("uploads/sample_medical_report.pdf")

entities = extract_entities(text)

print("=" * 60)
print("Detected Entities")
print("=" * 60)

for entity in entities:
    print(entity)