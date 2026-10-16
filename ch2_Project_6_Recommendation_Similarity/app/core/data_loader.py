"""Load and prepare the product catalogue (works with any CSV that has a name column)."""
import pandas as pd

from .text_processing import preprocess

TEXT_COLUMNS = ["name", "main_category", "sub_category"]
EXTRA_COLUMNS = ["image", "link", "ratings", "no_of_ratings", "discount_price", "actual_price"]


def load_catalog(path) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    if "name" not in df.columns:
        raise ValueError("Catalogue must contain at least a 'name' (title) column.")

    for col in TEXT_COLUMNS:                       # optional fields -> empty string if missing
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("").astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
    for col in EXTRA_COLUMNS:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("").astype(str)

    df = df[df["name"] != ""].drop_duplicates(subset=TEXT_COLUMNS).reset_index(drop=True)
    df.insert(0, "product_id", df.index)           # stable id = row position
    df["search_text"] = (df["name"] + " " + df["main_category"] + " " + df["sub_category"]).str.strip()
    df["processed_text"] = df["search_text"].map(preprocess)
    return df[["product_id", *TEXT_COLUMNS, *EXTRA_COLUMNS, "search_text", "processed_text"]]
