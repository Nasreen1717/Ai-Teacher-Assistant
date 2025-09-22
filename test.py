
import streamlit as st
import json
import os
from dataclasses import dataclass, asdict
from openai import OpenAI
from dotenv import load_dotenv

# Load local .env file
load_dotenv()

st.set_page_config(page_title="AI Teacher Assistant", page_icon="🧑‍🏫", layout="wide")

# =========================
# API KEY + MODEL SETTINGS
# =========================
def get_api_key():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("❌ OPENAI_API_KEY not found. Please add it to your .env file.")
        st.info("Create a file named `.env` with: OPENAI_API_KEY=your_key_here")
        st.stop()
    return api_key

def get_model_name():
    return os.getenv("MODEL_NAME", "gpt-4o-mini")

# Initialize OpenAI client
try:
    client = OpenAI(api_key=get_api_key())
    MODEL_NAME = get_model_name()
except Exception as e:
    st.error(f"❌ Failed to initialize OpenAI client: {e}")
    st.stop()

# =========================
# DATA CLASS
# =========================
@dataclass
class StudentProfile:
    Student_Name: str
    Academic_Name: str
    Academic_Level: str
    Class: int
    Subject: str

# =========================
# UTILS
# =========================
def get_academic_level(class_num: int) -> str:
    if 1 <= class_num <= 5:
        return "Primary"
    elif 6 <= class_num <= 8:
        return "Secondary"
    elif class_num == 9:
        return "Middle"
    elif class_num == 10:
        return "Matric"
    elif class_num in [11, 12]:
        return "Intermediate"
    elif 13 <= class_num <= 16:
        return "Graduation"
    elif class_num == 17:
        return "Master"
    elif class_num == 18:
        return "Ph.D"
    else:
        return "High Level"

def ask_openai(question: str, profile: StudentProfile) -> str:
    try:
        prompt = (
            f"You are a helpful teacher assistant.\n"
            f"Student Profile: {json.dumps(asdict(profile))}\n"
            f"Student Question: {question}\n"
            f"Please provide a step-by-step educational answer appropriate for "
            f"{profile.Academic_Level} students studying {profile.Subject}."
        )

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are an experienced and patient teacher assistant who adapts explanations to student academic levels."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ Error getting response from AI: {e}"

# =========================
# SESSION STATE
# =========================
if 'profile' not in st.session_state:
    st.session_state.profile = None
if 'current_option' not in st.session_state:
    st.session_state.current_option = "profile"
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# =========================
# MAIN APP
# =========================
def main():
    st.title("🧑‍🏫 AI Teacher Assistant")
    st.markdown("### Get personalized answers based on your academic level!")
    st.divider()

    # Sidebar
    with st.sidebar:
        st.header("📋 Menu")
        if st.button("👤 Student Profile", use_container_width=True):
            st.session_state.current_option = "profile"
        if st.button("❓ Ask Question", use_container_width=True, disabled=st.session_state.profile is None):
            st.session_state.current_option = "ask"
        if st.button("📚 Change Subject", use_container_width=True, disabled=st.session_state.profile is None):
            st.session_state.current_option = "subject"
        if st.button("🔄 Change Student", use_container_width=True):
            st.session_state.current_option = "change_student"
        st.divider()

        if st.session_state.profile:
            pr = st.session_state.profile
            st.subheader("📖 Current Profile")
            st.info(
                f"**Name:** {pr.Student_Name}\n"
                f"**Institution:** {pr.Academic_Name}\n"
                f"**Level:** {pr.Academic_Level}\n"
                f"**Class:** {pr.Class}\n"
                f"**Subject:** {pr.Subject}"
            )
        else:
            st.warning("⚠️ No profile created yet!")

    # Routing
    if st.session_state.current_option == "profile" or st.session_state.profile is None:
        show_profile_section()
    elif st.session_state.current_option == "ask":
        show_ask_question_section()
    elif st.session_state.current_option == "subject":
        show_change_subject_section()
    elif st.session_state.current_option == "change_student":
        show_change_student_section()

