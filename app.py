import logging
from flask import Flask, Response, render_template, request, send_from_directory, stream_with_context, send_file
from turbo_flask import Turbo
from audioguide import ChatGPT
import speech2text
import text2speech
import time

app = Flask(__name__)
turbo = Turbo(app)

# Annahme: Verlaufsdaten werden als Liste gespeichert
history = []
config = {'age': '', 'interests': '', 'frequency': ''}
# Konfiguration des Logging-Moduls
#logging.basicConfig(filename='app.log', level=logging.DEBUG)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/questionpage', methods=['POST', 'GET'])
def question_page():
    if request.method == 'POST':
        # Hier werden die Auswahlmöglichkeiten aus dem Popup verarbeitet
        age = request.form.get('ageInput')
        interests = request.form.get('interestSelect')
        frequency = request.form.get('frequenceSelect')
        
        config['age'] = age
        config['interests'] = interests
        config['frequency'] = frequency
        
    return render_template('questionpage.html', history=history)

@app.route('/ask_question', methods=['POST'])
def process_recording():
    # 1. Audio of the user to audio file
    timestr = time.strftime("%Y%m%d-%H%M%S")
    request_file = f'request-{timestr}.webm'
    audio_file = request.files['audio']
    audio_file.save(f'audio/requests/{request_file}')
    audio_file.flush()
    audio_file.close()
    
    # 2. Audio file to text, i.e. user request
    user_prompt = speech2text.speech_to_text_openai(f'audio/requests/{request_file}')
    
    # 3. User request to chatbot answer
    entry = {'id': len(history), 'user_prompt': user_prompt, 'response': "", 'user_audio': request_file, 'response_audio': None}
    entry.update(config)
    history.append(entry)
    turbo.push(turbo.replace(render_template('history.html', history=history), f'responseHistory'))
    if "stop" in str(user_prompt).lower():
        entry['response'] = "Recording stopped."
    else:
        gpt = ChatGPT(*config)
        gpt_response = ""
        for chunk in gpt.question_streamed(user_prompt):
            if chunk != None:
                gpt_response += chunk
                entry['response'] = gpt_response
                turbo.push(turbo.replace(render_template('botresponse.html', entry=entry), f'response{entry['id']}'))
    
    
    # 4. Chatbot answer to speech, TODO: this takes a lot of time!
    response_file =  f'response-{time.strftime("%Y%m%d-%H%M%S")}.mp3'
    text2speech.text_to_speech_openai(gpt_response, f'audio/responses/{response_file}')
    entry['response_audio'] = response_file

    turbo.push(turbo.replace(render_template('history.html', history=history), f'responseHistory'))
    return "Audio received, saved, and processed", 200
    

@app.route('/audio/responses/<path:filename>')
def download_file(filename):
    return send_from_directory('audio/responses/', filename)

@app.route('/text_to_text')
def text_to_text():
    user_prompt = request.args.get('user_prompt')
    gpt = ChatGPT(*config)
    
    def generate():
        for chunk in gpt.question_streamed(user_prompt):
            app.logger.debug(chunk)
            if chunk != None:
                yield chunk
    
    return app.response_class(stream_with_context(generate()), mimetype='text/event-stream') 
    

@app.route('/speech_to_text', methods=['POST'])
def speech_to_text():
    timestr = time.strftime("%Y%m%d-%H%M%S")
    request_file = f'request-{timestr}.webm'
    audio_file = request.files['audio']
    audio_file.save(f'audio/requests/{request_file}')
    audio_file.flush()
    audio_file.close()
    response = speech2text.speech_to_text_openai(f'audio/requests/{request_file}')
    return response

@app.route('/text_to_speech/<path:filename>')
def text_to_speech(filename):
    text = request.args.get('text')
    text2speech.text_to_speech_openai(text, f'audio/responses/{filename}')
    return send_file(f'audio/responses/{filename}', mimetype='audio/mp3')

if __name__ == '__main__':
    app.run(debug=True)

