"""
Music Player - YouTube playback via yt-dlp and FFmpeg
Simple and reliable without external servers
"""
import asyncio
import logging
import discord
import yt_dlp

logger = logging.getLogger(__name__)

YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
    'nocheckcertificate': True,
    'socket_timeout': 10,
    'retries': 10,
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -reconnect_at_eof 1',
    'options': '-vn -filter:a volume=0.5'
}


class MusicPlayer:
    """YouTube music player for Discord using yt-dlp."""
    
    def __init__(self):
        self.current_song = None
        self.is_playing = False
        self.volume = 0.5
        
    async def play_music(self, query: str, voice_client: discord.VoiceClient) -> str:
        """Search and play music from YouTube."""
        try:
            logger.info(f"🔍 Searching: {query}")
            
            # Run yt-dlp in executor
            loop = asyncio.get_running_loop()
            
            def extract():
                with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                    if not query.startswith('http'):
                        search = f"ytsearch:{query}"
                    else:
                        search = query
                    return ydl.extract_info(search, download=False)
            
            info = await loop.run_in_executor(None, extract)
            
            if 'entries' in info:
                info = info['entries'][0]
                
            # Get audio URL
            url = info.get('url')
            if not url:
                for fmt in info.get('formats', []):
                    if fmt.get('acodec') != 'none' and fmt.get('vcodec') == 'none':
                        url = fmt.get('url')
                        break
                        
            if not url:
                url = info.get('webpage_url', info.get('url'))
                # Re-extract for direct URL
                def get_direct():
                    with yt_dlp.YoutubeDL({**YDL_OPTIONS, 'format': 'bestaudio'}) as ydl:
                        return ydl.extract_info(url, download=False)
                info = await loop.run_in_executor(None, get_direct)
                url = info.get('url')
                
            if not url:
                logger.error("No audio URL found")
                return None
                
            title = info.get('title', 'Unknown')
            self.current_song = title
            logger.info(f"🎵 Playing: {title}")
            
            # Stop current
            if voice_client.is_playing():
                voice_client.stop()
                await asyncio.sleep(0.5)
            
            # Play
            source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
            voice_client.play(source, after=lambda e: self._on_end(e))
            self.is_playing = True
            
            return title
            
        except Exception as e:
            logger.error(f"Music error: {e}")
            import traceback
            traceback.print_exc()
            return None
            
    def _on_end(self, error):
        if error:
            logger.error(f"Player error: {error}")
        self.is_playing = False
        self.current_song = None
            
    async def stop_music(self, voice_client) -> bool:
        if voice_client and voice_client.is_playing():
            voice_client.stop()
            self.is_playing = False
            self.current_song = None
            return True
        return False
        
    async def pause_music(self, voice_client) -> bool:
        if voice_client and voice_client.is_playing():
            voice_client.pause()
            return True
        return False
        
    async def resume_music(self, voice_client) -> bool:
        if voice_client and voice_client.is_paused():
            voice_client.resume()
            return True
        return False
        
    def set_volume(self, level: int, voice_client):
        self.volume = max(0, min(100, level)) / 100
        
    async def skip(self, voice_client) -> bool:
        return await self.stop_music(voice_client)


music_player = MusicPlayer()
