import os
from dotenv import load_dotenv
from azure.cognitiveservices.speech import SpeechConfig, SpeechRecognizer, AudioConfig, SpeechSynthesizer
from moviepy.editor import VideoFileClip, AudioFileClip
from googletrans import Translator, LANGUAGES as GOOGLE_LANGUAGES
import streamlit as st

# Load environment variables from .env file
load_dotenv()

# Azure credentials
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")

# Temporary storage paths
TEMP_DIR = "temp_videos"
AUDIO_OUTPUT_DIR = "extracted_audio"
TRANSLATED_AUDIO_DIR = "translated_audio"
FINAL_OUTPUT_DIR = "translated_videos"

# Ensure directories exist
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(AUDIO_OUTPUT_DIR, exist_ok=True)
os.makedirs(TRANSLATED_AUDIO_DIR, exist_ok=True)
os.makedirs(FINAL_OUTPUT_DIR, exist_ok=True)

def save_uploaded_file(uploaded_file):
    temp_file_path = os.path.join(TEMP_DIR, uploaded_file.name)
    with open(temp_file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return temp_file_path

def remove_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)

def clear_temp_folder(folder):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        remove_file(file_path)

# Available languages for translation
LANGUAGES = {
    'English': 'en',
    'Spanish': 'es',
    'French': 'fr',
    'German': 'de',
    'Hindi': 'hi'
}

# 1. Extract Audio from Video
def extract_audio_from_video(video_path):
    audio_output_path = os.path.join(AUDIO_OUTPUT_DIR, "extracted_audio.wav")
    video_clip = VideoFileClip(video_path)
    audio_clip = video_clip.audio
    audio_clip.write_audiofile(audio_output_path)
    return audio_output_path

# 2. Speech-to-Text Conversion
def speech_to_text(audio_path):
    speech_config = SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION)
    audio_input = AudioConfig(filename=audio_path)
    recognizer = SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)

    print("Converting speech to text...")
    result = recognizer.recognize_once()
    return result.text

# 3. Language Detection
def detect_language(text):
    translator = Translator()
    detection = translator.detect(text)
    if detection is None:
        raise ValueError("Language detection failed")
    return detection.lang

# 4. Translation Function
def translate_text(text, target_language="en"):
    translator = Translator()
    detected_language = detect_language(text)
    print(f"Detected Source Language: {detected_language}")
    translation = translator.translate(text, src=detected_language, dest=target_language)
    return translation.text, detected_language

# 5. Text-to-Speech Conversion
def text_to_speech(text, language_code="en-US"):
    output_audio_path = os.path.join(TRANSLATED_AUDIO_DIR, "translated_audio.wav")
    speech_config = SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION)
    audio_output = AudioConfig(filename=output_audio_path)
    synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=audio_output)

    print("Converting text to speech...")
    synthesizer.speak_text(text)
    return output_audio_path

# 6. Embedding Translated Audio Back into Video
def embed_audio_in_video(video_path):
    translated_audio_path = os.path.join(TRANSLATED_AUDIO_DIR, "translated_audio.wav")
    output_video_path = os.path.join(FINAL_OUTPUT_DIR, "translated_video.mp4")
    video_clip = VideoFileClip(video_path)
    audio_clip = AudioFileClip(translated_audio_path)
    final_video = video_clip.set_audio(audio_clip)
    final_video.write_videofile(output_video_path, codec="libx264", audio_codec="aac")
    return output_video_path

# Main function to handle the entire pipeline
def process_video(video_file_path, target_language="en"):
    extracted_audio = extract_audio_from_video(video_file_path)
    
    original_text = speech_to_text(extracted_audio)
    print(f"Extracted Text: {original_text}")

    translated_text, detected_lang = translate_text(original_text, target_language)
    print(f"Translated Text: {translated_text} (from {detected_lang} to {target_language})")

    translated_audio = text_to_speech(translated_text, language_code=target_language)

    final_video = embed_audio_in_video(video_file_path)

    return final_video

# Streamlit App Interface
st.title("Voice Vista.ai - Video Language Translator")

# 1. File Upload Section
uploaded_video = st.file_uploader("Upload a video file", type=["mp4", "mkv", "avi"])

# 2. Language Selection Section
st.subheader("Select the target language for translation:")
target_language = st.selectbox("Choose a language:", list(LANGUAGES.keys()))

if uploaded_video is not None:
    st.write(f"Uploaded file: {uploaded_video.name}")

    # Save uploaded file
    video_path = save_uploaded_file(uploaded_video)

    # Display the uploaded video
    st.video(uploaded_video)

    # Process the video when the user clicks the button
    if st.button("Translate Video"):
        target_language_code = LANGUAGES[target_language]
        translated_video_path = process_video(video_path, target_language=target_language_code)

        # Display the translated video and provide download option
        st.video(translated_video_path)
        st.download_button("Download Translated Video", data=open(translated_video_path, "rb"), file_name="translated_video.mp4")