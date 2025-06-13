import streamlit as st
import pandas as pd
import random
import time

# --- Load Data ---
@st.cache_data
def load_data():
    """
    Loads WNBA player data from a Google Sheet and caches it.
    Filters out necessary columns, drops NaNs, and removes duplicates.
    Includes error handling for data loading.
    """
    try:
        df = pd.read_csv('https://docs.google.com/spreadsheets/d/e/2PACX-1vSo78o_XcjeBYWvYnDBaSolSgf6JAGvBCBSNipn9iLe7KsZkfLI3XCGbVb90oT0wsD57K6h7lR1H5wo/pub?output=csv')
        df = df[['Player', 'Team', 'Age', 'Ht', 'Exp', 'College', 'Pos', 'Draft Pick']].dropna().drop_duplicates()
        return df
    except Exception as e:
        st.error(f"❌ Failed to load data: {e}")
        return pd.DataFrame()

# --- Question Generator ---
def get_question(df, category):
    """
    Generates a question based on a random player and a specified category.
    Provides correct answer and a set of multiple-choice options.
    Handles specific logic for 'Age' and 'Height' categories to ensure
    meaningful incorrect choices.
    """
    player_info = df.sample(n=1).iloc[0]

    if category == 'Draft Pick':
        correct_answer = player_info['Player']
        question = player_info['Draft Pick'] # Draft pick is the question, player is the answer
        choices_pool = df['Player'].dropna().unique().tolist()
    elif category == 'Age':
        correct_answer = player_info['Age']
        question = player_info['Player'] # Player is the question, age is the answer
        correct_numeric = int(correct_answer)
        # Generate choices that are at least 2 years away from the correct age
        pool = sorted(set(int(a) for a in df['Age'].dropna().unique() if abs(int(a) - correct_numeric) >= 2))
        sampled = random.sample(pool, k=3) if len(pool) >= 3 else pool
        options = [correct_numeric] + sampled
        random.shuffle(options)
        return question, options, correct_numeric
    elif category == 'Ht':
        # Helper function to convert height string (e.g., "6' 0\"") to inches
        def height_to_inches(height):
            parts = height.replace("\"", "").split("'")
            return int(parts[0]) * 12 + int(parts[1]) if len(parts) == 2 else None

        # Helper function to convert inches back to height string
        def inches_to_height(inches):
            return f"{inches // 12}' {inches % 12}\""

        correct_answer = player_info['Ht']
        correct_inches = height_to_inches(correct_answer)
        question = player_info['Player'] # Player is the question, height is the answer
        valid_heights = df['Ht'].dropna().unique().tolist()

        # Filter heights to ensure choices are at least 2 inches away
        spaced = []
        for h in valid_heights:
            inches = height_to_inches(h)
            if inches is not None and abs(inches - correct_inches) >= 2:
                spaced.append(h)

        sampled = random.sample(spaced, k=3) if len(spaced) >= 3 else spaced
        options = [correct_answer] + sampled
        random.shuffle(options)
        return question, options, correct_answer
    else:
        # Default behavior for other categories (Team, Exp, College)
        correct_answer = player_info[category]
        question = player_info['Player'] # Player is the question, category value is the answer
        choices_pool = df[category].dropna().unique().tolist()

    # General logic for picking other choices from the pool
    other_choices = [c for c in choices_pool if c != correct_answer]
    sampled = random.sample(other_choices, k=3) if len(other_choices) >= 3 else other_choices
    options = [correct_answer] + sampled
    random.shuffle(options)

    return question, options, correct_answer

# --- Main App ---
# Custom CSS for Streamlit buttons
st.markdown("""
    <style>
    div.stButton > button {
        background-color: #FF7F00 !important; /* Orange background */
        color: white !important; /* White text */
        border-radius: 8px; /* Rounded corners */
        padding: 10px 20px; /* Padding for better button size */
        font-size: 1.1em; /* Slightly larger font */
        box-shadow: 2px 2px 5px rgba(0,0,0,0.2); /* Subtle shadow */
        transition: all 0.2s ease-in-out; /* Smooth transition on hover */
    }
    div.stButton > button:hover {
        background-color: #E66F00 !important; /* Slightly darker orange on hover */
        transform: translateY(-2px); /* Lift effect on hover */
        box-shadow: 3px 3px 8px rgba(0,0,0,0.3); /* Enhanced shadow on hover */
    }
    </style>
""", unsafe_allow_html=True)

# Define quiz categories and their corresponding DataFrame columns
quiz_options = {
    'Team': 'Team',
    'Age': 'Age',
    'Height': 'Ht',
    'WNBA Experience': 'Exp',
    'College/Country': 'College',
    'Draft Pick': 'Draft Pick'
}

