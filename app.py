import streamlit as st
from utils.analyzer import analyze_complaint
from utils.vector_db import search_similar

st.set_page_config(page_title="Bank Complaint Analyzer", layout="centered")

st.title("🏦 Banking Complaint Analyzer")
st.write("Analyze customer complaints using AI")

complaint = st.text_area("Enter your complaint:")

if st.button("Analyze"):
    if complaint.strip() == "":
        st.warning("Please enter a complaint")
    else:
        sentiment, category, summary, reason = analyze_complaint(complaint)

        st.subheader("🔍 Analysis Result")
        st.success(f"Sentiment: {sentiment}")
        st.info(f"Category: {category}")
        st.info(f"Summary: {summary}")
        st.write("🧠 Reason:", reason)

        # 🔥 Similar complaints
        st.subheader("🔎 Similar Complaints")
        results = search_similar(complaint)

        for i, row in results.iterrows():
            st.write("-", row["Complaint"])