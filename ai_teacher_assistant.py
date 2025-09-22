import os
import json
from dataclasses import dataclass, asdict
from typing import Dict
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")

@dataclass
class StudentProfile:
    Student_Name: str
    Academic_Name: str
    Academic_Level: str
    Class: int
    Subject: str


# Map Class → Academic Level
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


# Collect Student Profile
def collect_student_profile() -> StudentProfile:
    name = input("Enter Student Name: ")
    academic_name = input("Enter Academic Name (School/College/Uni): ")
    class_num = int(input("Enter Class (number): "))
    subject = input("Enter Subject: ")

    level = get_academic_level(class_num)
    return StudentProfile(
        Student_Name=name,
        Academic_Name=academic_name,
        Academic_Level=level,
        Class=class_num,
        Subject=subject,
    )

# Ask OpenAI for Answer
def ask_openai(question: str, profile: StudentProfile) -> str:
    prompt = (
        f"The student profile is: {json.dumps(asdict(profile))}.\n"
        f"The student has asked: {question}\n"
        f"Please answer according to the student's Academic_Level ({profile.Academic_Level})."
    )

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "system", "content": "You are a helpful teacher assistant."},
                  {"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()


def main():
    profile = collect_student_profile()
    print("\n📘 Student Profile:")
    print(json.dumps(asdict(profile), indent=2))

    while True:
        print("\nOptions:")
        print("1. Ask a Question")
        print("2. Change Subject")
        print("3. Change Student")
        print("4. Quit")
        choice = input("Choose an option: ")

        if choice == "1":
            q = input("Enter your question: ")
            ans = ask_openai(q, profile)
            print("\n🧑‍🏫 Answer:", ans)

        elif choice == "2":
            profile.Subject = input("Enter new subject: ")
            print(f"✅ Subject changed to {profile.Subject}")

        elif choice == "3":
            profile = collect_student_profile()  # Fixed: Added parentheses
            print("\n📘 Updated Student Profile:")
            print(json.dumps(asdict(profile), indent=2))

        elif choice == "4":
            print("👋 Exiting session. Goodbye!")
            break

        else:
            print("❌ Invalid option, try again.")

if __name__ == "__main__":
    main()

