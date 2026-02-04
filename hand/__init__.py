"""Hand module - Discord Bot and Music Player"""
import discord.opus

# Load opus library for Discord voice
if not discord.opus.is_loaded():
    try:
        # Try common macOS locations
        for path in [
            '/opt/homebrew/lib/libopus.dylib',
            '/opt/homebrew/lib/libopus.0.dylib',
            '/usr/local/lib/libopus.dylib',
            'libopus',
        ]:
            try:
                discord.opus.load_opus(path)
                break
            except:
                continue
    except:
        pass

from .music import MusicPlayer
from .discord_bot import create_bot

__all__ = ['MusicPlayer', 'create_bot']