# Initialize session state variables if they don't exist
if 'score' not in st.session_state:
    st.session_state.score = 0
    st.session_state.q_number = 1 # Current question number
    st.session_state.last_answered = False # Flag if last question was answered
    st.session_state.correct = None # Tracks if last answer was correct
    st.session_state.missed = [] # List of missed questions for review
    st.session_state.category_index = 0 # Helps cycle through categories (though dynamic now)
    st.session_state.review_mode = False # Flag for review mode
    st.session_state.quiz_complete = False # Flag if entire quiz (all levels) is complete
    st.session_state.awaiting_input = True # True if awaiting user's answer, False if answer given
    st.session_state.selected_answer = None # Stores the answer selected by the user
    st.session_state.show_intro = True # Added: Show intro for the first level initially
    st.session_state.used_players = set() # Track used players in the current round

# Load player data
df = load_data()

# Level-specific configuration: number of team questions and if height questions are included
level_configs = {
    1: {'team_questions': 7, 'include_height': False},
    2: {'team_questions': 5, 'include_height': False},
    3: {'team_questions': 4, 'include_height': True},
    4: {'team_questions': 3, 'include_height': True},
    5: {'team_questions': 1, 'include_height': True},
}

# Initialize current level tracking
if 'current_level' not in st.session_state:
    st.session_state.current_level = 1

category_keys = list(quiz_options.keys())
level_names = ['The Rook', 'No Slump Sophomore', 'Cap Space Problem', 'No All Star Break for You!', 'Knoxville Forever...']

