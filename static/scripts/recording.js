// set up basic variables for app

const record_button = document.getElementById('recordingButton');
//const stop = document.querySelector('.stop');
//const soundClips = document.querySelector('.sound-clips');
const canvas = document.getElementById('speechVisualizer');
const mainSection = document.getElementById('main-controls');
let recording_started = false;

// visualiser setup - create web audio api context and canvas

let audioCtx;
const canvasCtx = canvas.getContext("2d");

//main block for doing the audio recording

if (navigator.mediaDevices.getUserMedia) {
  console.log('getUserMedia supported.');

  const constraints = { audio: true };
  let chunks = [];

  let onSuccess = function(stream) {
    const mediaRecorder = new MediaRecorder(stream);

    visualize(stream);

    record_button.onclick = function () {
      if (!recording_started) {
        mediaRecorder.start();
        recording_started = true;
        console.log(mediaRecorder.state);
        console.log("recorder started");
       // record_button.style.background = "#e74c3c";
       // record_button.style.color = "white";
        record_button.innerText = "Aufnahme beenden"; // to do internationalization
      } else { 
        mediaRecorder.stop();
        recording_started = false;
        console.log(mediaRecorder.state);
        console.log("recorder stopped");
       // record_button.style.background = "#B7E5B4;";
       // record_button.style.color = "black";
        record_button.innerText = "Aufnahme starten"; // to do internationalization
        record_button.disabled = true;
      }
    }

    mediaRecorder.onstop = function(e) {
      console.log("data available after MediaRecorder.stop() called.");      
      const blob = new Blob(chunks, { 'type': 'audio/webm' });
      chunks = [];
      console.log("recorder stopped");
      sendUserAudioToServer(blob);
    }

    mediaRecorder.ondataavailable = function(e) {
      chunks.push(e.data);
    }
  }

  let onError = function(err) {
    console.log('The following error occured: ' + err);
  }

  navigator.mediaDevices.getUserMedia(constraints).then(onSuccess, onError);

} else {
   console.log('getUserMedia not supported on your browser!');
}

function visualize(stream) {
  if (!audioCtx) {
    audioCtx = new AudioContext();
  }

  const source = audioCtx.createMediaStreamSource(stream);

  const analyser = audioCtx.createAnalyser();
  analyser.fftSize = 2048;
  const bufferLength = analyser.frequencyBinCount;
  const dataArray = new Uint8Array(bufferLength);

  source.connect(analyser);
  //analyser.connect(audioCtx.destination);

  draw()

  function draw() {
    const WIDTH = canvas.width
    const HEIGHT = canvas.height;

    requestAnimationFrame(draw);

    analyser.getByteTimeDomainData(dataArray);

    canvasCtx.fillStyle = 'rgb(200, 200, 200)';
    canvasCtx.fillRect(0, 0, WIDTH, HEIGHT);

    canvasCtx.lineWidth = 2;
    canvasCtx.strokeStyle = 'rgb(0, 0, 0)';

    canvasCtx.beginPath();

    let sliceWidth = WIDTH * 1.0 / bufferLength;
    let x = 0;


    for (let i = 0; i < bufferLength; i++) {

      let v = dataArray[i] / 128.0;
      let y = v * HEIGHT / 2;

      if (i === 0) {
        canvasCtx.moveTo(x, y);
      } else {
        canvasCtx.lineTo(x, y);
      }

      x += sliceWidth;
    }

    canvasCtx.lineTo(canvas.width, canvas.height / 2);
    canvasCtx.stroke();

  }
}

window.onresize = function () {
  canvas.width = mainSection.offsetWidth;
}

window.onresize();


// The following code implements the client server communication for one user (audio) request.
// The Server translates the audio to text and calls openAI's ChatGPT
// The answer from ChatGPT is streamed back to the client which fills in the text chunks.
// Futhermore it gathers chunks until a certain aggregate is available.
// Then it ask the server to translate the aggregate into audio
// The audio is queued and if the first audio arrives, the client starts playing

/**
 * Sends the user audio prompt to the server
 * 
 * @param {Blob} audioBlob - The user audio prompt
 */
