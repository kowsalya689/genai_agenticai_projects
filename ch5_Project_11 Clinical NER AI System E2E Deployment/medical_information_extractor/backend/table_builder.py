def build_tables(data):
    """
    Convert extracted JSON into frontend-friendly tables.
    """

    patient = data["patient_information"]
    clinical = data["clinical_information"]
    labs = data["laboratory_information"]
    medications = data["medications"]

    # -----------------------
    # Patient Table
    # -----------------------

    patient_table = [
        {"Field": "Patient", "Value": patient["patient"]},
        {"Field": "Age", "Value": patient["age"]},
        {"Field": "Gender", "Value": patient["gender"]},
        {"Field": "Doctor", "Value": patient["doctor"]},
        {"Field": "Hospital", "Value": patient["hospital"]},
        {"Field": "Date", "Value": patient["date"]},
    ]

    # -----------------------
    # Disease Table
    # -----------------------

    disease_table = []

    for disease in clinical["disease"]:
        disease_table.append({
            "Disease": disease
        })

    # -----------------------
    # Medication Table
    # -----------------------

    medication_table = []

    for med in medications:

        medication_table.append({

            "Medicine": med["medicine"],

            "Dosage": med["dosage"],

            "Frequency": med["frequency"]

        })

    # -----------------------
    # Laboratory Table
    # -----------------------

    lab_table = []

    tests = labs["lab_tests"]
    values = labs["test_values"]

    for i in range(max(len(tests), len(values))):

        lab_table.append({

            "Lab Test": tests[i] if i < len(tests) else "",

            "Result": values[i] if i < len(values) else ""

        })

    return {

        "patient_table": patient_table,

        "disease_table": disease_table,

        "medication_table": medication_table,

        "lab_table": lab_table

    }