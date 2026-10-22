import re
import spacy

from medical_rules import (
    MEDICINES,
    DISEASES,
    LAB_TESTS,
    FREQUENCIES,
    DOSAGE_PATTERN,
    TEST_VALUE_PATTERN,
    DATE_PATTERNS,
)

from medication_mapper import map_medications
from data_cleaner import clean_entities

nlp = spacy.load("en_core_sci_md")


def extract_information(text):

    doc = nlp(text)

    data = {
        "patient": "",
        "age": "",
        "gender": "",
        "doctor": "",
        "hospital": "",
        "date": "",
        "disease": [],
        "medicine": [],
        "dosage": [],
        "frequency": [],
        "lab_tests": [],
        "test_values": [],
        "medications": []
    }

    # ------------------------
    # Sentence Processing
    # ------------------------

    for sent in doc.sents:

        sentence = sent.text.strip()

        lower = sentence.lower()

        # ------------------------
        # Patient
        # ------------------------

        if not data["patient"]:

            patterns = [
                r"Patient Name\s*:?\s*(.+)",
                r"Patient\s*:?\s*(.+)",
                r"Name\s*:?\s*(.+)"
            ]

            for p in patterns:

                m = re.search(p, sentence, re.I)

                if m:

                    data["patient"] = m.group(1).strip()

                    break

        # ------------------------
        # Age
        # ------------------------

        if not data["age"]:

            m = re.search(r"(\d{1,3})\s*[- ]?year[- ]?old", lower)

            if m:

                data["age"] = m.group(1)

            else:

                m = re.search(r"Age\s*:?\s*(\d+)", sentence, re.I)

                if m:

                    data["age"] = m.group(1)

        # ------------------------
        # Gender
        # ------------------------

        if not data["gender"]:

            if "male" in lower:

                data["gender"] = "Male"

            elif "female" in lower:

                data["gender"] = "Female"

        # ------------------------
        # Doctor
        # ------------------------

        if not data["doctor"]:

            m = re.search(r"(Dr\.\s*[A-Za-z .]+)", sentence)

            if m:

                data["doctor"] = m.group(1).strip()

        # ------------------------
        # Hospital
        # ------------------------

        if not data["hospital"]:

            hospital_keywords = [
                "hospital",
                "medical center",
                "clinic",
                "institute"
            ]

            for keyword in hospital_keywords:

                m = re.search(
                    rf"([A-Za-z& ]+{keyword})",
                    sentence,
                    re.I
                )

                if m:

                    data["hospital"] = m.group(1).strip()

                    break

        # ------------------------
        # Date
        # ------------------------

        if not data["date"]:

            for pattern in DATE_PATTERNS:

                m = re.search(pattern, sentence, re.I)

                if m:

                    data["date"] = m.group()

                    break

        # ------------------------
        # Disease
        # ------------------------

        for disease in DISEASES:

            if disease.lower() in lower:

                if disease not in data["disease"]:

                    data["disease"].append(disease)

        # ------------------------
        # Medicine
        # ------------------------

        for med in MEDICINES:

            if med.lower() in lower:

                if med.title() not in data["medicine"]:

                    data["medicine"].append(med.title())

        # ------------------------
        # Frequency
        # ------------------------

        for freq in FREQUENCIES:

            if freq.lower() in lower:

                if freq not in data["frequency"]:

                    data["frequency"].append(freq)

        # ------------------------
        # Lab Tests
        # ------------------------

        for lab in LAB_TESTS:

            if lab.lower() in lower:

                if lab not in data["lab_tests"]:

                    data["lab_tests"].append(lab)

    # ------------------------
    # Dosages
    # ------------------------

    data["dosage"] = list(
        set(
            re.findall(
                DOSAGE_PATTERN,
                text,
                re.I
            )
        )
    )

    # ------------------------
    # Test Values
    # ------------------------

    data["test_values"] = re.findall(
        TEST_VALUE_PATTERN,
        text,
        re.I
    )

    # ------------------------
    # Medication Mapping
    # ------------------------

    data["medications"] = map_medications(
        text,
        data["medicine"]
    )

    # ------------------------
    # Cleaning
    # ------------------------

    data = clean_entities(data)

    return data