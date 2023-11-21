import gtts
from openai import OpenAI

def text_to_speech(text: str, filename='tts.wav', language='en'):
    tts = gtts.gTTS(text=text, lang=language)
    tts.save(filename)

def text_to_speech_openai(text: str, filename):
    client = OpenAI()
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text
    )
    response.stream_to_file(filename)