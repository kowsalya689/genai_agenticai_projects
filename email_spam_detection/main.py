# from src.data.load_data import load_data

# df = load_data("data/raw/email_spam.csv")

# print(df.head())
# print(df.columns.tolist())

# print(df["v1"].value_counts())

# from src.data.preprocess import clean_text
 
# sample = """Limited offer!!! Buy now and get 50% discount."""
 
# print(clean_text(sample))

from src.data.process_dataset import process_dataset
 
process_dataset()

