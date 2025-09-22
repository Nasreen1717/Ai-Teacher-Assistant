# ================================
# 📌 AI Teacher Assistant (Streamlit App)
# ================================

# ---------- Imports ----------
import os
import json
from dataclasses import dataclass, asdict
from dotenv import load_dotenv
import streamlit as st
from openai import OpenAI


# ---------- Load Environment Variables ----------
load_dotenv()


# ---------- Page Config ----------
st.set_page_config(
    page_title="AI Teacher Assistant",
    page_icon="🧑‍🏫",
    layout="wide"
)


# ---------- API Key Handling ----------
def get_api_key():
    """Fetch OpenAI API key from Streamlit secrets or environment variables."""
    try:
        return st.secrets["OPENAI_API_KEY"]
    except (KeyError, FileNotFoundError):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            st.error("❌ OPENAI_API_KEY not found. Please set it in environment variables or Streamlit secrets.")
            st.info("""
            **For Local Development:**
            1. Create a `.env` file in your project directory
            2. Add: `OPENAI_API_KEY=your_api_key_here`
            
            **For Streamlit Cloud:**
            1. Go to App Settings
            2. Add OPENAI_API_KEY in Secrets section
            """)
            st.stop()
        return api_key


def get_model_name():
    """Fetch OpenAI model name with fallback."""
    try:
        return st.secrets.get("MODEL_NAME", "gpt-4o-mini")
    except (KeyError, FileNotFoundError):
        return os.getenv("MODEL_NAME", "gpt-4o-mini")


# ---------- Initialize OpenAI Client ----------
try:
    client = OpenAI(api_key=get_api_key())
    MODEL_NAME = get_model_name()
except Exception as e:
    st.error(f"❌ Failed to initialize OpenAI client: {str(e)}")
    st.stop()


# ---------- Data Model ----------
@dataclass
class StudentProfile:
    Student_Name: str
    Academic_Name: str
    Academic_Level: str
    Class: int
    Subject: str


# ---------- Utility: Map Class → Academic Level ----------
def get_academic_level(class_num: int) -> str:
    """Map class number to academic level."""
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


# ---------- OpenAI Query ----------
def ask_openai(question: str, profile: StudentProfile) -> str:
    """Send a question to OpenAI API with student profile context."""
    try:
        prompt = (
            f"The student profile is: {json.dumps(asdict(profile))}.\n"
            f"The student has asked: {question}\n"
            f"Please answer according to the student's Academic_Level ({profile.Academic_Level})."
        )

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful teacher assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ Error getting response: {str(e)}"


# ---------- Session State Initialization ----------
if "profile" not in st.session_state:
    st.session_state.profile = None
if "current_option" not in st.session_state:
    st.session_state.current_option = "profile"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# ================================
# 📌 Sections
# ================================
def section_profile():
    """Student Profile Section"""
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

            # Subject selection (with free text fallback)
            subjects = ["Mathematics", "Physics", "Chemistry", "Biology", "Computer Science", "English", "History", "Geography", "Other"]
            
            # Set default index based on current profile
            default_index = 0
            if st.session_state.profile and st.session_state.profile.Subject in subjects:
                default_index = subjects.index(st.session_state.profile.Subject)
            elif st.session_state.profile and st.session_state.profile.Subject not in subjects:
                default_index = subjects.index("Other")
            
            selected_subject = st.selectbox("Select Subject *", subjects, index=default_index)
            
            if selected_subject == "Other":
                subject = st.text_input("Enter Custom Subject *", 
                                      value=st.session_state.profile.Subject if st.session_state.profile and st.session_state.profile.Subject not in subjects else "")
            else:
                subject = selected_subject

        # Academic level preview
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
                    Subject=subject,
                )
                st.success("✅ Profile created/updated successfully!")
                st.toast("Profile updated 🎉")
                st.subheader("📘 Profile Summary")
                st.json(asdict(st.session_state.profile))
            else:
                st.error("❌ Please fill all required fields!")


def section_ask_question():
    """Ask Question Section"""
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

                st.session_state.chat_history.append({
                    "question": question,
                    "answer": answer,
                })

                st.subheader("🧑‍🏫 Teacher's Answer:")
                st.markdown(f"**Question:** {question}")
                st.info(answer)

        # Chat History
        if st.session_state.chat_history:
            st.divider()
            st.subheader("📚 Previous Questions & Answers")

            if st.button("🗑️ Clear Chat History"):
                st.session_state.chat_history = []
                st.rerun()

            for i, chat in enumerate(reversed(st.session_state.chat_history), 1):
                with st.expander(f"Q{len(st.session_state.chat_history) - i + 1}: {chat['question'][:60]}..."):
                    st.markdown(f"**❓ Question:** {chat['question']}")
                    st.markdown(f"**💡 Answer:** {chat['answer']}")


def section_change_subject():
    """Change Subject Section"""
    st.header("📚 Change Subject")

    if st.session_state.profile:
        current_subject = st.session_state.profile.Subject
        st.info(f"Current Subject: **{current_subject}**")

        with st.form("subject_form"):
            new_subject = st.text_input("Enter New Subject:", value=current_subject)

            col1, col2 = st.columns(2)

            with col1:
                if st.form_submit_button("✅ Update Subject", use_container_width=True):
                    if new_subject:
                        st.session_state.profile.Subject = new_subject
                        st.success(f"✅ Subject changed to: **{new_subject}**")
                        st.toast("Subject updated ✅")
                    else:
                        st.error("❌ Please enter a subject name!")

            with col2:
                if st.form_submit_button("🔄 Reset to Original", use_container_width=True):
                    st.session_state.profile.Subject = current_subject
                    st.info("Subject reset to original value")


def section_change_student():
    """Change Student Profile Section"""
    st.header("🔄 Change Student Profile")
    st.warning("⚠️ Creating a new student profile will clear the current profile and chat history.")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("✅ Create New Profile", use_container_width=True):
            st.session_state.profile = None
            st.session_state.chat_history = []
            st.session_state.current_option = "profile"
            st.success("Ready to create new profile!")
            st.rerun()

    with col2:
        if st.button("📝 Edit Current Profile", use_container_width=True):
            st.session_state.current_option = "profile"
            st.rerun()

    with col3:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.current_option = "ask"
            st.rerun()

    if st.session_state.profile:
        st.divider()
        st.subheader("📖 Current Profile")
        st.json(asdict(st.session_state.profile))


# ================================
# 📌 Main App Layout
# ================================
def main():
    # ---------- Header ----------
    st.title("🧑‍🏫 AI Teacher Assistant")
    st.markdown("### Get personalized answers based on your academic level!")
    st.divider()

    # ---------- Sidebar Navigation ----------
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

        # ---------- Current Profile Info ----------
        if st.session_state.profile:
            st.subheader("📖 Current Profile")
            profile = st.session_state.profile
            st.info(f"""
            **Name:** {profile.Student_Name}  
            **Institution:** {profile.Academic_Name}  
            **Level:** {profile.Academic_Level}  
            **Class:** {profile.Class}  
            **Subject:** {profile.Subject}  
            """)
        else:
            st.warning("⚠️ No profile created yet!")

    # ---------- Main Section Routing ----------
    if st.session_state.current_option == "profile" or st.session_state.profile is None:
        section_profile()
    elif st.session_state.current_option == "ask":
        section_ask_question()
    elif st.session_state.current_option == "subject":
        section_change_subject()
    elif st.session_state.current_option == "change_student":
        section_change_student()


# ---------- Run App ----------
if __name__ == "__main__":
    main()