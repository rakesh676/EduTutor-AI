import streamlit as st
from services.mcq_generator2 import generate_mcqs
from services.pinecone_service import upsert_user_data, get_user_by_email, get_all_quiz_results, store_quiz_result, get_quizzes_by_student
from passlib.hash import bcrypt
from datetime import datetime
import re
import uuid
from streamlit_oauth import OAuth2Component
import os
import requests

# Set your credentials here or load from .env
GOOGLE_CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID"
GOOGLE_CLIENT_SECRET = "YOUR_GOOGLE_CLIENT_SECRET"

oauth2 = OAuth2Component(
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    authorize_endpoint="https://accounts.google.com/o/oauth2/v2/auth",
    token_endpoint="https://oauth2.googleapis.com/token"
)

# Helper to parse quiz text
def parse_quiz_text(quiz_text):
    pattern = r"Q\d+\..*?(?=Q\d+\.|\Z)"  # Matches each question block
    blocks = re.findall(pattern, quiz_text, re.DOTALL)
    parsed = []
    for block in blocks:
        question_match = re.search(r"Q\d+\.\s*(.*?)\nA\)", block)
        options = re.findall(r"[A-D]\)\s*(.*)", block)
        answer_match = re.search(r"Answer:\s*([A-D])", block)
        if question_match and options and answer_match:
            parsed.append({
                "question": question_match.group(1).strip(),
                "options": options,
                "correct": answer_match.group(1)
            })
    return parsed

# --- Session State ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = None
    st.session_state.user_role = None
    st.session_state.user_name = None
    st.session_state.questions = []
    st.session_state.user_answers = []
    st.session_state.quiz_submitted = False
    st.session_state.score = 0
    st.session_state.total = 0

# --- Auth UI ---
def login_form():
    st.subheader("Login")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")
    if st.button("Login"):
        user = get_user_by_email(email)
        if user and bcrypt.verify(password, user["password"]):
            st.session_state.logged_in = True
            st.session_state.user_email = email
            st.session_state.user_role = user.get("role", "student")
            st.session_state.user_name = user.get("name", "")
            st.success("Logged in successfully!")
            st.rerun()
        else:
            st.error("Invalid email or password.")


def signup_form():
    st.subheader("Sign Up")
    email = st.text_input("Email", key="signup_email")
    password = st.text_input("Password", type="password", key="signup_password")
    name = st.text_input("Name", key="signup_name")
    role = st.selectbox("Role", ["student", "educator"], key="signup_role")
    if st.button("Sign Up"):
        if get_user_by_email(email):
            st.error("User already exists.")
        else:
            hashed_pw = bcrypt.hash(password)
            user_id = str(uuid.uuid4())
            user_data = {
                "email": email,
                "password": hashed_pw,
                "role": role,
                "name": name
            }
            upsert_user_data(user_id, user_data)
            st.success("Signup successful! Please log in.")


def google_login():
    st.subheader("Login with Google")
    result = oauth2.authorize_button(
        name="Login with Google",
        redirect_uri="http://localhost:8501",
        scope="openid email profile"
    )
    if result and "token" in result:
        id_token = result["token"]["id_token"]
        userinfo = requests.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {result['token']['access_token']}"}
        ).json()
        email = userinfo.get("email")
        name = userinfo.get("name")
        if email:
            user = get_user_by_email(email)
            if not user:
                user_id = str(uuid.uuid4())
                user_data = {
                    "email": email,
                    "password": "google_oauth",
                    "role": "student",
                    "name": name or email
                }
                upsert_user_data(user_id, user_data)
                role = "student"
            else:
                role = user.get("role", "student")
            st.session_state.logged_in = True
            st.session_state.user_email = email
            st.session_state.user_role = role
            st.session_state.user_name = name or email
            st.success(f"Logged in as {email} via Google!")
            st.rerun()
        else:
            st.error("Could not retrieve email from Google.")
    elif result and "error" in result:
        st.error(f"Google login error: {result['error']}")

# --- Main Auth Page ---
def auth_page():
    st.title("Welcome to the EduTutor")
    tabs = st.tabs(["Login", "Sign Up", "Google Login"])
    with tabs[0]:
        login_form()
    with tabs[1]:
        signup_form()
    with tabs[2]:
        google_login()

