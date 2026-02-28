import os
import streamlit as st
import google.generativeai as genai
import openai
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

from deep_translator import GoogleTranslator
translator = GoogleTranslator(source='auto', target='en')
translated = translator.translate("Bonjour")
print(translated)

if GEMINI_API_KEY:
    openai.api_key = GEMINI_API_KEY
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-pro")
else:
    model = None
import speech_recognition as sr
import pyttsx3
from deep_translator import GoogleTranslator

# -----------------------------------
# 🌿 App Configuration
# -----------------------------------
st.set_page_config(
    page_title="Holistic Elderly Companion",
    page_icon="🌸",
    layout="centered"
)

st.title("🌸 Holistic Elderly Companion")
st.markdown("""
Your gentle companion — designed for emotional support, mindfulness, and daily wellness for senior citizens.  
Speak in your own language and let your companion guide you kindly. 💬🕊️
""")

# -----------------------------------
# 🔐 GEMINI API KEY (set in .env as GEMINI_API_KEY)
# -----------------------------------
if not GEMINI_API_KEY:
    st.warning("Set GEMINI_API_KEY in .env file to enable AI features.")
else:
    genai.configure(api_key=GEMINI_API_KEY)
# -----------------------------------
# 🌍 Language Selection
# -----------------------------------
st.subheader("🌐 Choose Your Language")
languages = {
    "English": "en",
    "Hindi (हिंदी)": "hi",
    "Marathi (मराठी)": "mr",
    "Gujarati (ગુજરાતી)": "gu",
    "Tamil (தமிழ்)": "ta",
    "Bengali (বাংলা)": "bn",
    "Telugu (తెలుగు)": "te",
}
selected_language = st.selectbox("Select Language", list(languages.keys()))
lang_code = languages[selected_language]

translator = GoogleTranslator(source='auto', target=lang_code)  

# -----------------------------------
# 🎤 Voice Input Section
# -----------------------------------
st.subheader("🎙️ Speak to Your Companion")
recognizer = sr.Recognizer()
voice_button = st.button("🎧 Start Speaking")

if voice_button:
    with sr.Microphone() as source:
        st.info("🎧 Listening... Please speak clearly.")
        audio = recognizer.listen(source, phrase_time_limit=10)
        st.info("⏳ Processing your speech...")
        try:
            text = recognizer.recognize_google(audio, language=lang_code)
            st.success(f"🗣️ You said: {text}")
        except sr.UnknownValueError:
            st.error("Sorry, I couldn't understand. Please try again.")
            text = None
        except sr.RequestError:
            st.error("Speech recognition service unavailable.")
            text = None
else:
    text = None

# -----------------------------------
# 💬 AI Companion Response
# -----------------------------------
if text and model:
    # Translate to English (for Gemini model)
    text_en = GoogleTranslator(source=lang_code, target='en').translate(text)


    holistic_prompt = f"""
    You are a kind, caring, and empathetic AI companion for elderly people.
    Your role is to provide emotional support, mindfulness guidance, 
    first-aid awareness, light humor, and holistic well-being advice.
    Avoid any medical prescriptions or diagnoses.
    Always respond gently and positively.

    The user said: "{text_en}"
    """

    try:
        response = model.generate_content(holistic_prompt)
        reply_en = response.text.strip()

        # Translate back to user's chosen language
        reply_translated = GoogleTranslator(source='en', target=lang_code).translate(reply_en)

        st.markdown(f"**🌼 Companion:** {reply_translated}")

        # Speak the reply aloud
        engine = pyttsx3.init()
        engine.setProperty("rate", 165)
        engine.say(reply_translated)
        engine.runAndWait()

    except Exception as e:
        st.error(f"⚠️ Error generating response: {e}")

def trigger_local_sos(patient_id):
    patient = Patient.query.get(patient_id)
    patient.is_emergency = True
    
    # Create a high-priority notification
    new_note = Notification(
        user_id=patient.guardian_id,
        message=f"🚨 URGENT: {patient.name} is calling for help!"
    )
    
    db.session.add(new_note)
    db.session.commit()
    speak("I have alerted your guardian.")
