import os
import pandas as pd
from src.data.preprocess import clean_batch


def process_dataset():

    print("Script Started")

    # Load raw dataset
    df = pd.read_csv(
        "data/raw/email_spam.csv",
        encoding="latin1"
    )

    print("Dataset Loaded")
    print("Original Columns:", df.columns.tolist())

    # Remove spaces from column names
    df.columns = df.columns.astype(str).str.strip()

    # -------------------------------------------------
    # Find LABEL column
    # -------------------------------------------------

    possible_label_columns = [
        "label",
        "v1",
        "category",
        "class",
        "target",
        "spam"
    ]

    label_column = None

    for column in possible_label_columns:
        if column in df.columns:
            label_column = column
            break

    if label_column is None:
        raise ValueError(
            "Label column not found. "
            f"Available columns: {df.columns.tolist()}"
        )

    print("Label Column:", label_column)

    # Standardize label column
    df["label"] = (
        df[label_column]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    # -------------------------------------------------
    # Find EMAIL/TEXT column
    # -------------------------------------------------

    possible_text_columns = [
        "email_text",
        "email",
        "message",
        "text",
        "content",
        "body",
        "mail",
        "email_body",
        "v2"
    ]

    text_column = None

    for column in possible_text_columns:
        if column in df.columns:
            text_column = column
            break

    # If no standard text column is found,
    # use the first object/string column that isn't label
    if text_column is None:

        for column in df.columns:
            if column != label_column:
                if df[column].dtype == "object":
                    text_column = column
                    break

    if text_column is None:
        raise ValueError(
            "Email/text column not found. "
            f"Available columns: {df.columns.tolist()}"
        )

    print("Email Column:", text_column)

    # Create standard email_text column
    df["email_text"] = df[text_column].astype(str)

    # -------------------------------------------------
    # Text cleaning
    # -------------------------------------------------

    texts = df["email_text"].str.lower()

    texts = texts.str.replace(
        r"http\S+",
        "",
        regex=True
    )

    texts = texts.str.replace(
        r"[^a-zA-Z ]",
        "",
        regex=True
    )

    # NLP preprocessing
    df["clean_email"] = clean_batch(texts)

    print("Cleaning Completed")

    # -------------------------------------------------
    # Create processed directory
    # -------------------------------------------------

    os.makedirs(
        "data/processed",
        exist_ok=True
    )

    # Save processed dataset
    df.to_csv(
        "data/processed/cleaned_emails.csv",
        index=False
    )

    print("File Saved")

    print("\nFinal Columns:")
    print(df.columns.tolist())

    print("\nLabel Counts:")
    print(df["label"].value_counts())

    return df