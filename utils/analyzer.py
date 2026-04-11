from transformers import pipeline
from utils.preprocess import clean_text

# Load models
sentiment_model = pipeline("sentiment-analysis")
summarizer = pipeline("summarization")

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
    try:
        summary_result = summarizer(cleaned_text, max_length=30, min_length=10, do_sample=False)
        summary = summary_result[0]['summary_text']
    except:
        summary = "Summary not available"

    return sentiment, category, summary, reason