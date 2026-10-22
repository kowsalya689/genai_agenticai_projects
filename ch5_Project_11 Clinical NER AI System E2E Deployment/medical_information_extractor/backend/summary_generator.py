def generate_summary(data):
    """
    Generate a human-readable medical summary
    from the extracted JSON.
    """

    patient = data["patient_information"]

    clinical = data["clinical_information"]

    labs = data["laboratory_information"]

    summary = []

    # Patient Info
    summary.append(
        f"{patient['patient']}, a {patient['age']}-year-old "
        f"{patient['gender'].lower()}, visited "
        f"{patient['hospital']} on {patient['date']}."
    )

    # Doctor
    summary.append(
        f"The consultation was conducted by {patient['doctor']}."
    )

    # Diseases
    if clinical["disease"]:

        diseases = ", ".join(clinical["disease"])

        summary.append(
            f"The patient was diagnosed with {diseases}."
        )

    # Medicines
    if clinical["medicine"]:

        meds = ", ".join(clinical["medicine"])

        summary.append(
            f"Prescribed medications include {meds}."
        )

    # Lab Tests
    if labs["lab_tests"]:

        lab = ", ".join(labs["lab_tests"])

        summary.append(
            f"Laboratory investigations included {lab}."
        )

    return "\n\n".join(summary)