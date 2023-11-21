from openai import OpenAI
import speech_recognition as sr

def speech_to_text(audifile: str):
    recognizer = sr.Recognizer()
    text = ''
    with sr.AudioFile(audifile) as source:
        audio = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio)
            print("Speech recognizion: " + text)
        except sr.UnknownValueError:
            print("Could not understand audio")
        except sr.RequestError as e:
            print("Error; {0}".format(e))
    return text

def speech_to_text_openai(audiofile):
    client = OpenAI()

    audio_file= open(audiofile, "rb")
    transcript = client.audio.transcriptions.create(
        model="whisper-1", 
        file=audio_file,
        response_format="text"
    )
    
    return transcript