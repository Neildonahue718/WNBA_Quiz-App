import streamlit as st
import pandas as pd
import random
import time

# --- Load Data ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('https://docs.google.com/spreadsheets/d/e/2PACX-1vSo78o_XcjeBYWvYnDBaSolSgf6JAGvBCBSNipn9iLe7KsZkfLI3XCGbVb90oT0wsD57K6h7lR1H5wo/pub?output=csv')
        df = df[['Player', 'Team', 'Age', 'Ht', 'Exp', 'College', 'Pos', 'Draft Pick']].dropna().drop_duplicates()
        return df
    except FileNotFoundError:
        st.error("Error: Google Sheet not found.")
        return pd.DataFrame()

# --- Question Generator ---
def get_question(df, category):
    player_info = df.sample(n=1).iloc[0]
    if category == 'Draft Pick':
        correct_answer = player_info['Player']
        question = player_info['Draft Pick']
        choices_pool = df['Player'].dropna().unique().tolist()
    elif category == 'Age':
        correct_answer = player_info['Age']
        question = player_info['Player']
        correct_numeric = int(correct_answer)
        pool = sorted(set(int(a) for a in df['Age'].dropna().unique() if abs(int(a) - correct_numeric) >= 2))
        sampled = random.sample(pool, k=3) if len(pool) >= 3 else pool
        options = [correct_numeric] + sampled
        random.shuffle(options)
        return question, options, correct_numeric
    else:
        correct_answer = player_info[category]
        question = player_info['Player']
        choices_pool = df[category].dropna().unique().tolist()

    other_choices = [c for c in choices_pool if c != correct_answer]
    sampled = random.sample(other_choices, k=3) if len(other_choices) >= 3 else other_choices
    options = [correct_answer] + sampled
    random.shuffle(options)

    return question, options, correct_answer

# --- Main App ---
# (main app logic remains unchanged)
