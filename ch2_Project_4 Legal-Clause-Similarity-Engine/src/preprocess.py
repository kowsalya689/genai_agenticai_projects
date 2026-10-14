
import re
import string
import spacy

# Load the English NLP model
nlp = spacy.load("en_core_web_sm")

# Keep legally important words, especially negations and obligations
stop_words = set(nlp.Defaults.stop_words)
stop_words -= {
    "no", "not", "nor", "never", "none",
    "shall", "must", "may", "cannot"
}

def preprocess_text(text):
    """Clean and tokenize a legal clause."""
    if not isinstance(text, str):
        return []

    text = text.lower()
    text = re.sub(r"\s+", " ", text).strip()

    doc = nlp(text)
    tokens = []

    for token in doc:
        if (
            not token.is_space
            and token.is_alpha
            and token.text not in stop_words
        ):
            tokens.append(token.lemma_)

    return tokens
