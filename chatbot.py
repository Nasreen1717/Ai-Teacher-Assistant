import os
import json
import chainlit as cl
from ai_teacher_assistant import StudentProfile, get_academic_level

# Create the missing functions
def map_class_to_academic_level(class_num: int) -> str:
    """Wrapper for get_academic_level function"""
    return get_academic_level(class_num)

def build_system_prompt(profile: StudentProfile) -> str:
    """Build a system prompt based on student profile"""
    return f"""You are a helpful teacher assistant. 

Student Details:
- Name: {profile.Student_Name}
- Academic Institution: {profile.Academic_Name}
- Class/Grade: {profile.Class}
- Academic Level: {profile.Academic_Level}
- Subject Focus: {profile.Subject}

Please provide educational responses appropriate for a {profile.Academic_Level} level student studying {profile.Subject}. 
Adjust your language complexity and examples to match their academic level."""

def teacher_answer_question(profile: StudentProfile, question: str) -> str:
    """Get an AI response for the student's question based on their profile"""
    try:
        from openai import OpenAI
        from dotenv import load_dotenv
        
        load_dotenv()
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
        
        system_prompt = build_system_prompt(profile)
        
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)}"

# Store user profiles and profile building state per session
user_profiles = {}
profile_building = {}

@cl.on_chat_start
async def start():
    user_id = cl.user_session.get("id", "default")
    # Initialize profile building state
    profile_building[user_id] = {
        "step": 1,
        "data": {}
    }
    
    await cl.Message("Welcome to AI Teacher Assistant! 🎓✨\n\nI'm here to help you learn! But first, let me get to know you better.\n\n**What's your name?** 😊").send()

@cl.on_message
async def main(message: cl.Message):
    text = message.content.strip()
    user_id = cl.user_session.get("id", "default")
    
    # Check if we're in profile building mode
    if user_id in profile_building:
        building_state = profile_building[user_id]
        step = building_state["step"]
        data = building_state["data"]
        
        if step == 1:  # Asking for name
            data["student_name"] = text
            building_state["step"] = 2
            await cl.Message(f"Nice to meet you, **{text}**! 👋\n\nWhich school, college, or university do you attend?").send()
            
        elif step == 2:  # Asking for institution
            data["academic_name"] = text
            building_state["step"] = 3
            await cl.Message(f"Great! So you're studying at **{text}**. 🏫\n\nWhat grade/class are you in? (Please enter a number like 5, 10, 12, etc.)").send()
            
        elif step == 3:  # Asking for class/grade
            try:
                class_num = int(text)
                if class_num < 1 or class_num > 20:
                    await cl.Message("Please enter a valid grade/class number between 1 and 20. 🤔").send()
                    return
                    
                data["student_class"] = class_num
                data["academic_level"] = map_class_to_academic_level(class_num)
                building_state["step"] = 4
                await cl.Message(f"Perfect! You're in **grade {class_num}** ({data['academic_level']} level). 📚\n\nWhat subject would you like help with today? (e.g., Math, Science, English, History, etc.)").send()
                
            except ValueError:
                await cl.Message("Please enter a valid number for your grade/class. For example: 10 🔢").send()
                
        elif step == 4:  # Asking for subject
            data["subject"] = text
            
            # Create the profile
            profile = StudentProfile(
                Student_Name=data["student_name"],
                Academic_Name=data["academic_name"],
                Class=data["student_class"],
                Academic_Level=data["academic_level"],
                Subject=data["subject"]
            )
            
            # Store profile and remove from building state
            user_profiles[user_id] = profile
            del profile_building[user_id]
            
            # Welcome message with profile summary
            welcome_msg = f"""🎉 **Profile Created Successfully!**

📋 **Your Details:**
• **Name:** {profile.Student_Name}
• **Institution:** {profile.Academic_Name}  
• **Grade:** {profile.Class} ({profile.Academic_Level} level)
• **Subject:** {profile.Subject}

✅ **All set!** Now you can ask me any questions about **{profile.Subject}** or any other topic. I'll explain things at a level that's perfect for you! 

💡 **Try asking me something like:**
• "Explain [topic] in simple terms"
• "Help me solve this problem"
• "What is [concept]?"

What would you like to learn about? 🤓"""
            
            await cl.Message(welcome_msg).send()
            
    else:
        # Profile is complete, handle regular questions
        profile = user_profiles.get(user_id)
        
        if not profile:
            # Something went wrong, restart profile building
            profile_building[user_id] = {"step": 1, "data": {}}
            await cl.Message("It seems I lost your profile information. Let's start over! 😅\n\n**What's your name?**").send()
            return
        
        # Handle special commands
        if text.lower() in ["change profile", "new profile", "reset profile"]:
            # Restart profile building
            profile_building[user_id] = {"step": 1, "data": {}}
            if user_id in user_profiles:
                del user_profiles[user_id]
            await cl.Message("Sure! Let's create a new profile. 🔄\n\n**What's your name?**").send()
            return
            
        if text.lower() in ["my profile", "show profile", "profile"]:
            profile_info = f"""📋 **Your Current Profile:**

• **Name:** {profile.Student_Name}
• **Institution:** {profile.Academic_Name}
• **Grade:** {profile.Class} ({profile.Academic_Level} level)
• **Subject Focus:** {profile.Subject}

💡 *Type "change profile" if you want to create a new one.*"""
            await cl.Message(profile_info).send()
            return
        
        # Process educational question
        try:
            await cl.Message("🤔 Let me think about that...").send()
            answer = teacher_answer_question(profile, text)
            
            response = f"**📖 Answer for {profile.Student_Name} ({profile.Academic_Level} level):**\n\n{answer}\n\n---\n💡 *Need help with something else? Just ask! You can also type \"my profile\" to see your details or \"change profile\" to start over.*"
            await cl.Message(response).send()
            
        except Exception as e:
            await cl.Message(f"❌ Sorry, I encountered an error: {str(e)}\n\nPlease try asking your question again! 🔄").send()

@cl.on_chat_end
async def end():
    # Clean up user data when chat ends
    user_id = cl.user_session.get("id", "default")
    if user_id in user_profiles:
        del user_profiles[user_id]
    if user_id in profile_building:
        del profile_building[user_id]