function sendUserAudioToServer(audioBlob) {
  const formData = new FormData();
  formData.append('audio', audioBlob, 'audioToSave.webm')
  fetch('/upload_audio', {
    method: 'POST',
    body: formData
  }).then(response => {
    let text = response.text();
    console.log('reponse: ' + text);
    return text;
  }).then(request_file => {
    console.log('request_file: ' + request_file);
    let json = JSON.parse(request_file);
    let id = json.id
    textChunksToPlayedAudio(id);
    
  }).catch(error => {
    console.error('Error:', error);
  });
}

/**
 * This function does all the translation from chunks of text (sent by the server) to played audio.
 * 
 * @param {Int} id - number of the entry in the history starting at 0.
 */
function textChunksToPlayedAudio(id) {
  const eventSource = new EventSource(`/ask_question?id=${id}`);
  let maxLen = 300;
  let minLen = 120;
  let currentAggregate = ""
  let count = 0;
  let order = 0;
  let playing = false;
  
  let audioContext = new(window.AudioContext || window.webkitAudioContext)();
  let audioFiles = [];

  function loadAndPlayAudio(url) {
    // load the result from the server
    return fetch(url)
      .then(response => response.arrayBuffer())
      .then(buffer => audioContext.decodeAudioData(buffer))
      .then(decodedBuffer => {
        if (!playing) { 
          var source = audioContext.createBufferSource();
          source.buffer = decodedBuffer;
          source.connect(audioContext.destination);

          source.onended = function () {
            playing = false;
            
            // no more text chunks coming in and the last audioFile was played => we are done!
            if (eventSource.readyState == eventSource.CLOSED && order == audioFiles.length-1) {
              audioFiles = [];
              location.reload();
            } else {
              playNextAudio();
            }
          };

          source.start();
          playing = true;
        }
      });
  }

  function playNextAudio() {
    if (audioFiles.length > order && audioFiles[order] != null) {
      let nextAudioUrl = audioFiles[order];
      console.log(`play next generated speech chunk ${audioFiles}`);
      order += 1;
      loadAndPlayAudio(nextAudioUrl);
    }
  }

  function addAudioToQueue(url) {
    console.log('generate speech chunk: ' + url);
    audioFiles.push(null);
    let index = audioFiles.length - 1;

    // tell the server to generate the audio
    fetch(url)
      .then(response => response.blob())
      .then(blob => {
        let url = URL.createObjectURL(blob);
        audioFiles[index] = url;
        if (audioContext.state === 'suspended') {
          audioContext.resume(); // Resume the audio context if needed
        }
        if (!playing) {
          playNextAudio();
        }
      });
  }

  eventSource.onmessage = function (event) {
    if (event.data === "END_OF_STREAM") {
      console.log("end of chunk stream");
      if (currentAggregate.length > 0) {
        addAudioToQueue(`/text_to_speech?filename=entry${id}-chunk-${count.toString()}.mp3&text=${encodeURIComponent(currentAggregate)}`);
      }
      eventSource.close();
    }
    else { 
      let li_response = document.getElementById("response" + id);
      let div_response = li_response.getElementsByTagName('div')[0];
      div_response.innerHTML += event.data;
      currentAggregate += event.data;

      if (/[.!?,:;]$/.test(event.data) && currentAggregate.length >= minLen || currentAggregate.length >= maxLen) {
        addAudioToQueue(`/text_to_speech?filename=entry${id}-chunk-${count.toString()}.mp3&text=${encodeURIComponent(currentAggregate)}`);
        count += 1;
        currentAggregate = " ";
      }
    }
  };

  eventSource.addEventListener('customEvent', function (event) {
    // Handle custom named events if your server sends them
    console.log('customEvent:', event.data);
  });

  eventSource.onerror = function () {
    console.error("EventSource failed:", error);
    eventSource.close();
  };
}

function expand() {
  const isExpanded = this.classList.contains('expanded');
  console.log('test');
  if (isExpanded) {
    this.classList.remove("expanded");
    this.classList.add("shrunk");
  } else {
    this.classList.add("expanded");
    this.classList.remove("shrunk");
  }
};