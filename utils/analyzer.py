from transformers import pipeline
from utils.preprocess import clean_text

# Load models
sentiment_model = pipeline("sentiment-analysis")
summarizer = None


def get_summarizer():
    global summarizer
    if summarizer is None:
        summarizer = pipeline("summarization")
    return summarizer


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

    # --- Sentiment ---
    result = sentiment_model(cleaned_text)[0]
    sentiment = result['label']

    if sentiment == "POSITIVE":
        sentiment = "Positive"
    else:
        sentiment = "Negative"

    # --- Category ---
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

    # --- Summary ---
    # One-line complaints are already shorter than a useful model summary.
    # A structured triage summary is more useful and avoids model repetition.
    word_count = len(cleaned_text.split())
    if word_count < 25:
        summary = make_triage_summary(text, category, sentiment)
    else:
        try:
            summary_result = get_summarizer()(text.strip(), max_length=35, min_length=12, do_sample=False)
            model_summary = summary_result[0]['summary_text'].strip()

            if model_summary.lower() == cleaned_text or len(model_summary.split()) >= word_count:
                summary = make_triage_summary(text, category, sentiment)
            else:
                summary = model_summary
        except:
            summary = make_triage_summary(text, category, sentiment)

    return sentiment, category, summary, reason
