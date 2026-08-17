import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter
import re
import textstat
from nltk.corpus import stopwords
import nltk

# Safe download of NLTK data
try:
    stopwords.words('english')
except:
    nltk.download('punkt')
    nltk.download('stopwords')

st.set_page_config(page_title="Response Verification Tool", layout="wide")
st.title("LLM Response Verification Dashboard (Automatic)")
st.markdown("Just upload your CSV. The app will try to detect the important columns automatically.")

uploaded_file = st.file_uploader("Upload your harvester CSV file", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.success(f"Successfully loaded **{len(df)}** responses")

    # ---------- Automatic column detection ----------
    columns_lower = {col.lower(): col for col in df.columns}

    def find_column(possible_names):
        for name in possible_names:
            if name in columns_lower:
                return columns_lower[name]
        return None

    model_col = find_column(['model', 'agent', 'llm', 'system', 'provider'])
    question_col = find_column(['question', 'domain', 'prompt', 'topic', 'query'])
    text_col = find_column(['response', 'text', 'answer', 'output', 'content', 'completion'])

    # Show what was detected
    st.subheader("Detected columns")
    st.write(f"**Model column:** `{model_col}`")
    st.write(f"**Question column:** `{question_col}`")
    st.write(f"**Response text column:** `{text_col}`")

    # If detection failed, let user choose
    if not model_col or not text_col:
        st.warning("Could not automatically detect all columns. Please select them below:")
        cols = st.columns(3)
        with cols[0]:
            model_col = st.selectbox("Model column", df.columns)
        with cols[1]:
            question_col = st.selectbox("Question column", df.columns)
        with cols[2]:
            text_col = st.selectbox("Response text column", df.columns)

    # ---------- Basic cleaning ----------
    df['word_count'] = df[text_col].astype(str).apply(lambda x: len(str(x).split()))

    # ---------- 1. Overview by Model ----------
    st.header("1. Overview by Model")
    model_stats = df.groupby(model_col).agg(
        Responses=('word_count', 'count'),
        Avg_Words=('word_count', 'mean'),
        Median_Words=('word_count', 'median'),
        Min_Words=('word_count', 'min'),
        Max_Words=('word_count', 'max')
    ).round(1)
    st.dataframe(model_stats)

    # ---------- 2. Overview by Question ----------
    if question_col:
        st.header("2. Overview by Question")
        q_stats = df.groupby(question_col).agg(
            Responses=('word_count', 'count'),
            Avg_Words=('word_count', 'mean'),
            Median_Words=('word_count', 'median')
        ).round(1)
        st.dataframe(q_stats)

    # ---------- 3. Model × Question counts ----------
    if question_col:
        st.header("3. Number of responses (Model × Question)")
        cross = pd.crosstab(df[model_col], df[question_col])
        st.dataframe(cross)

    # ---------- 4. Quick sample viewer ----------
    st.header("4. Sample Responses")
    
    selected_model = st.selectbox("Choose a model to view samples", sorted(df[model_col].unique()))
    
    samples = df[df[model_col] == selected_model].sample(min(5, len(df[df[model_col] == selected_model])))
    
    for i, (_, row) in enumerate(samples.iterrows(), 1):
        question_name = row[question_col] if question_col else "Unknown question"
        with st.expander(f"Sample {i} | {question_name} | {row['word_count']} words"):
            st.write(row[text_col])

    st.success("Done! You can now explore your data above.")

else:
    st.info("Please upload your CSV file to begin.")