# Ensure data is loaded before proceeding with the quiz logic
if not df.empty:
    # Button to review missed answers
    if st.button("Review Missed Answers"):
        st.session_state.review_mode = True

    # Logic for Review Mode
    if st.session_state.review_mode:
        st.subheader("📝 Review Missed Questions")
        if not st.session_state.missed:
            st.info("Great job! You didn't miss any questions in the last quiz!")
        else:
            for missed in st.session_state.missed:
                st.markdown(f"**{missed['question']}**")
                st.markdown(f"Your answer: ❌ {missed['your_answer']}")
                st.markdown(f"Correct answer: ✅ {missed['correct_answer']}")
        st.stop() # Halt execution after displaying review, waiting for user to refresh or interact

    # --- Quiz Completion / Level Progression Logic ---
    # This block executes when 10 questions have been answered in the current round
    if st.session_state.q_number > 10:
        if st.session_state.score == 10 and st.session_state.current_level < 5:
            # User passed the current level, move to the next!
            st.success(f"🌟 Congratulations! You completed Level {st.session_state.current_level}!")
            st.session_state.current_level += 1
            st.session_state.show_intro = True # Trigger new level intro on next run
            # Reset quiz state for the next level
            st.session_state.q_number = 1
            st.session_state.score = 0
            st.session_state.missed = []
            st.session_state.used_players = set() # Reset used players for new level
            st.session_state.current_q = None # Clear current question to force new generation
            st.session_state.awaiting_input = True # Ready for input for the first question of the new level
            time.sleep(2) # Give user a moment to see success message
            st.rerun() # Rerun the script to apply state changes and show intro

        elif st.session_state.score == 10 and st.session_state.current_level == 5:
            # User mastered all 5 levels!
            st.balloons() # Celebrate!
            st.success("🎉 You've mastered all 5 levels of the WNBA Flashcard Trainer!")
            time.sleep(2) # Small pause for user to read success message
            st.session_state.quiz_complete = True
            st.subheader("🏁 Quiz Complete!")
            st.write(f"Your final score: {st.session_state.score} out of 10")
            # Reset state so they can potentially start a new quiz from Level 1
            st.session_state.q_number = 1
            st.session_state.score = 0
            st.session_state.missed = []
            st.session_state.used_players = set()
            st.session_state.current_q = None
            st.session_state.awaiting_input = False
            st.stop() # Stop further execution as the quiz is truly finished

        else:
            # Quiz complete, but score not 10 (or not all levels mastered perfectly)
            st.session_state.quiz_complete = True
            st.subheader("🏁 Quiz Complete!")
            st.write(f"Your final score: {st.session_state.score} out of 10")
            # Reset state for a potential new quiz
            st.session_state.q_number = 1
            st.session_state.score = 0
            st.session_state.missed = []
            st.session_state.used_players = set()
            st.session_state.current_q = None
            st.session_state.awaiting_input = False
            st.stop() # Stop further execution, user must interact (e.g., refresh) to restart or review


    # --- Level Intro Display ---
    # Show an introduction screen for the current level
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
        time.sleep(3) # Blocking sleep for intro, consider alternatives if needed
        # After showing intro, set show_intro to False and rerun to start quiz
        st.session_state.show_intro = False # Don't show intro again until next level
        st.rerun() # Trigger a rerun to move past the intro phase

    # --- Question Generation and Display ---
    # Generate a new question if 'current_q' is not set or awaiting_input is False (meaning previous question answered)
    if 'current_q' not in st.session_state or not st.session_state.awaiting_input:
        # Build round-specific question set based on current level configuration
        level_cfg = level_configs[st.session_state.current_level]
        random_pool = [k for k in quiz_options if k != 'Team']

        # Adjust random_pool based on level for 'Height' (Height questions only from Level 4)
        if st.session_state.current_level < 4:
            random_pool = [k for k in random_pool if k != 'Height']

        # Determine sample size for random categories
        sample_size = min(10 - level_cfg['team_questions'], len(random_pool))

        # Explicitly set question categories for specific levels for finer control
        if st.session_state.current_level == 1:
            question_categories = ['Team'] * 6 + ['College/Country'] * 4 # Specific categories for level 1
        elif st.session_state.current_level == 4:
            # More varied categories for level 4
            question_categories = ['Team'] * 3 + ['College/Country', 'WNBA Experience', 'Draft Pick', 'Age', 'Height', 'Draft Pick', 'Age']
        elif st.session_state.current_level == 5:
            # Most varied categories for level 5
            question_categories = ['Team'] + ['College/Country', 'WNBA Experience', 'Draft Pick', 'Age', 'Height', 'College/Country', 'Draft Pick', 'Age', 'Height']
        else:
            # Default behavior for other levels using random sampling
            question_categories = ['Team'] * level_cfg['team_questions'] + random.sample(random_pool, sample_size)

        # Select the category for the current question number (0-indexed list, 1-indexed q_number)
        selected_category = question_categories[st.session_state.q_number - 1]

        # Filter out players already used in the current round to avoid repetition
        # If all players used, reset the pool for the next round within the level
        filtered_df = df[~df['Player'].isin(st.session_state.used_players)]
        if filtered_df.empty:
            st.session_state.used_players = set()
            filtered_df = df.copy()

        # Get the question, choices, and correct answer
        question, choices, answer = get_question(filtered_df, quiz_options[selected_category])
        st.session_state.current_q = (question, choices, answer, selected_category)
        st.session_state.used_players.add(question) # Add the current player to used set
        st.session_state.awaiting_input = True # Mark as awaiting input for the new question
        st.session_state.selected_answer = None # Clear previous selection

    # Safety check: If for some reason current_q is None, stop to prevent errors
    if 'current_q' not in st.session_state or st.session_state.current_q is None:
        st.stop()

    # Unpack current question details
    question, choices, correct_answer, category_display = st.session_state.current_q

    # --- Display UI Elements (Header, Progress, Question) ---
    st.markdown(f"""
    <div style='display: flex; align-items: center; flex-direction: column; align-items: flex-start;'>
        <div style='display: flex; align-items: center;'>
            <img src='https://upload.wikimedia.org/wikipedia/commons/7/7a/Basketball.png' width='50' style='margin-right: 15px;'>
            <h1 style='margin: 0;'>WNBA Flashcard Trainer</h1>
        </div>
        <div style='background-color: #f0f0f0; padding: 4px 12px; border-radius: 4px; margin-top: 5px;'>
            <strong style='font-size: 1.4em;'>Level {st.session_state.current_level}: {
                level_names[st.session_state.current_level - 1]
            }</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f"<h3 style='margin-top: 0;'>Question {st.session_state.q_number} of 10:</h3>", unsafe_allow_html=True)
    # Display progress bar
    st.progress(st.session_state.q_number - 1, text=f"Progress: Question {st.session_state.q_number} of 10")

    # Display the actual question text based on category
    if category_display == 'Team':
        st.write(f"{question} plays for what team?")
    elif category_display == 'Draft Pick':
        st.write(f"Who was selected with the draft pick: **{question}**?")
    else:
        st.write(f"What is the **{'WNBA experience' if category_display == 'WNBA Experience' else category_display.lower()}** of **{question}**?")

    # --- Display Answer Buttons ---
    for option in choices:
        if st.button(str(option), key=f"option_{option}_{st.session_state.q_number}"): # Unique key for buttons
            if st.session_state.awaiting_input: # Only process if awaiting input
                st.session_state.awaiting_input = False # No longer awaiting input for this question
                st.session_state.selected_answer = option # Store the selected answer

                if option == correct_answer:
                    st.success("✅ Correct!")
                    st.session_state.score += 1
                    st.session_state.correct = True
                else:
                    st.error(f"❌ Incorrect. The correct answer was: {correct_answer}")
                    st.session_state.correct = False
                    # Add missed question details to the review list
                    st.session_state.missed.append({
                        'question': (f"Who was selected with the draft pick: {question}" if category_display == 'Draft Pick'
                                     else f"What is the {category_display.lower()} of {question}?"),
                        'your_answer': option,
                        'correct_answer': correct_answer
                    })
                st.session_state.q_number += 1 # Increment question number
                st.session_state.category_index += 1 # Increment category index (for old logic, now determined by level)
                time.sleep(1) # Short pause before next question/rerun
                st.rerun() # Rerun the script to display the next question or end-of-round state

    # Display current score
    st.markdown(f"**Current Score:** {st.session_state.score} / {min(st.session_state.q_number - 1, 10)}")
else:
    # Message displayed if data loading fails
    st.warning("⚠️ No data found! Please check the Google Sheet link or your internet connection.")
    st.stop() # Stop the app if data is not available