# =========================
# SECTIONS
# =========================
def show_profile_section():
    st.header("👤 Student Profile")
    if st.session_state.profile is None:
        st.info("📝 Please create a student profile to get started!")
    with st.form("profile_form"):
        st.subheader("📋 Enter Student Details")
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Student Name *", value=st.session_state.profile.Student_Name if st.session_state.profile else "")
            academic_name = st.text_input("Academic Institution *", value=st.session_state.profile.Academic_Name if st.session_state.profile else "")
        with col2:
            class_num = st.number_input("Class *", min_value=1, max_value=20, value=st.session_state.profile.Class if st.session_state.profile else 10)
            subject = st.text_input("Subject *", value=st.session_state.profile.Subject if st.session_state.profile else "")
        if class_num:
            level = get_academic_level(class_num)
            st.info(f"📊 Academic Level: **{level}**")
        submitted = st.form_submit_button("✅ Create/Update Profile", use_container_width=True)
        if submitted:
            if name and academic_name and subject:
                level = get_academic_level(class_num)
                st.session_state.profile = StudentProfile(
                    Student_Name=name,
                    Academic_Name=academic_name,
                    Academic_Level=level,
                    Class=class_num,
                    Subject=subject
                )
                st.success("✅ Profile created/updated successfully!")
                st.balloons()
            else:
                st.error("❌ Please fill all required fields!")

def show_ask_question_section():
    st.header("❓ Ask Your Question")
    if st.session_state.profile:
        profile = st.session_state.profile
        st.success(f"🎯 Ready to answer questions for **{profile.Student_Name}** ({profile.Academic_Level} level)")
        with st.form("question_form"):
            question = st.text_area(f"Ask anything about {profile.Subject}:", height=100)
            ask_button = st.form_submit_button("🚀 Get Answer", use_container_width=True)
            if ask_button and question:
                with st.spinner("🤔 AI Teacher is thinking..."):
                    answer = ask_openai(question, profile)
                st.session_state.chat_history.append({'question': question, 'answer': answer})
                st.subheader("🧑‍🏫 Teacher's Answer:")
                st.markdown(f"**Question:** {question}")
                st.markdown("**Answer:**")
                st.info(answer)

        if st.session_state.chat_history:
            st.divider()
            st.subheader("📚 Previous Q&A")
            if st.button("🗑️ Clear Chat History"):
                st.session_state.chat_history = []
                st.rerun()
            for i, chat in enumerate(reversed(st.session_state.chat_history), 1):
                label = f"Q{len(st.session_state.chat_history) - i + 1}: " + (chat['question'][:60] + "..." if len(chat['question']) > 60 else chat['question'])
                with st.expander(label):
                    st.markdown(f"**❓ Question:** {chat['question']}")
                    st.markdown(f"**💡 Answer:** {chat['answer']}")

def show_change_subject_section():
    st.header("📚 Change Subject")
    if st.session_state.profile:
        current_subject = st.session_state.profile.Subject
        st.info(f"Current Subject: **{current_subject}**")
        with st.form("subject_form"):
            new_subject = st.text_input("Enter New Subject:", value=current_subject)
            if st.form_submit_button("✅ Update Subject", use_container_width=True):
                if new_subject:
                    st.session_state.profile.Subject = new_subject
                    st.success(f"✅ Subject changed to: **{new_subject}**")
                    st.balloons()
                else:
                    st.error("❌ Please enter a subject name!")

def show_change_student_section():
    st.header("🔄 Change Student Profile")
    st.warning("⚠️ Creating a new student profile will clear the current profile and chat history.")
    if st.button("✅ Create New Profile", use_container_width=True):
        st.session_state.profile = None
        st.session_state.chat_history = []
        st.session_state.current_option = "profile"
        st.rerun()

# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    main()
