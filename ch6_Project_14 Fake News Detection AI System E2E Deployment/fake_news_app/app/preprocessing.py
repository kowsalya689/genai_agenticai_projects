"""
Text cleaning.

This is the SAME cleaning used while training the model in the notebook.
It is important that training and the app clean text the same way, otherwise
the model sees text in a format it was never trained on.

The key step is removing the "(Reuters)" dateline. During training this stopped
the model from cheating (real articles almost always had it, fakes did not).
We keep it here so the app behaves exactly like training.
"""
import re


def clean_text(text: str) -> str:
    """Clean one piece of text and remove the Reuters shortcut."""
    if not isinstance(text, str):
        return ""
    t = text
    # remove an opening dateline like "WASHINGTON (Reuters) - " or "SEATTLE/LONDON (Reuters) -"
    t = re.sub(r'^[A-Z][A-Za-z\.\,\/\-\s]{0,40}\(Reuters\)\s*[-\u2013\u2014]\s*', '', t)
    # remove any remaining Reuters mentions
    t = re.sub(r'\(Reuters\)', ' ', t)
    t = re.sub(r'\bReuters\b', ' ', t)
    # remove web links
    t = re.sub(r'http\S+|www\.\S+', ' ', t)
    # squeeze repeated spaces / newlines into a single space
    t = re.sub(r'\s+', ' ', t).strip()
    return t
