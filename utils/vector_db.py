import re

import pandas as pd

from utils.preprocess import clean_text


data = pd.read_csv("data/complaints.csv")

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "for",
    "from",
    "has",
    "have",
    "i",
    "in",
    "is",
    "it",
    "my",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "was",
    "were",
    "with",
}


def _tokenize(text: str) -> set[str]:
    cleaned = clean_text(text)
    tokens = re.findall(r"[a-zA-Z']+", cleaned.lower())
    return {token for token in tokens if token not in STOPWORDS and len(token) > 2}


data["_tokens"] = data["Complaint"].fillna("").map(_tokenize)


def _similarity_score(query_tokens: set[str], complaint_tokens: set[str]) -> float:
    if not query_tokens or not complaint_tokens:
        return 0.0

    overlap = len(query_tokens & complaint_tokens)
    union = len(query_tokens | complaint_tokens)
    return overlap / union if union else 0.0


def search_similar(query, k=2):
    query_tokens = _tokenize(query)

    scored = data.copy()
    scored["_score"] = scored["_tokens"].map(lambda tokens: _similarity_score(query_tokens, tokens))
    scored = scored.sort_values(["_score", "Date"], ascending=[False, False])

    results = scored.drop(columns=["_tokens", "_score"]).head(k)
    return results.reset_index(drop=True)
