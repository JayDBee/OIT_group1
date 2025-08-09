// static/client.js
const localVid = document.getElementById("local");
const remoteVid = document.getElementById("remote");
const startBtn = document.getElementById("startBtn");
const answerBtn = document.getElementById("answerBtn");

const pcConfig = {
  iceServers: [
    { urls: "stun:stun.l.google.com:19302" } // public STUN
  ]
};

let pc;
let ws;
let localStream;

async function initMedia() {
  localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
  localVid.srcObject = localStream;
}

function connectWebSocket() {
  ws = new WebSocket((location.protocol === "https:" ? "wss://" : "ws://") + location.host + "/ws");
  ws.onopen = () => console.log("WS open");
  ws.onmessage = async (evt) => {
    const msg = JSON.parse(evt.data);
    console.log("WS msg:", msg);

    if (msg.type === "waiting") {
      console.log("Waiting for peer...");
    } else if (msg.type === "paired") {
      console.log("Paired with", msg.peer);
    } else if (msg.type === "offer") {
      await handleOffer(msg.offer);
    } else if (msg.type === "answer") {
      await pc.setRemoteDescription(msg.answer);
    } else if (msg.type === "ice") {
      try {
        await pc.addIceCandidate(msg.candidate);
      } catch (e) { console.warn("Add ICE failed:", e); }
    } else if (msg.type === "peer-disconnected") {
      console.log("Peer disconnected");
      if (remoteVid.srcObject) {
        remoteVid.srcObject.getTracks().forEach(t => t.stop());
        remoteVid.srcObject = null;
      }
    }
  };
}

function sendSignal(obj) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(obj));
  } else {
    console.warn("WebSocket not open");
  }
}

function createPeerConnection() {
  pc = new RTCPeerConnection(pcConfig);

  // send any ICE candidates to the other peer
  pc.onicecandidate = (event) => {
    if (event.candidate) {
      sendSignal({ type: "ice", candidate: event.candidate });
    }
  };

  // show remote stream
  pc.ontrack = (event) => {
    // multiple tracks might be present; set the first stream
    remoteVid.srcObject = event.streams[0];
  };

  // add local tracks
  if (localStream) {
    for (const t of localStream.getTracks()) {
      pc.addTrack(t, localStream);
    }
  }
}

async function doOffer() {
  createPeerConnection();

  const offer = await pc.createOffer();
  await pc.setLocalDescription(offer);

  sendSignal({ type: "offer", offer: pc.localDescription });
}

async function handleOffer(offer) {
  createPeerConnection();
  await pc.setRemoteDescription(offer);
  const answer = await pc.createAnswer();
  await pc.setLocalDescription(answer);
  sendSignal({ type: "answer", answer: pc.localDescription });
}

// button handlers
if (startBtn) {
  startBtn.onclick = async () => {
    await initMedia();
    connectWebSocket();
    // Wait a bit for ws to pair, then create offer
    // you can also react to "paired" message
    setTimeout(() => doOffer(), 500);
  };
}

if (answerBtn) {
  answerBtn.onclick = async () => {
    await initMedia();
    connectWebSocket();
    // wait: onmessage will handle incoming offer and answer automatically
  };
}
