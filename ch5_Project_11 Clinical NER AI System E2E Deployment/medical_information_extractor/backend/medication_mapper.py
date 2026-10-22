import re


def map_medications(text, medicines):
    """
    Maps medicine -> dosage -> frequency
    using the surrounding sentence.
    """

    medication_list = []

    # Split report into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)

    for medicine in medicines:

        medicine_found = False

        for sentence in sentences:

            if medicine.lower() in sentence.lower():

                medicine_found = True

                # -----------------------
                # Dosage
                # -----------------------

                dosage = ""

                dosage_match = re.search(
                    r"\b\d+\s?(?:mg|mcg|g|ml)\b",
                    sentence,
                    re.IGNORECASE,
                )

                if dosage_match:
                    dosage = dosage_match.group()

                # -----------------------
                # Frequency
                # -----------------------

                frequency = ""

                frequency_patterns = [

                    "once daily",

                    "twice daily",

                    "three times daily",

                    "every 4 hours",

                    "every 6 hours",

                    "every 8 hours",

                    "every 12 hours",

                    "after meals",

                    "before meals",

                    "at bedtime",

                    "as needed"
                ]

                found = []

                for pattern in frequency_patterns:

                    if pattern.lower() in sentence.lower():

                        found.append(pattern)

                frequency = " ".join(found)

                medication_list.append({

                    "medicine": medicine,

                    "dosage": dosage,

                    "frequency": frequency

                })

                break

        if not medicine_found:

            medication_list.append({

                "medicine": medicine,

                "dosage": "",

                "frequency": ""

            })

    return medication_list