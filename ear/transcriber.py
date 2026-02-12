"""
Transcriber - Speech-to-Text using Whisper
Uses openai-whisper (stable) for voice transcription
"""
import os
import logging
import tempfile
import subprocess

# Set up ffmpeg path BEFORE importing whisper
from config import WHISPER_MODEL, WHISPER_DEVICE, FFMPEG_PATH, BASE_DIR

# Ensure ffmpeg is in PATH
ffmpeg_dir = os.path.dirname(os.path.abspath(FFMPEG_PATH))
if ffmpeg_dir:
    os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
# Also add project directory (for bundled ffmpeg binary)
os.environ["PATH"] = str(BASE_DIR) + os.pathsep + os.environ.get("PATH", "")

logger = logging.getLogger(__name__)

_model = None


def get_model():
    """Load Whisper model (openai-whisper)."""
    global _model
    if _model is None:
        import whisper
        
        model_name = WHISPER_MODEL
        logger.info(f"Loading Whisper model: {model_name} (device: {WHISPER_DEVICE})")
        _model = whisper.load_model(model_name)
        logger.info("✅ Whisper model loaded")
    return _model


class Transcriber:
    """Speech-to-Text transcriber using Whisper."""
    
    def __init__(self):
        self.model = None
        
    def load(self):
        """Load the model."""
        self.model = get_model()
        
    def transcribe(self, audio_path: str, language: str = "th") -> str:
        """Transcribe audio file to text."""
        if self.model is None:
            self.load()
            
        wav_path = None
        try:
            logger.info(f"Transcribing: {audio_path} (Language: {language})")
            
            # Convert to 16kHz WAV first (fixes webm issues)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                wav_path = f.name
                
            # Convert using ffmpeg binary
            # cmd: ffmpeg -y -i input.webm -ar 16000 -ac 1 -c:a pcm_s16le output.wav
            cmd = [
                FFMPEG_PATH, '-y',
                '-v', 'error',       # Less verbose
                '-i', audio_path,
                '-ar', '16000',      # Sample rate 16k
                '-ac', '1',          # Mono
                '-c:a', 'pcm_s16le', # PCM 16-bit
                wav_path
            ]
            
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            
            # Force decoding options for Thai
            import whisper
            options = whisper.DecodingOptions(language=language, without_timestamps=True, fp16=False)
            
            # Load from converted WAV
            audio = whisper.load_audio(wav_path)
            audio = whisper.pad_or_trim(audio)
            
            # Get n_mels from model dimensions
            n_mels = self.model.dims.n_mels
            mel = whisper.log_mel_spectrogram(audio, n_mels=n_mels).to(self.model.device)
            
            result = self.model.decode(mel, options)
            text = result.text.strip()
            
            logger.info(f"Transcribed: {text}")
            return text
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg conversion failed: {e.stderr.decode() if e.stderr else 'Unknown error'}")
            return ""
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""
        finally:
            if wav_path and os.path.exists(wav_path):
                try:
                    os.unlink(wav_path)
                except:
                    pass


# Global instance
transcriber = Transcriber()
