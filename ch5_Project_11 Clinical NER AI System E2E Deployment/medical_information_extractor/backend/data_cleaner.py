def normalize_text(text):
    """
    Normalize text by trimming whitespace and converting
    to title case.
    """
    if not text:
        return ""

    return " ".join(text.strip().split()).title()


def remove_duplicates(items):
    """
    Remove duplicates while preserving order.
    Comparison is case-insensitive.
    """
    seen = set()
    cleaned = []

    for item in items:

        if not item:
            continue

        normalized = normalize_text(item)

        key = normalized.lower()

        if key not in seen:
            seen.add(key)
            cleaned.append(normalized)

    return cleaned


def clean_entities(data):
    """
    Clean extracted entities.
    """

    data["disease"] = remove_duplicates(data.get("disease", []))

    data["medicine"] = remove_duplicates(data.get("medicine", []))

    data["lab_tests"] = remove_duplicates(data.get("lab_tests", []))

    data["dosage"] = remove_duplicates(data.get("dosage", []))

    data["frequency"] = remove_duplicates(data.get("frequency", []))

    data["test_values"] = remove_duplicates(data.get("test_values", []))

    return data