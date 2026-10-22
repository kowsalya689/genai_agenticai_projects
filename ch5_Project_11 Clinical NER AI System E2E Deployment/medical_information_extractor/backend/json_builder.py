from datetime import datetime


def build_json(extracted_data):
    """
    Convert extracted entities into a clean JSON structure.
    """

    return {

        "metadata": {

            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

            "status": "Success"

        },

        "patient_information": {

            "patient": extracted_data.get("patient", ""),

            "age": extracted_data.get("age", ""),

            "gender": extracted_data.get("gender", ""),

            "doctor": extracted_data.get("doctor", ""),

            "hospital": extracted_data.get("hospital", ""),

            "date": extracted_data.get("date", "")

        },

        "clinical_information": {

            "disease": extracted_data.get("disease", []),

            "medicine": extracted_data.get("medicine", []),

            "dosage": extracted_data.get("dosage", []),

            "frequency": extracted_data.get("frequency", [])

        },

        "laboratory_information": {

            "lab_tests": extracted_data.get("lab_tests", []),

            "test_values": extracted_data.get("test_values", [])

        },

        "medications": extracted_data.get("medications", [])

    }