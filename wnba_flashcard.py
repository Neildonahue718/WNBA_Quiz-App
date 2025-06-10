import streamlit as st
import pandas as pd
import random
import time

# --- Load Data ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('https://docs.google.com/spreadsheets/d/1C7cWDVRnCQVLRVquKoSN4dakCNZQtL5DqY4tPx6cC1Y/edit?pli=1&gid=1613698693#gid=1613698693')
        df = df[['Player', 'Team', 'Age', 'Ht', 'Exp', 'College', 'Pos', 'Draft Pick']].dropna().drop_duplicates()
        return df
    except FileNotFoundError:
        st.error("Error: 'https://docs.google.com/spreadsheets/d/1C7cWDVRnCQVLRVquKoSN4dakCNZQtL5DqY4tPx6cC1Y/edit?pli=1&gid=1613698693#gid=1613698693' not found.")
        return pd.DataFrame()

# --- Question Generator ---
def get_question(df, category):
    player_info = df.sample(n=1).iloc[0]
    if category == 'Draft Pick':
        correct_answer = player_info['Player']
        question = player_info['Draft Pick']
        choices_pool = df['Player'].dropna().unique().tolist()
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
st.title("🏀 WNBA Flashcard Trainer")
st.markdown("Sharpen your knowledge of WNBA players — one flashcard at a time!")

quiz_options = {
    'Team': 'Team',
    'Age': 'Age',
    'Height': 'Ht',
    'Experience (Years)': 'Exp',
    'College/Country': 'College',
    'Position': 'Pos',
    'Draft Pick': 'Draft Pick'
}

if 'score' not in st.session_state:
    st.session_state.score = 0
    st.session_state.q_number = 1
    st.session_state.last_answered = False
    st.session_state.correct = None
    st.session_state.missed = []
    st.session_state.category_index = 0
    st.session_state.review_mode = False
    st.session_state.quiz_complete = False
    st.session_state.awaiting_input = True

# Load data
st.write("🚀 Starting the app...")
df = load_data()
st.write("📊 DataFrame loaded:", df.shape)

category_keys = list(quiz_options.keys())

if not df.empty:
    if st.button("Review Missed Answers"):
        st.session_state.review_mode = True

    if st.session_state.review_mode:
        st.subheader("📝 Review Missed Questions")
        for missed in st.session_state.missed:
            st.markdown(f"**{missed['question']}**")
            st.markdown(f"Your answer: ❌ {missed['your_answer']}")
            st.markdown(f"Correct answer: ✅ {missed['correct_answer']}")
        st.stop()

    if st.session_state.q_number > 10:
        st.session_state.quiz_complete = True
        st.subheader("🏁 Quiz Complete!")
        st.write(f"Your final score: {st.session_state.score} out of 10")
        st.stop()

    current_category = category_keys[st.session_state.category_index % len(category_keys)]

    if 'current_q' not in st.session_state or not st.session_state.awaiting_input:
        question, choices, answer = get_question(df, quiz_options[current_category])
        st.session_state.current_q = (question, choices, answer, current_category)
        st.session_state.awaiting_input = True

    question, choices, correct_answer, category_display = st.session_state.current_q

    st.subheader(f"Question {st.session_state.q_number} of 10:")
    if category_display == 'Draft Pick':
        st.write(f"Who was selected with the draft pick: **{question}**?")
    else:
        st.write(f"What is the **{category_display.lower()}** of **{question}**?")

    for option in choices:
        if st.session_state.awaiting_input and st.button(str(option)):
            st.session_state.awaiting_input = False
            if option == correct_answer:
                st.markdown(f"<div style='padding:1em;background-color:#d4edda;border-radius:0.5em;'>✅ Correct!</div>", unsafe_allow_html=True)
                st.session_state.score += 1
                st.session_state.correct = True
            else:
                st.markdown(f"<div style='padding:1em;background-color:#f8d7da;border-radius:0.5em;'>❌ Incorrect. The correct answer was: {correct_answer}</div>", unsafe_allow_html=True)
                st.session_state.correct = False
                st.session_state.missed.append({
                    'question': f"{('Who was selected with the draft pick: ' + question) if category_display == 'Draft Pick' else f'What is the {category_display.lower()} of {question}?'}",
                    'your_answer': option,
                    'correct_answer': correct_answer
                })
            st.session_state.q_number += 1
            st.session_state.category_index += 1
            time.sleep(1)
            st.rerun()

    st.markdown(f"**Current Score:** {st.session_state.score} / {min(st.session_state.q_number - 1, 10)}")
else:
    st.warning("⚠️ No data found! Please check the CSV file.")
    st.stop()
