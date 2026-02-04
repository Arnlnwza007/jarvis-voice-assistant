"""
TTS - Text-to-Speech using Edge-TTS
Generates Thai speech for Jarvis responses
"""
import asyncio
import tempfile
import logging
import os
import discord
import edge_tts
from config import TTS_VOICE, TTS_ENABLED

logger = logging.getLogger(__name__)


async def generate_speech(text: str) -> str:
    """Generate speech audio file from text."""
    try:
        communicate = edge_tts.Communicate(text, TTS_VOICE)
        
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            temp_path = f.name
            
        await communicate.save(temp_path)
        return temp_path
        
    except Exception as e:
        logger.error(f"TTS generation error: {e}")
        return None


async def speak(text: str, voice_client: discord.VoiceClient):
    """Speak text through Discord voice client."""
    if not TTS_ENABLED:
        return
        
    if not voice_client or not voice_client.is_connected():
        logger.warning("No voice client for TTS")
        return
        
    try:
        # Generate audio
        audio_path = await generate_speech(text)
        if not audio_path:
            return
        
        logger.info(f"🗣️ Speaking: {text}")
        
        # Stop any current audio
        if voice_client.is_playing():
            voice_client.stop()
            await asyncio.sleep(0.3)
        
        # Use event to wait for completion
        finished = asyncio.Event()
        loop = asyncio.get_running_loop()
        
        def after_play(error):
            if error:
                logger.error(f"TTS playback error: {error}")
            # Use stored loop reference
            loop.call_soon_threadsafe(finished.set)
        
        # Play TTS
        source = discord.FFmpegPCMAudio(audio_path)
        voice_client.play(source, after=after_play)
        
        # Wait for TTS to finish (max 10 seconds)
        try:
            await asyncio.wait_for(finished.wait(), timeout=10.0)
        except asyncio.TimeoutError:
            logger.warning("TTS timeout, stopping")
            if voice_client.is_playing():
                voice_client.stop()
        
        # Small delay before next audio
        await asyncio.sleep(0.5)
            
        # Cleanup
        try:
            os.unlink(audio_path)
        except:
            pass
        
    except Exception as e:
        logger.error(f"TTS speak error: {e}")
