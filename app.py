import logging
from flask import Flask, Response, render_template, jsonify, request, send_from_directory, url_for, redirect, stream_with_context, send_file
from turbo_flask import Turbo
from audioguide import ChatGPT
import speech2text
import text2speech
import time
import os

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
        age = request.form.get('age')
        interests = request.form.get('interestSelect')
        frequency = request.form.get('frequenceSelect')
        
        config['age'] = age
        config['interests'] = interests
        config['frequency'] = frequency
        app.logger.debug(f'config: {config}')
        
    return render_template('questionpage.html', history=history)

@app.route('/ask_question')
def process_recording():
    id = int(request.args.get('id'))
    entry = history[id]
    app.logger.debug(f'/ask_question: {id}')
    user_prompt = entry['user_prompt']
    
    # 3. User request to chatbot answer        
    gpt = ChatGPT(age=config['age'], interests=config['interests'], frequency=config['frequency'])
    def generate():
        gpt_response = ""
        acc = ""
        for chunk in gpt.question_streamed(user_prompt):
            if chunk != None:
                gpt_response += chunk
                acc += chunk
                entry['response'] = gpt_response
                app.logger.debug(chunk)
                yield f'data: {chunk}\n\n'
        yield "data: END_OF_STREAM\n\n"
        
        app.logger.debug('End of generation')
        response_file =  f'response-{time.strftime("%Y%m%d-%H%M%S")}.mp3'
        
        entry['response_audio'] = response_file
        text2speech.text_to_speech_openai(gpt_response, f'audio/responses/{response_file}')
        app.logger.debug('Resonsed saved')
    return Response(generate(), mimetype='text/event-stream') 

@app.route('/upload_audio', methods=['POST'])
def upload_user_audio_request():
    if 'audio' in request.files:
       # 1. Audio of the user to audio file
        timestr = time.strftime("%Y%m%d-%H%M%S")
        request_file = f'request-{timestr}.mp3'
        audio_file = request.files['audio']
        audio_file.save(f'audio/requests/{request_file}')
        audio_file.flush()
        audio_file.close()
        user_prompt = speech2text.speech_to_text_openai(f'audio/requests/{request_file}')
        
        id = len(history)
        entry = {'id': id, 'user_prompt': user_prompt, 'response': "", 'user_audio': request_file, 'response_audio': None}
        entry.update(config)
        history.append(entry)
        turbo.push(turbo.replace(render_template('history.html', history=history), f'responseHistory'))
        # You can return a unique task ID if you have a background processing task
        
        return jsonify({'request_file': request_file, 'id': id}), 200
    else:
        return jsonify({'error': 'No audio file found'}), 400    

@app.route('/audio/responses/<path:filename>')
def download_file(filename):
    """
        Sends back an audio file.
    """    
    return send_from_directory('audio/responses/', filename)

@app.route('/text_to_text')
def text_to_text():
    """Streams the text based on a user prompted contained in the request back as response.

    Returns:
        the streamed text
    """
    
    user_prompt = request.args.get('user_prompt')
    gpt = ChatGPT(*config)
    
    def generate():
        for chunk in gpt.question_streamed(user_prompt):
            #app.logger.debug(chunk)
            if chunk != None:
                yield chunk
    
    return app.response_class(stream_with_context(generate()), mimetype='text/event-stream') 
    

@app.route('/speech_to_text', methods=['POST'])
def speech_to_text():
    """Returns the plain text generated out of speech as response.
 
    Returns:
        plain text
    """
    
    timestr = time.strftime("%Y%m%d-%H%M%S")
    request_file = f'request-{timestr}.webm'
    audio_file = request.files['audio']
    audio_file.save(f'audio/requests/{request_file}')
    audio_file.flush()
    audio_file.close()
    response = speech2text.speech_to_text_openai(f'audio/response/{request_file}')
    return response

@app.route('/text_to_speech')
def text_to_speech():
    """Streams audio (speech), generated of a text contained in the request, into a file.
       The file is send back as response.

    Returns:
        the streamed file
    """
    
    filename = request.args.get('filename')
    text = request.args.get('text')
    text2speech.text_to_speech_openai(text, f'audio/responses/{filename}')
    return send_file(f'audio/responses/{filename}', mimetype='audio/mp3')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    app.run(debug=True)

