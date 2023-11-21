import wave
import sys
import pyaudio
import wikipediaapi
import text2speech
import speech2text
from chatbot import ChatGPT

def record_microphone(seconds: int, filename: str):
    """Records (speech) from the microphone.

    Args:
        seconds (int): number of seconds of the recording
        filename (str): filename where the recording gets saved
    """
    
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1 if sys.platform == 'darwin' else 2
    RATE = 44100
    RECORD_SECONDS = seconds

    with wave.open(filename, 'wb') as wf:
        p = pyaudio.PyAudio()
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)

        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True)

        print('Recording...')
        for _ in range(0, RATE // CHUNK * RECORD_SECONDS):
            wf.writeframes(stream.read(CHUNK, exception_on_overflow = False))
        print('Done')

        stream.close()
        p.terminate()

if __name__ == "__main__":
    #record_microphone(seconds=5, filename='recording.wav')
    #text = speech_to_text('recording.wav')
    response = ChatGPT().question('Beschreibe das Bild der Mona Lisa')
    #wiki_wiki = wikipediaapi.Wikipedia('MyProjectName (merlin@example.com)', 'en')
    #page_py = wiki_wiki.page('Python_(programming_language)')
    #text2speech.text_to_speech_openai(response, 'mona_lisa_openai.wav')
    text = speech2text.speech_to_text_openai('mona_lisa_openai.wav')
    print(text)