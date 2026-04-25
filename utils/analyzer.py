import os
import re
from functools import lru_cache

from utils.preprocess import clean_text

try:
    from transformers import pipeline
except ModuleNotFoundError:
    pipeline = None


LIGHTWEIGHT_SENTIMENT_MODEL = "distilbert-base-uncased-finetuned-sst-2-english"

POSITIVE_HINTS = {
    "good",
    "great",
    "smooth",
    "helpful",
    "quick",
    "resolved",
    "satisfied",
    "happy",
    "excellent",
}
NEGATIVE_HINTS = {
    "bad",
    "delay",
    "delayed",
    "failed",
    "fraud",
    "issue",
    "problem",
    "complaint",
    "unauthorized",
    "charged",
    "debited",
    "blocked",
    "error",
    "poor",
    "refund",
    "stuck",
}


def _should_use_transformers() -> bool:
    return os.getenv("USE_TRANSFORMERS_SENTIMENT", "").strip().lower() in {"1", "true", "yes"}


@lru_cache(maxsize=1)
def get_sentiment_model():
    if pipeline is None or not _should_use_transformers():
        return None

    return pipeline("sentiment-analysis", model=LIGHTWEIGHT_SENTIMENT_MODEL)


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z']+", text.lower())


def _keyword_sentiment(text: str) -> str:
    tokens = _tokenize(text)
    positive_score = sum(token in POSITIVE_HINTS for token in tokens)
    negative_score = sum(token in NEGATIVE_HINTS for token in tokens)
    return "Positive" if positive_score > negative_score else "Negative"


def classify_sentiment(text: str) -> str:
    sentiment_model = get_sentiment_model()
    if sentiment_model is None:
        return _keyword_sentiment(text)

    try:
        result = sentiment_model(text)[0]
        return "Positive" if result["label"] == "POSITIVE" else "Negative"
    except Exception:
        return _keyword_sentiment(text)


def make_triage_summary(text, category, sentiment):
    issue = text.strip()
    if not issue:
        return "No complaint details were provided."

    issue = issue[0].lower() + issue[1:]
    category_text = category.lower()
    tone = "negative" if sentiment == "Negative" else "positive"

    return f"{tone.capitalize()} {category_text} case: customer reports that {issue}."


def analyze_complaint(text):
    cleaned_text = clean_text(text)

    sentiment = classify_sentiment(cleaned_text)

    text_lower = cleaned_text

    if "loan" in text_lower:
        category = "Loan"
        reason = "The complaint mentions loan-related terms."
    elif "credit" in text_lower:
        category = "Credit Card"
        reason = "The complaint is about credit card usage or charges."
    elif "debit" in text_lower:
        category = "Debit Card"
        reason = "The complaint involves debit card issues."
    elif "atm" in text_lower:
        category = "ATM"
        reason = "The complaint refers to ATM machine problems."
    elif "fraud" in text_lower or "unauthorized" in text_lower:
        category = "Fraud"
        reason = "The complaint indicates unauthorized or fraudulent activity."
    elif "transaction" in text_lower or "account" in text_lower:
        category = "Transaction"
        reason = "The complaint is related to account or transaction issues."
    elif "support" in text_lower or "staff" in text_lower:
        category = "Support"
        reason = "The complaint is about customer support or staff."
    elif "app" in text_lower:
        category = "App"
        reason = "The complaint is related to mobile or banking app."
    else:
        category = "Other"
        reason = "The complaint does not match predefined categories."

    summary = make_triage_summary(text, category, sentiment)

    return sentiment, category, summary, reason
