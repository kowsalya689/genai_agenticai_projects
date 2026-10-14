import pandas as pd
import joblib
from collections import Counter

from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.feature_extraction.text import CountVectorizer
from imblearn.over_sampling import RandomOverSampler

from src.models.build_model import build_model


# ---------------------------------------
# Load processed dataset
# ---------------------------------------

df = pd.read_csv(
    "data/processed/cleaned_emails.csv",
    encoding="latin1"
)

df["clean_email"] = df["clean_email"].fillna("")


# ---------------------------------------
# Create imbalanced dataset
# ---------------------------------------

# Keep all ham
ham = df[df["label"] == "ham"]

# Keep only 25 spam
spam = df[df["label"] == "spam"].head(25)

imbalanced = pd.concat(
    [ham, spam],
    ignore_index=True
)

print(
    "Class counts:",
    Counter(imbalanced["label"])
)


# ---------------------------------------
# Create CountVectorizer
# ---------------------------------------

vectorizer = CountVectorizer(
    max_features=5000
)

X = vectorizer.fit_transform(
    imbalanced["clean_email"]
)

y = imbalanced["label"]


# ---------------------------------------
# Save CountVectorizer
# ---------------------------------------

joblib.dump(
    vectorizer,
    "models/count_vectorizer.pkl"
)

print(
    "CountVectorizer saved successfully."
)


# ---------------------------------------
# Train-Test Split
# ---------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)


# ---------------------------------------
# Baseline Model
# ---------------------------------------

baseline = build_model()

baseline.fit(
    X_train,
    y_train
)


# ---------------------------------------
# Evaluation
# ---------------------------------------

print("\n--- Baseline (imbalanced) ---")

print(
    classification_report(
        y_test,
        baseline.predict(X_test)
    )
)

# ---------------------------------------
# Oversampling
# ---------------------------------------

print("Before:", Counter(y_train))

ros = RandomOverSampler(
    random_state=42
)

X_res, y_res = ros.fit_resample(
    X_train,
    y_train
)

print("After: ", Counter(y_res))


# ---------------------------------------
# Optimized Model
# ---------------------------------------

optimized = build_model()

optimized.fit(
    X_res,
    y_res
)


# ---------------------------------------
# Evaluation After Oversampling
# ---------------------------------------

print("\n--- After oversampling ---")

print(
    classification_report(
        y_test,
        optimized.predict(X_test)
    )
)