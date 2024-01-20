// set up basic variables for app

const record = document.querySelector('.record');
const stop = document.querySelector('.stop');
//const soundClips = document.querySelector('.sound-clips');
const canvas = document.querySelector('.visualizer');
const mainSection = document.querySelector('.main-controls');

// disable stop button while not recording

stop.disabled = true;

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

    record.onclick = function() {
      mediaRecorder.start();
      console.log(mediaRecorder.state);
      console.log("recorder started");
      record.style.background = "red";

      stop.disabled = false;
      record.disabled = true;
    }

    stop.onclick = function() {
      mediaRecorder.stop();
      console.log(mediaRecorder.state);
      console.log("recorder stopped");
      record.style.background = "";
      record.style.color = "";
      // mediaRecorder.requestData();

      stop.disabled = true;
      record.disabled = false;
    }

    mediaRecorder.onstop = function(e) {
      console.log("data available after MediaRecorder.stop() called.");      
      const blob = new Blob(chunks, { 'type': 'audio/webm' });
      chunks = [];
      console.log("recorder stopped");

      sendAudioToServer(blob)
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

function sendAudioToServer(audioBlob) {
  const formData = new FormData();
  //formData.append("audio", audioBlob);
  formData.append('audio', audioBlob, 'audioToSave.webm')
  fetch('/upload_audio', {
    method: 'POST',
    body: formData
  }).then(response => {
    // Handle the response. Possibly the server returns a unique ID for the audio processing task
    let text = response.text();
    console.log('reponse: ' + text);
    return text;
  }).then(request_file => {
    // Use this task ID to listen for server-sent events
    console.log('request_file: ' + request_file);
    let json = JSON.parse(request_file);
    let filename = json.request_file
    let id = json.id
    listen_for_server_text_response(filename, id);
    
  }).catch(error => {
    console.error('Error:', error);
  });
}

function listen_for_server_text_response(filename, id) {
  // Replace '/ask_question' with your SSE endpoint
  // You can pass the task ID as a query parameter if needed
  const eventSource = new EventSource(`/ask_question?filename=${filename}&id=${id}`);
  let max_len = 200;
  let current_aggregate = ""
  let count = 0;
  let playing = false;
  let audios = [];
  eventSource.onmessage = function (event) {
    console.log('Message:', event.data);
    console.log("response" + id);
    let li_response = document.getElementById("response"+id);
    li_response.innerHTML += event.data;
    current_aggregate += event.data;
    
    if (current_aggregate.length >= max_len) {
      audios.push(new Audio(`/text_to_speech?filename=${filename + count.toString()}&text=${encodeURIComponent(current_aggregate)}`));
      current_aggregate = "";
    }
    
    if (!playing && audios.length > 0) {
      playing = true;
      let audio = audios.shift();
      audio.play();
      audio.addEventListener("ended", audio_ended);

      function audio_ended() { 
        if (audios.length > 0) {
          audio = audios.shift();
          audio.play();
          audio.addEventListener("ended", audio_ended);
        }
      }

      /*audio.addEventListener("ended", function () {
        audio = new Audio(`/text_to_speech?filename=${filename + count.toString()}&text=${encodeURIComponent(current_aggregate)}`);
        audio.play();
      });*/
    }
  };

  eventSource.addEventListener('customEvent', function (event) {
    // Handle custom named events if your server sends them
    console.log('customEvent:', event.data);
  });

  eventSource.onerror = function () {
    console.log('Error occurred.');
    eventSource.close();
  };
}

function visualize(stream) {
  if(!audioCtx) {
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


    for(let i = 0; i < bufferLength; i++) {

      let v = dataArray[i] / 128.0;
      let y = v * HEIGHT/2;

      if(i === 0) {
        canvasCtx.moveTo(x, y);
      } else {
        canvasCtx.lineTo(x, y);
      }

      x += sliceWidth;
    }

    canvasCtx.lineTo(canvas.width, canvas.height/2);
    canvasCtx.stroke();

  }
}

/*function playChunk() {
  document.getElementById('historyList').lastElementChild.querySelector('audio');
  console.log(document.getElementById('historyList').lastElementChild);

  if (playing != true && chunks.length > 0) {
    playing = true;
    audio = new Audio('/text_to_speech/filename?text=' + encodeURIComponent(chunks.shift()));
    audio.play();
    audio.addEventListener("ended", function () {
      playing = false;
    });
  }
}


var playTimer;
playTimer = setInterval(function () {
  // check the response for new data
  playChunk();
}, 1000);
*/

window.onresize = function() {
  canvas.width = mainSection.offsetWidth;
}

window.onresize();

