from pprint import pprint

from pdf_reader import extract_text
from entity_extractor import extract_information

text = extract_text("uploads/sample_medical_report.pdf")

result = extract_information(text)

print("=" * 60)
print("MEDICAL INFORMATION")
print("=" * 60)

pprint(result)