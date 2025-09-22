
import streamlit as st
import json
from ai_teacher_assistant import StudentProfile, get_academic_level, ask_openai

# ---------------------------
# Helper Functions
# ---------------------------
def format_profile(profile: StudentProfile) -> str:
    return (
        f"👤 Student Name: {profile.Student_Name}\n"
        f"🏫 Academic Name: {profile.Academic_Name}\n"
        f"🎓 Academic Level: {profile.Academic_Level}\n"
        f"📘 Class: {profile.Class}\n"
        f"📚 Subject: {profile.Subject}"
    )

def menu_text():
    return [
        "Ask a Question",
        "Change Subject",
        "Change Student",
        "Start New Session",
        "Exit Session",
    ]

# ---------------------------
# Streamlit UI
# ---------------------------
def main():
    st.set_page_config(page_title="AI Teacher Assistant", page_icon="📚", layout="centered")
    st.title("🤖 AI Teacher Assistant")

    # Session states
    if "student_profile" not in st.session_state:
        st.session_state.student_profile = None
    if "menu_choice" not in st.session_state:
        st.session_state.menu_choice = None
    if "question" not in st.session_state:
        st.session_state.question = ""

    # If profile not created yet → show form
    if st.session_state.student_profile is None:
        st.subheader("📝 Build Student Profile")
        with st.form("profile_form"):
            name = st.text_input("Enter Student Name")
            academic_name = st.text_input("Enter Academic Name (School/College/University)")
            class_num = st.number_input("Enter Class (number)", min_value=1, step=1)
            subject = st.text_input("Enter Subject")
            submitted = st.form_submit_button("Create Profile")

            if submitted:
                level = get_academic_level(int(class_num))
                profile = StudentProfile(
                    Student_Name=name,
                    Academic_Name=academic_name,
                    Academic_Level=level,
                    Class=int(class_num),
                    Subject=subject,
                )
                st.session_state.student_profile = profile
                st.success("✅ Profile Created Successfully!")

    # If profile exists → show profile & menu
    if st.session_state.student_profile:
        st.subheader("📘 Student Profile")
        st.text(format_profile(st.session_state.student_profile))

        # Menu Options
        st.subheader("⚡ Options")
        choice = st.radio("Select an action:", menu_text(), key="menu_choice")

        # Handle choices
        if choice == "Ask a Question":
            st.subheader("❓ Ask Your Question")
            q = st.text_area("Enter your question:", key="question")
            if st.button("Get Answer"):
                if q.strip():
                    answer = ask_openai(q, st.session_state.student_profile)
                    st.markdown(f"🧑‍🏫 **Answer:** {answer}")
                else:
                    st.warning("Please enter a question first.")

        elif choice == "Change Subject":
            new_subject = st.text_input("Enter new Subject:")
            if st.button("Update Subject"):
                if new_subject.strip():
                    st.session_state.student_profile.Subject = new_subject.strip()
                    st.success(f"✅ Subject updated to {new_subject}")
                else:
                    st.warning("Please enter a valid subject.")

        elif choice == "Change Student":
            st.session_state.student_profile = None
            st.success("🔄 Student reset! Please create a new profile.")

        elif choice == "Start New Session":
            st.session_state.clear()
            st.success("🚀 New Session Started! Reload the page to begin.")

        elif choice == "Exit Session":
            st.session_state.clear()
            st.info("👋 Session ended. Thank you for using AI Teacher Assistant!")

if __name__ == "__main__":
    main()