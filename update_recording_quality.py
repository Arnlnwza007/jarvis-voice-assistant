
import os

file_path = '/Users/kwanchai/Library/Mobile Documents/com~apple~CloudDocs/jarvis/jarvis-2/web/static/index.html'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_recording_code = """        // Recording using standard MediaRecorder with High Quality Constraints
        async function startRecording() {
            try {
                if (isRecording) return;
                
                // Get Stream with High Quality Audio
                const stream = await navigator.mediaDevices.getUserMedia({ 
                    audio: {
                        channelCount: 1,
                        sampleRate: { ideal: 48000 },
                        sampleSize: 16,
                        echoCancellation: false,
                        noiseSuppression: false,
                        autoGainControl: true
                    }
                });
                
                // Determine supported mime type
                let mimeType = 'audio/webm';
                const types = [
                    'audio/webm;codecs=opus',
                    'audio/webm',
                    'audio/ogg;codecs=opus',
                    'audio/mp4',
                    'audio/aac'
                ];
                
                for (const type of types) {
                    if (MediaRecorder.isTypeSupported(type)) {
                        mimeType = type;
                        break;
                    }
                }
                
                console.log("Using MIME type:", mimeType);

                // High Bitrate Recording
                mediaRecorder = new MediaRecorder(stream, { 
                    mimeType: mimeType,
                    audioBitsPerSecond: 128000 
                });
                
                audioChunks = [];

                mediaRecorder.ondataavailable = event => {
                    if (event.data.size > 0) {
                        audioChunks.push(event.data);
                    }
                };

                mediaRecorder.onstop = () => {
                    const audioBlob = new Blob(audioChunks, { type: mimeType });
                    
                    // Cleanup tracks
                    stream.getTracks().forEach(track => track.stop());

                    // Send to server
                    if (audioBlob.size > 0) {
                        console.log(`Sending audio: ${audioBlob.size} bytes, ${audioBlob.type}`);
                        
                        if (ws && ws.readyState === WebSocket.OPEN) {
                            ws.send(audioBlob);
                        } else {
                            console.error("WebSocket not connected");
                            connect();
                        }
                    } else {
                        console.warn("Audio too short");
                    }
                    
                    processing.classList.remove('visible');
                    stopVisualizer();
                };

                mediaRecorder.start();
                isRecording = true;
                
                // Visualizer (Optional - Fails quietly)
                try {
                    const AudioContext = window.AudioContext || window.webkitAudioContext;
                    if (AudioContext) {
                        // Re-use or create context
                        if (!audioContext) audioContext = new AudioContext();
                        else if (audioContext.state === 'closed') audioContext = new AudioContext();
                        
                        if (audioContext.state === 'suspended') await audioContext.resume();
                        
                        analyser = audioContext.createAnalyser();
                        const source = audioContext.createMediaStreamSource(stream);
                        source.connect(analyser);
                        analyser.fftSize = 32;
                        startVisualizer(analyser);
                        window.currentSource = source;
                    }
                } catch (e) {
                    console.warn("Visualizer failed to initialize (Audio only mode):", e);
                }

                currentStream = stream; // Store for cleanup

                // UI Updates
                micBtn.classList.add('recording');
                micRing.classList.add('recording');
                micLabel.classList.add('recording');
                micLabel.textContent = 'กำลังฟัง...';
                visualizer.classList.add('active');

            } catch (err) {
                console.error('Recording Error:', err);
                addMessage('error', '❌ ไม่สามารถเข้าถึงไมโครโฟน: ' + err.message);
                isRecording = false;
            }
        }
"""

start_idx = -1
end_idx = -1

# Find boundaries
for i, line in enumerate(lines):
    if "async function startRecording() {" in line:
        # Move up to catch the comment if possible, but safe to replace from function def
        if i > 0 and "Recording using standard MediaRecorder" in lines[i-1]:
             start_idx = i - 1
        else:
             start_idx = i
        break

for i, line in enumerate(lines):
    if "function stopRecording() {" in line:
        end_idx = i
        break

if start_idx != -1 and end_idx != -1:
    new_content = "".join(lines[:start_idx]) + new_recording_code + "\n        " + "".join(lines[end_idx:])
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Successfully updated startRecording logic")
else:
    print(f"Could not find start/end markers. Start: {start_idx}, End: {end_idx}")

