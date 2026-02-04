# app/services/speech_service.py
import speech_recognition as sr
import tempfile

def speech_to_text(audio_bytes):
    recognizer = sr.Recognizer()

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
        tmp.write(audio_bytes)
        tmp.flush()

        with sr.AudioFile(tmp.name) as source:
            audio = recognizer.record(source)

    try:
        return recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        return ""
    except sr.RequestError:
        return ""
