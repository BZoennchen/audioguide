# Audioguide

This is a minimalistic example of an *audioguide*.
At the momment it is possible to

1. make a recording from your local microphone input
2. transform **text-to-speech** using either [gTTS](https://pypi.org/project/gTTS/) (Google Text-to-Speech) or [openai](https://pypi.org/project/openai/)
3. transform **speech-to-text** using [openai](https://pypi.org/project/openai/) (Whisper)

## How to use OpenAI API

To use the OpenAI API you need an API-Key in your **environment variable** and you need money :/.
Go to the [OpenAI webpage](https://openai.com/), login and generate your API-Key.
Go to API.
Then go to Quickstart.
**Step 2: Setup your API key** (Windows / Mac) and do those steps.

## Run the App

```
python -m flask --app app run --debug 
```