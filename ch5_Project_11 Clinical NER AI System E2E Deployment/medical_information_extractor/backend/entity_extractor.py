# import os
# import spacy

from medication_mapper import map_medications
from data_cleaner import clean_entities

# # Load your fine-tuned BioClinicalBERT model
# MODEL_PATH = os.path.join(
#     os.path.dirname(__file__),
#     "model-best"
# )

# print(MODEL_PATH)

# nlp = spacy.load(MODEL_PATH)
import os
import spacy

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(BASE_DIR, "model-best")

print("Model path:", MODEL_PATH)
print("Exists:", os.path.exists(MODEL_PATH))

nlp = spacy.load(MODEL_PATH)


def extract_information(text):

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

    doc = nlp(text)

    for ent in doc.ents:

        value = ent.text.strip()
        label = ent.label_

        if label == "PATIENT":
            data["patient"] = value

        elif label == "AGE":
            data["age"] = value

        elif label == "GENDER":
            data["gender"] = value

        elif label == "DOCTOR":
            data["doctor"] = value

        elif label == "HOSPITAL":
            data["hospital"] = value

        elif label == "DATE":
            data["date"] = value

        elif label == "DISEASE":
            if value not in data["disease"]:
                data["disease"].append(value)

        elif label == "MEDICINE":
            if value not in data["medicine"]:
                data["medicine"].append(value)

        elif label == "DOSAGE":
            if value not in data["dosage"]:
                data["dosage"].append(value)

        elif label == "FREQUENCY":
            if value not in data["frequency"]:
                data["frequency"].append(value)

        elif label == "LAB_TEST":
            if value not in data["lab_tests"]:
                data["lab_tests"].append(value)

        elif label == "TEST_VALUE":
            if value not in data["test_values"]:
                data["test_values"].append(value)

    # Medication Mapping
    data["medications"] = map_medications(
        text,
        data["medicine"]
    )

    # Clean duplicates / empty values
    data = clean_entities(data)

    return data