# --- Educator Dashboard ---
def educator_dashboard():
    st.title("Educator Dashboard")
    st.write(f"Logged in as: {st.session_state.user_email} (educator)")
    if st.button("Logout"):
        for key in ["logged_in", "user_email", "user_role", "user_name", "questions", "user_answers", "quiz_submitted", "score", "total"]:
            st.session_state[key] = None if key != "logged_in" else False
        st.rerun()
    st.header("All Student Quiz Results")
    results = get_all_quiz_results()
    if not results:
        st.info("No quiz results found.")
    else:
        import pandas as pd
        df = pd.DataFrame(results)
        df = df[['email', 'topic', 'score', 'total', 'time']] if all(col in df.columns for col in ['email','topic','score','total','time']) else df
        st.dataframe(df.rename(columns={
            'email': 'Student Email',
            'topic': 'Topic',
            'score': 'Score',
            'total': 'Total',
            'time': 'Time'
        }), use_container_width=True)

# --- Student Quiz History ---
def student_quiz_history():
    st.header("Your Quiz History")
    results = get_quizzes_by_student(st.session_state.user_email)
    if not results:
        st.info("You have not taken any quizzes yet.")
    else:
        import pandas as pd
        df = pd.DataFrame(results)
        df = df[['topic', 'score', 'total', 'time']] if all(col in df.columns for col in ['topic','score','total','time']) else df
        st.dataframe(df.rename(columns={
            'topic': 'Topic',
            'score': 'Score',
            'total': 'Total',
            'time': 'Time'
        }), use_container_width=True)

# --- Main App Logic ---
def quiz_ui():
    st.title("Quiz Generator & Taker")
    st.write(f"Logged in as: {st.session_state.user_email} ({st.session_state.user_role})")
    if st.button("Logout"):
        for key in ["logged_in", "user_email", "user_role", "user_name", "questions", "user_answers", "quiz_submitted", "score", "total"]:
            st.session_state[key] = None if key != "logged_in" else False
        st.rerun()

    # Quiz Generation UI
    with st.form("quiz_form"):
        topic = st.text_input("Enter topic")
        difficulty = st.selectbox("Select difficulty", ["easy", "medium", "hard"])
        submitted = st.form_submit_button("Generate Quiz")
        if submitted and topic:
            quiz_text = generate_mcqs(topic=topic, difficulty=difficulty, num_questions=3)
            st.session_state.questions = parse_quiz_text(quiz_text)
            st.session_state.user_answers = [None] * len(st.session_state.questions)
            st.session_state.quiz_submitted = False
            st.session_state.score = 0
            st.session_state.total = 0

    # Quiz Taking UI
    if st.session_state.questions and not st.session_state.quiz_submitted:
        st.header("Take the Quiz!")
        for i, q in enumerate(st.session_state.questions):
            st.write(f"Q{i+1}: {q['question']}")
            st.session_state.user_answers[i] = st.radio(
                f"Options for Q{i+1}", q['options'], key=f"q{i}", index=None)
        if st.button("Submit Quiz"):
            if None in st.session_state.user_answers:
                st.warning("Please answer all questions before submitting.")
            else:
                correct_answers = [q['correct'] for q in st.session_state.questions]
                user_answers = [
                    chr(65 + q['options'].index(ans)) if ans in q['options'] else None
                    for ans, q in zip(st.session_state.user_answers, st.session_state.questions)
                ]
                score = sum(ua == ca for ua, ca in zip(user_answers, correct_answers))
                st.session_state.score = score
                st.session_state.total = len(st.session_state.questions)
                st.session_state.quiz_submitted = True
                # Store quiz result in Pinecone
                quiz_data = {
                    "topic": topic,
                    "score": score,
                    "total": len(st.session_state.questions),
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                store_quiz_result(st.session_state.user_email, quiz_data)

    # Quiz Result UI
    if st.session_state.quiz_submitted:
        st.success(f"You scored {st.session_state.score} out of {st.session_state.total}")
        for i, q in enumerate(st.session_state.questions):
            st.write(f"Q{i+1}: {q['question']}")
            st.write(f"Your answer: {st.session_state.user_answers[i]}")
            st.write(f"Correct answer: {q['options'][ord(q['correct'])-65]}")
        if st.button("Try Another Quiz"):
            st.session_state.questions = []
            st.session_state.user_answers = []
            st.session_state.quiz_submitted = False
            st.session_state.score = 0
            st.session_state.total = 0

    # Student Quiz History
    student_quiz_history()

# --- App Entrypoint ---
if not st.session_state.logged_in:
    auth_page()
else:
    if st.session_state.user_role == "educator":
        educator_dashboard()
    else:
        quiz_ui() 