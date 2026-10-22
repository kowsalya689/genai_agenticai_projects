import re

# ------------------------
# Medical Dictionaries
# ------------------------

MEDICINES = {
    "paracetamol",
    "metformin",
    "azithromycin",
    "amoxicillin",
    "ibuprofen",
    "atorvastatin",
    "rosuvastatin",
    "aspirin",
    "insulin",
    "amlodipine",
    "losartan",
    "ceftriaxone",
    "pantoprazole",
    "omeprazole",
    "doxycycline",
    "ciprofloxacin"
}

DISEASES = {
    "diabetes",
    "diabetes mellitus",
    "type 2 diabetes mellitus",
    "hypertension",
    "asthma",
    "pneumonia",
    "community-acquired pneumonia",
    "copd",
    "tuberculosis",
    "covid-19",
    "dengue",
    "malaria",
    "migraine"
}

LAB_TESTS = {
    "cbc",
    "wbc",
    "wbc count",
    "hb",
    "hba1c",
    "blood sugar",
    "glucose",
    "ecg",
    "x-ray",
    "ct scan",
    "mri",
    "creatinine",
    "hemoglobin"
}

FREQUENCIES = [
    "once daily",
    "twice daily",
    "three times daily",
    "every 6 hours",
    "every 8 hours",
    "after meals",
    "before meals",
    "at bedtime",
    "SOS"
]

DOSAGE_PATTERN = r"\b\d+(?:\.\d+)?\s?(?:mg|mcg|g|ml)\b(?!\/)"

TEST_VALUE_PATTERN = (
    r"\d+\.?\d*%|"
    r"\d+\s?mg/dL|"
    r"\d+,?\d*\s?cells/uL"
)

DATE_PATTERNS = [
    r"\d{1,2}\s(?:Jan|January|Feb|February|Mar|March|Apr|April|May|Jun|June|Jul|July|Aug|August|Sep|September|Oct|October|Nov|November|Dec|December)\s\d{4}",
    r"\d{4}-\d{2}-\d{2}"
]