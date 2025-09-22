import chainlit as cl
import json
from ai_teacher_assistant import StudentProfile, get_academic_level, ask_openai

# Helper: Profile --> readable string 
def format_profile(profile: StudentProfile) -> str:
    return (
        f"👤 Student Name: {profile.Student_Name}\n"
        f"🏫 Academic Name: {profile.Academic_Name}\n"
        f"🎓 Academic Level: {profile.Academic_Level}\n"
        f"📘 Class: {profile.Class}\n"
        f"📚 Subject: {profile.Subject}"
    )

def menu_text() -> str:
    return (
        "⚡ Options:\n"
        "1️⃣ Ask a Question\n"
        "2️⃣ Change Subject\n"
        "3️⃣ Change Student\n"
        "4️⃣ Start New Session\n"
        "5️⃣ Exit Session"
    )

# Start new chat
@cl.on_chat_start
async def start():
    cl.user_session.set("step", "name")
    cl.user_session.set("temp_data", {})
    cl.user_session.set("student_profile", None)

    await cl.Message(
        content="👋 Welcome! Let's build your student profile.\nPlease enter your Name:"
    ).send()

# Handle messages
@cl.on_message
async def main(message: cl.Message):
    step = cl.user_session.get("step")
    temp_data = cl.user_session.get("temp_data")
    student_profile: StudentProfile = cl.user_session.get("student_profile")

    # STEP 1: build profile
    if student_profile is None:
        if step == "name":
            temp_data["name"] = message.content.strip()
            cl.user_session.set("step", "academic")
            await cl.Message(content="🏫 Enter your Academic Name (School/College/University):").send()

        elif step == "academic":
            temp_data["academic_name"] = message.content.strip()
            cl.user_session.set("step", "class")
            await cl.Message(content="📘 Enter your Class (number):").send()

        elif step == "class":
            try:
                class_num = int(message.content.strip())
                temp_data["class_num"] = class_num
                cl.user_session.set("step", "subject")
                await cl.Message(content="📚 Enter your Subject:").send()
            except ValueError:
                await cl.Message(content="⚠️ Please enter a valid number for Class.").send()

        elif step == "subject":
            temp_data["subject"] = message.content.strip()

            # Profile create karo
            student_profile = StudentProfile(
                Student_Name=temp_data["name"],
                Academic_Name=temp_data["academic_name"],
                Academic_Level=get_academic_level(temp_data["class_num"]),
                Class=temp_data["class_num"],
                Subject=temp_data["subject"],
            )

            cl.user_session.set("student_profile", student_profile)
            cl.user_session.set("step", "menu")

            await cl.Message(content="✅ Profile Created:\n" + format_profile(student_profile)).send()
            await cl.Message(content=menu_text()).send()

    # STEP 2: after build profile
    else:
        if step == "menu":
            choice = message.content.strip()
            if choice == "1":
                cl.user_session.set("step", "ask")
                await cl.Message(content="❓ Please enter your question:").send()

            elif choice == "2":
                cl.user_session.set("step", "change_subject")
                await cl.Message(content="📚 Enter new Subject:").send()

            elif choice == "3":
                # Reset student
                cl.user_session.set("student_profile", None)
                cl.user_session.set("temp_data", {})
                cl.user_session.set("step", "name")
                await cl.Message(content="🔄 Switching Student... Enter Name:").send()

            elif choice == "4":
                # Restart session
                cl.user_session.set("student_profile", None)
                cl.user_session.set("temp_data", {})
                cl.user_session.set("step", "name")
                await cl.Message(content="🚀 Starting new session...\nPlease enter your Name:").send()

            elif choice == "5":
                await cl.Message(content="👋 Exiting session. Goodbye!").send()
                await cl.stop()
            else:
                await cl.Message(content="⚠️ Invalid choice, select 1-5.").send()

        elif step == "ask":
            answer = ask_openai(message.content, student_profile)
            await cl.Message(content=f"🧑‍🏫 Answer:\n{answer}").send()
            cl.user_session.set("step", "menu")
            await cl.Message(content=menu_text()).send()

        elif step == "change_subject":
            student_profile.Subject = message.content.strip()
            cl.user_session.set("student_profile", student_profile)
            cl.user_session.set("step", "menu")
            await cl.Message(content=f"✅ Subject updated to {student_profile.Subject}").send()
            await cl.Message(content=menu_text()).send()