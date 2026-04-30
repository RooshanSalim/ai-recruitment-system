import streamlit as st
import PyPDF2
import speech_recognition as sr
import matplotlib.pyplot as plt
import math

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="AI Recruitment System", layout="wide")

# ---------------- SESSION STATE ----------------
if "questions" not in st.session_state:
    st.session_state.questions = []

if "answers" not in st.session_state:
    st.session_state.answers = []

if "final_score" not in st.session_state:
    st.session_state.final_score = 0

if "ats_score" not in st.session_state:
    st.session_state.ats_score = 0

# ---------------- VOICE INPUT ----------------
def get_voice_input():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎤 Speak now...")
        audio = r.listen(source)

    try:
        return r.recognize_google(audio)
    except:
        return ""

# ---------------- SKILLS ----------------
SKILL_KEYWORDS = {
    "python": ["python", "pandas", "numpy"],
    "data_analysis": ["analysis", "analytics", "data"],
    "sql": ["sql", "mysql", "postgres"],
    "visualization": ["tableau", "powerbi", "matplotlib"],
    "machine_learning": ["ml", "machine learning", "model"]
}

def extract_skills(text):
    text = text.lower()
    skills = set()

    for skill, words in SKILL_KEYWORDS.items():
        for w in words:
            if w in text:
                skills.add(skill)

    return skills

# ---------------- ATS ----------------
def get_ats_score(resume, jd):
    resume_skills = extract_skills(resume)
    jd_skills = extract_skills(jd)

    matched = resume_skills & jd_skills
    missing = jd_skills - resume_skills

    score = int((len(matched) / len(jd_skills)) * 100) if jd_skills else 0

    return score, matched, missing

# ---------------- QUESTIONS ----------------
def generate_questions(jd):
    skills = extract_skills(jd)

    questions = []

    if "python" in skills:
        questions.append("Explain a Python project you worked on.")
    if "sql" in skills:
        questions.append("Write a SQL query to fetch top 5 records.")
    if "data_analysis" in skills:
        questions.append("How do you analyze a dataset?")

    if not questions:
        questions = ["Tell me about yourself", "What are your strengths?"]

    return questions

# ---------------- EVALUATION ----------------
def evaluate_answer(answer):
    answer = answer.lower()
    words = len(answer.split())

    length_score = 5 if words > 30 else 3 if words > 15 else 1
    keywords = ["data", "project", "analysis", "sql", "python"]
    keyword_score = sum(1 for w in keywords if w in answer)

    score = min(length_score + keyword_score, 10)

    feedback = (
        "Excellent" if score >= 7 else
        "Average" if score >= 4 else
        "Weak"
    )

    return score, feedback

# ---------------- FINAL DECISION ----------------
def final_decision(ats, interview):
    score = (ats * 0.6) + (interview * 0.4)

    if score > 90:
        return "✅ Strong Hire"
    elif score > 75:
        return "⚠️ Consider"
    else:
        return "❌ Reject"

# ---------------- PDF ----------------
def extract_text(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for p in reader.pages:
        text += p.extract_text()
    return text

# ---------------- DASHBOARD ----------------
def show_dashboard(ats, interview):
    fig, ax = plt.subplots()
    ax.bar(["ATS", "Interview"], [ats, interview])
    st.pyplot(fig)

def show_pie(ats, interview):
    if ats == 0 and interview == 0:
        st.warning("No data to display")
        return

    fig, ax = plt.subplots()
    ax.pie([ats, interview], labels=["ATS", "Interview"], autopct="%1.1f%%")
    st.pyplot(fig)

# ---------------- UI ----------------
st.title("🤖 AI Recruitment System")

job_description = st.text_area("📝 Job Description")

# ---------------- MULTIPLE RESUME RANKING ----------------
resume_files = st.file_uploader(
    "📄 Upload Multiple Resumes",
    type=["pdf"],
    accept_multiple_files=True
)

if st.button("🏆 Rank Candidates"):
    if not resume_files or not job_description:
        st.warning("Upload resumes + job description")
    else:
        candidates = []

        for file in resume_files:
            text = extract_text(file)
            ats, _, _ = get_ats_score(text, job_description)

            final = (ats * 0.6) + (50 * 0.4)

            candidates.append((file.name, ats, final))

        ranked = sorted(candidates, key=lambda x: x[2], reverse=True)

        st.subheader("🏆 Leaderboard")

        for i, c in enumerate(ranked):
            st.write(f"{i+1}. {c[0]} — ATS: {c[1]} | Final: {int(c[2])}")

# ---------------- SINGLE ANALYSIS ----------------
single_resume = st.file_uploader("📄 Upload Single Resume", type=["pdf"])

resume_text = ""

if single_resume:
    resume_text = extract_text(single_resume)

if st.button("Analyze Resume"):
    score, matched, missing = get_ats_score(resume_text, job_description)

    st.session_state.ats_score = score

    st.metric("ATS Score", f"{score}%")
    st.write("Matched:", ", ".join(matched))
    st.write("Missing:", ", ".join(missing))

# ---------------- INTERVIEW ----------------
if st.button("Start Interview"):
    st.session_state.questions = generate_questions(job_description)
    st.session_state.answers = []

if st.session_state.questions:
    for i, q in enumerate(st.session_state.questions):
        st.write(f"Q{i+1}: {q}")

        if st.button(f"🎤 Answer {i+1}"):
            ans = get_voice_input()

            if ans:
                st.write(ans)
                st.session_state.answers.append(ans)

    if st.button("Evaluate Interview"):
        total = 0

        for a in st.session_state.answers:
            s, f = evaluate_answer(a)
            st.write(f"{s}/10 - {f}")
            total += s

        if st.session_state.answers:
            final = int((total / (len(st.session_state.answers)*10)) * 100)
            st.session_state.final_score = final

            st.metric("Interview Score", f"{final}%")

# ---------------- FINAL ----------------
if st.button("Final Decision"):
    decision = final_decision(
        st.session_state.ats_score,
        st.session_state.final_score
    )

    st.write("Final Decision:", decision)

# ---------------- DASHBOARD ----------------
if st.button("Show Dashboard"):
    ats = st.session_state.ats_score
    interview = st.session_state.final_score

    if ats is None or math.isnan(ats):
        ats = 0
    if interview is None or math.isnan(interview):
        interview = 0

    show_dashboard(ats, interview)
    show_pie(ats, interview)