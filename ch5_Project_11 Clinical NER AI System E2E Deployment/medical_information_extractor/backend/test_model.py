from entity_extractor import extract_information


text = """
Patient Name: John Smith
Age: 52
Gender: Male

Doctor: Dr. James Wilson

Hospital: Apollo Hospital

Diagnosis:
Diabetes Mellitus

Prescription
Metformin 500 mg
Twice daily

Lab Test
HbA1c
Result: 8.5%

Date:
2025-04-18
"""

result = extract_information(text)

print(result)