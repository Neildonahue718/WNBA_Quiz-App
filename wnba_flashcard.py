import streamlit as st
import pandas as pd
import random

@st.cache_data
def load_data():
    try:
        df = pd.read_csv('https://docs.google.com/spreadsheets/d/e/2PACX-1vSo78o_XcjeBYWvYnDBaSolSgf6JAGvBCBSNipn9iLe7KsZkfLI3XCGbVb90oT0wsD57K6h7lR1H5wo/pub?output=csv')
        df = df[['Player', 'Team', 'Age', 'Ht', 'Exp', 'College', 'Pos', 'Draft Pick']].dropna().drop_duplicates()
        return df
    except Exception as e:
        st.error(f"❌ Failed to load data: {e}")
        return pd.DataFrame()

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
    elif category == 'Ht':
        def height_to_inches(height):
            parts = height.replace("\"", "").split("'")
            return int(parts[0]) * 12 + int(parts[1]) if len(parts) == 2 else None

        correct_answer = player_info['Ht']
        correct_inches = height_to_inches(correct_answer)
        question = player_info['Player']
        valid_heights = df['Ht'].dropna().unique().tolist()
        spaced = [h for h in valid_heights if height_to_inches(h) and abs(height_to_inches(h) - correct_inches) >= 2]
        sampled = random.sample(spaced, k=3) if len(spaced) >= 3 else spaced
        options = [correct_answer] + sampled
        random.shuffle(options)
        return question, options, correct_answer
    else:
        correct_answer = player_info[category]
        question = player_info['Player']
        choices_pool = df[category].dropna().unique().tolist()

    other_choices = [c for c in choices_pool if c != correct_answer]
    sampled = random.sample(other_choices, k=3) if len(other_choices) >= 3 else other_choices
    options = [correct_answer] + sampled
    random.shuffle(options)
    return question, options, correct_answer

quiz_options = {
    'Team': 'Team',
    'Age': 'Age',
    'Height': 'Ht',
    'WNBA Experience': 'Exp',
    'College/Country': 'College',
    'Draft Pick': 'Draft Pick'
}

if 'score' not in st.session_state:
    st.session_state.update({
        'score': 0,
        'q_number': 1,
        'correct': None,
        'missed': [],
        'awaiting_input': True,
        'used_players': set(),
        'current_q': None
    })

df = load_data()

if not df.empty:
    if st.session_state.q_number > 20:
        st.subheader("🏁 Quiz Complete!")
        st.write(f"Your final score: {st.session_state.score} out of 20")
        if st.button("🔄 Restart Quiz"):
            st.session_state.update({
                'score': 0,
                'q_number': 1,
                'correct': None,
                'missed': [],
                'awaiting_input': True,
                'used_players': set(),
                'current_q': None
            })
            st.rerun()
        st.stop()

    if 'current_q' not in st.session_state or not st.session_state.awaiting_input:
        team_questions = ['Team'] * 10
        other_keys = [k for k in quiz_options if k != 'Team']
        other_questions = random.choices(other_keys, k=10)
        question_categories = team_questions + other_questions
        random.shuffle(question_categories)
        selected_category = question_categories[(st.session_state.q_number - 1) % len(question_categories)]

        filtered_df = df[~df['Player'].isin(st.session_state.used_players)]
        if filtered_df.empty:
            st.session_state.used_players = set()
            filtered_df = df.copy()

        question, choices, answer = get_question(filtered_df, quiz_options[selected_category])
        st.session_state.current_q = (question, choices, answer, selected_category)
        st.session_state.used_players.add(question)
        st.session_state.awaiting_input = True
        st.session_state.selected_answer = None

    if st.session_state.current_q:
        question, choices, correct_answer, category_display = st.session_state.current_q

        st.title("🏀 WNBA Flashcard Trainer")
        st.subheader(f"Question {st.session_state.q_number} of 20")

        if category_display == 'Team':
            st.write(f"{question} plays for what team?")
        elif category_display == 'Draft Pick':
            st.write(f"Who was selected with the draft pick: **{question}**?")
        else:
            st.write(f"What is the **{'WNBA experience' if category_display == 'WNBA Experience' else category_display.lower()}** of **{question}**?")

        for option in choices:
            if st.session_state.awaiting_input:
                if st.button(str(option), key=option):
                    st.session_state.awaiting_input = False
                    st.session_state.selected_answer = option
                    if option == correct_answer:
                        st.success("✅ Correct!")
                        st.session_state.score += 1
                    else:
                        st.error(f"❌ Incorrect. The correct answer was: {correct_answer}")
                        st.session_state.missed.append({
                            'question': f"{('Who was selected with the draft pick: ' + question) if category_display == 'Draft Pick' else f'What is the {category_display.lower()} of {question}?'}",
                            'your_answer': option,
                            'correct_answer': correct_answer
                        })
                    st.session_state.q_number += 1
                    st.session_state.current_q = None
                    st.rerun()

        st.markdown(f"**Current Score:** {st.session_state.score} / {min(st.session_state.q_number - 1, 20)}")
else:
    st.warning("⚠️ No data found! Please check the Google Sheet link.")
    st.stop()
