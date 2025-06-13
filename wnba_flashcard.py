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
    except Exception as e:
        st.error(f"❌ Failed to load data: {e}")
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
    elif category == 'Ht':
        def height_to_inches(height):
            parts = height.replace("\"", "").split("'")
            return int(parts[0]) * 12 + int(parts[1]) if len(parts) == 2 else None

        def inches_to_height(inches):
            return f"{inches // 12}' {inches % 12}\""

        correct_answer = player_info['Ht']
        correct_inches = height_to_inches(correct_answer)
        question = player_info['Player']
        valid_heights = df['Ht'].dropna().unique().tolist()

        # Convert and filter heights by 2 inch spacing
        spaced = []
        for h in valid_heights:
            inches = height_to_inches(h)
            if inches and abs(inches - correct_inches) >= 2:
                spaced.append(h)

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

# --- Main App ---
st.markdown("""
    <style>
    div.stButton > button {
        background-color: #FF7F00 !important;
        color: white !important;
    }
    div.stButton > button:hover {
        background-color: #FF7F00 !important;
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

quiz_options = {
    'Team': 'Team',
    'Age': 'Age',
    'Height': 'Ht',
    'WNBA Experience': 'Exp',
    'College/Country': 'College',
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
    st.session_state.selected_answer = None

df = load_data()
# Level-specific configuration
level_configs = {
    1: {'team_questions': 7, 'include_height': False},
    2: {'team_questions': 5, 'include_height': False},
    3: {'team_questions': 4, 'include_height': True},
    4: {'team_questions': 3, 'include_height': True},
    5: {'team_questions': 1, 'include_height': True},
}

# Initialize level tracking
if 'current_level' not in st.session_state:
    st.session_state.current_level = 1

category_keys = list(quiz_options.keys())

level_names = ['The Rook', 'No Slump Sophomore', 'Cap Space Problem', 'No All Star Break for You!', 'Knoxville Forever...']


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
        if st.session_state.score == 10 and st.session_state.current_level < 5:
            st.session_state.current_level += 1
            st.session_state.current_q = None
            st.session_state.q_number = 1
            st.session_state.score = 0
            st.session_state.missed = []
            st.session_state.show_intro = True
            st.rerun()
        elif st.session_state.score == 10:
            st.session_state.current_q = None
            st.success("🎉 You've mastered all 5 levels of the WNBA Flashcard Trainer!")
            time.sleep(2)

        st.session_state.q_number = 1
        st.session_state.score = 0
        st.session_state.missed = []
        st.rerun()
        st.session_state.quiz_complete = True
        st.subheader("🏁 Quiz Complete!")
        st.write(f"Your final score: {st.session_state.score} out of 10")
        st.stop()

    current_category = category_keys[st.session_state.category_index % len(category_keys)]

    if 'show_intro' in st.session_state and st.session_state.show_intro:
        level_names = ['The Rook', 'No Slump Sophomore', 'Cap Space Problem', 'No All Star Break for You!', 'Knoxville Forever...']
        level_intros = [
            "You're getting noticed. Let’s see if you belong.",
            "No slump allowed. You’ve been here before.",
            "Money’s tight, pressure’s high. Let’s work.",
            "No time off. Bring your A-game every night.",
            "Legacy time. Can you go all the way?"
        ]
        st.title(f"🔥 Level {st.session_state.current_level}: {level_names[st.session_state.current_level - 1]} 🔥")
        st.markdown(level_intros[st.session_state.current_level - 1])
        time.sleep(3)
        st.session_state.q_number = 1
        st.session_state.score = 0
        st.session_state.missed = []
        st.session_state.awaiting_input = True
        st.session_state.show_intro = False
        st.rerun()

    if 'current_q' not in st.session_state or not st.session_state.awaiting_input:
        # Build round-specific question set
        level_cfg = level_configs[st.session_state.current_level]
        random_pool = [k for k in quiz_options if k != 'Team']
        if st.session_state.current_level < 4:
            random_pool = [k for k in random_pool if k != 'Height']

        # Select question categories for this round
        sample_size = min(10 - level_cfg['team_questions'], len(random_pool))
        if st.session_state.current_level == 1:
            question_categories = ['Team'] * 6 + ['College/Country'] * 4
        elif st.session_state.current_level == 4:
            question_categories = ['Team'] * 3 + ['College/Country', 'WNBA Experience', 'Draft Pick', 'Age', 'Height', 'Draft Pick', 'Age']
        elif st.session_state.current_level == 5:
            question_categories = ['Team'] + ['College/Country', 'WNBA Experience', 'Draft Pick', 'Age', 'Height', 'College/Country', 'Draft Pick', 'Age', 'Height']
        else:
            question_categories = ['Team'] * level_cfg['team_questions'] + random.sample(random_pool, sample_size)
        else:
            question_categories = ['Team'] * level_cfg['team_questions'] + random.sample(random_pool, sample_size)
        selected_category = question_categories[st.session_state.q_number - 1]

        question, choices, answer = get_question(df, quiz_options[selected_category])
        st.session_state.current_q = (question, choices, answer, selected_category)
        st.session_state.awaiting_input = True
        st.session_state.selected_answer = None

    question, choices, correct_answer, category_display = st.session_state.current_q

    st.markdown(f"""
    <div style='display: flex; align-items: center; flex-direction: column; align-items: flex-start;'>
        <div style='display: flex; align-items: center;'>
            <img src='https://upload.wikimedia.org/wikipedia/commons/7/7a/Basketball.png' width='50' style='margin-right: 15px;'>
            <h1 style='margin: 0;'>WNBA Flashcard Trainer</h1>
        </div>
        <div style='background-color: #f0f0f0; padding: 4px 12px; border-radius: 4px; margin-top: 5px;'>
            <strong style='font-size: 1.4em;'>Level {st.session_state.current_level}: {
                ['The Rook', 'No Slump Sophomore', 'Cap Space Problem', 'No All Star Break for You!', 'Knoxville Forever...'][st.session_state.current_level - 1]
            }</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f"<h3 style='margin-top: 0;'>Question {st.session_state.q_number} of 10:</h3>", unsafe_allow_html=True)
    st.progress(st.session_state.q_number - 1, text=f"Progress: Question {st.session_state.q_number} of 10")

    if category_display == 'Team':
        st.write(f"{question} plays for what team?")
    elif category_display == 'Draft Pick':
        st.write(f"Who was selected with the draft pick: **{question}**?")
    else:
        st.write(f"What is the **{'WNBA experience' if category_display == 'WNBA Experience' else category_display.lower()}** of **{question}**?")

    for option in choices:
        if st.button(str(option), key=option):
            if st.session_state.awaiting_input:
                st.session_state.awaiting_input = False
                st.session_state.selected_answer = option

                if option == correct_answer:
                    st.success("✅ Correct!")
                    st.session_state.score += 1
                    st.session_state.correct = True
                else:
                    st.error(f"❌ Incorrect. The correct answer was: {correct_answer}")
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
    st.warning("⚠️ No data found! Please check the Google Sheet link.")
    st.stop()
