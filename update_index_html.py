
import os

file_path = '/Users/kwanchai/Library/Mobile Documents/com~apple~CloudDocs/jarvis/jarvis-2/web/static/index.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Define the start marker for the recording block
start_marker = "// Recording with manual WAV conversion"
# Define the end marker or sufficient context to find the end
# Since the end is near the end of the script, we can look for the closing of stopRecording and subsequent helpers
# But it's safer to just identifying the line numbers from previous view_file
# Line 885 is start_marker.
# We want to replace everything from there down to line 1040 (floatTo16BitPCM end)

# Let's find the Exact String from the file content to be safe
try:
    start_index = content.index(start_marker)
    # We need to find where to stop. Let's separate the file into two parts.
    # The part BEFORE the recording logic, and the part AFTER (event listeners).
    
    # Looking for event listeners start
    end_marker = "// Event listeners"
    end_index = content.index(end_marker)
    
    new_code = """        // Recording using standard MediaRecorder (Stable Revert)
        async function startRecording() {
            try {
                if (isRecording) return;
                
                const stream = await navigator.mediaDevices.getUserMedia({ 
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true
                    }
                });
                
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

                mediaRecorder = new MediaRecorder(stream, { mimeType: mimeType });
                audioChunks = [];

                mediaRecorder.ondataavailable = event => {
                    if (event.data.size > 0) {
                        audioChunks.push(event.data);
                    }
                };

                mediaRecorder.onstop = () => {
                    const audioBlob = new Blob(audioChunks, { type: mimeType });
                    
                    stream.getTracks().forEach(track => track.stop());

                    if (audioBlob.size > 0) {
                        console.log(`Sending audio: ${audioBlob.size} bytes, ${audioBlob.type}`);
                        
                        if (ws && ws.readyState === WebSocket.OPEN) {
                            ws.send(audioBlob);
                        } else {
                            console.error("WebSocket not connected");
                            connect();
                        }
                    }
                    
                    processing.classList.remove('visible');
                    stopVisualizer();
                };

                mediaRecorder.start();
                isRecording = true;
                
                // Visualizer
                const AudioContext = window.AudioContext || window.webkitAudioContext;
                if (AudioContext) {
                    if (!audioContext) audioContext = new AudioContext();
                    if (audioContext.state === 'suspended') await audioContext.resume();
                    
                    analyser = audioContext.createAnalyser();
                    const source = audioContext.createMediaStreamSource(stream);
                    source.connect(analyser);
                    analyser.fftSize = 32;
                    startVisualizer(analyser);
                    window.currentSource = source;
                }

                currentStream = stream;

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

        function stopRecording() {
            if (mediaRecorder && isRecording) {
                mediaRecorder.stop();
                isRecording = false;

                if (window.currentSource) {
                    window.currentSource.disconnect();
                }

                micBtn.classList.remove('recording');
                micRing.classList.remove('recording');
                micLabel.classList.remove('recording');
                micLabel.textContent = 'กดค้างเพื่อพูด';
                visualizer.classList.remove('active');
                
                processing.classList.add('visible');
            }
        }

"""
    
    # Construct new content
    new_content = content[:start_index] + new_code + "\n        " + content[end_index:]
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
        
    print("Successfully updated index.html")

except ValueError as e:
    print(f"Error finding markers: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
