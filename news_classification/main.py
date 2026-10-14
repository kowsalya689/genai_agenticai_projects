# from src.data.load_data import load_data
 
# df = load_data("data/raw")
 
# print(df.shape)
# print(df.columns)
# print(df["news_category"].value_counts())

# from src.data.preprocess import clean_text
 
# sample = """Global smartphone sales in Q3 fall 5.7% to 36.6 cr units: Gartner"""
 
# print(clean_text(sample))

from src.data.process_dataset import process_dataset
 
process_dataset()

