#!/usr/bin/env python3
"""
Jarvis - Voice Assistant
========================

Architecture:
  🌐 Web    : Push-to-talk → Whisper STT → Ollama LLM
  🤖 Discord: TTS output + Music playback

Usage:
  python app.py
"""
import asyncio
import logging
from config import DISCORD_TOKEN, WEB_PORT

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('jarvis.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


def print_banner():
    print(f"""
    ╔═══════════════════════════════════════════════════════════╗
    ║              🤖 JARVIS Voice Assistant                    ║
    ╠═══════════════════════════════════════════════════════════╣
    ║  🌐 Web   : http://localhost:{WEB_PORT} (Push-to-talk)         ║
    ║  👂 Ear   : Faster-Whisper STT                            ║
    ║  🧠 Brain : Ollama + Typhoon 2                            ║
    ║  🗣️ Mouth : Edge-TTS (Thai)                               ║
    ║  🎵 Music : YouTube via Discord                           ║
    ╠═══════════════════════════════════════════════════════════╣
    ║  📝 Use /join in Discord, then speak via web interface    ║
    ╚═══════════════════════════════════════════════════════════╝
    """)


async def preload_models():
    """Preload AI models."""
    logger.info("⏳ Loading AI models...")
    
    # Load Whisper
    try:
        from ear.transcriber import transcriber
        transcriber.load()
        logger.info("✅ Whisper loaded")
    except Exception as e:
        logger.warning(f"Whisper preload: {e}")
    
    # Test Ollama
    try:
        import ollama
        ollama.list()
        logger.info("✅ Ollama connected")
    except Exception as e:
        logger.error(f"❌ Ollama: {e}")


async def main():
    """Main entry point."""
    print_banner()
    
    if not DISCORD_TOKEN:
        logger.error("❌ DISCORD_TOKEN not set in .env")
        return
        
    # Preload models
    await preload_models()
    
    # Start both servers
    logger.info("🚀 Starting Jarvis...")
    
    from hand.discord_bot import run_bot
    from web.server import run_server
    
    # Run Discord bot and web server concurrently
    await asyncio.gather(
        run_bot(),
        run_server()
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Jarvis shutting down...")
