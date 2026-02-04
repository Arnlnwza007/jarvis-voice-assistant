"""
Transcriber - Speech-to-Text using Whisper
Uses openai-whisper (stable) with optional faster-whisper support
"""
import os
import logging

# Add project directory to PATH for ffmpeg
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ["PATH"] = project_dir + os.pathsep + os.environ.get("PATH", "")

from config import WHISPER_MODEL, WHISPER_DEVICE

logger = logging.getLogger(__name__)

_model = None


def get_model():
    """Load Whisper model (openai-whisper)."""
    global _model
    if _model is None:
        import whisper
        
        # Map model names
        model_name = WHISPER_MODEL
        if "turbo" in model_name:
            model_name = "large-v3"  # turbo is only in faster-whisper
            
        logger.info(f"Loading Whisper model: {model_name}")
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
            
        try:
            result = self.model.transcribe(audio_path, language=language)
            text = result["text"].strip()
            logger.info(f"Transcribed: {text}")
            return text
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""


# Global instance
transcriber = Transcriber()
