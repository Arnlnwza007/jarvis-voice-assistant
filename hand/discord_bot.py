"""
Discord Bot - Commands and music playback
"""
import asyncio
import logging
import discord
from discord.ext import commands

from config import DISCORD_TOKEN
from hand.music import music_player
from mouth.tts import speak

logger = logging.getLogger(__name__)

bot_instance = None


def create_bot():
    """Create Discord bot."""
    global bot_instance
    
    intents = discord.Intents.default()
    intents.message_content = True
    intents.voice_states = True
    intents.guilds = True
    
    bot = commands.Bot(command_prefix="!", intents=intents)
    
    @bot.event
    async def on_ready():
        logger.info(f"✅ Jarvis online: {bot.user}")
        asyncio.create_task(process_commands(bot))
        try:
            synced = await bot.tree.sync()
            logger.info(f"Synced {len(synced)} commands")
        except Exception as e:
            logger.error(f"Sync error: {e}")
        
    @bot.tree.command(name="join", description="เข้าห้องเสียง")
    async def join(interaction: discord.Interaction):
        if not interaction.user.voice:
            await interaction.response.send_message("❌ เข้าห้องเสียงก่อนครับ", ephemeral=True)
            return
        await interaction.response.defer()
        channel = interaction.user.voice.channel
        voice_client = await channel.connect()
        await interaction.followup.send(f"✅ เข้าห้อง **{channel.name}** แล้วครับ")
        
        # รอให้ voice connection พร้อมก่อนพูด
        await asyncio.sleep(2)
        
        # Jarvis กล่าวทักทายเมื่อเข้าห้อง
        await speak("สวัสดีครับเจ้านาย Jarvis พร้อมรับคำสั่งครับ", voice_client)
        
    @bot.tree.command(name="leave", description="ออกจากห้องเสียง")
    async def leave(interaction: discord.Interaction):
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
            await interaction.response.send_message("👋 ออกแล้วครับ")
        else:
            await interaction.response.send_message("❌ ไม่ได้อยู่ในห้องครับ", ephemeral=True)
            
    @bot.tree.command(name="play", description="เล่นเพลง")
    async def play(interaction: discord.Interaction, song: str):
        # Defer immediately to avoid "Application did not respond"
        await interaction.response.defer()
        
        if not interaction.guild.voice_client:
            if interaction.user.voice:
                try:
                    await interaction.user.voice.channel.connect()
                except Exception as e:
                    await interaction.followup.send(f"❌ เชื่อมต่อห้องเสียงไม่ได้: {e}")
                    return
            else:
                await interaction.followup.send("❌ เข้าห้องเสียงก่อนครับ")
                return
        
        title = await music_player.play_music(song, interaction.guild.voice_client)
        await interaction.followup.send(f"🎵 เล่น: **{title}**" if title else "❌ ไม่พบเพลง")
        
    @bot.tree.command(name="stop", description="หยุดเพลง")
    async def stop(interaction: discord.Interaction):
        if interaction.guild.voice_client:
            await music_player.stop_music(interaction.guild.voice_client)
            await interaction.response.send_message("⏹️ หยุดแล้ว")
        else:
            await interaction.response.send_message("❌ ไม่ได้เล่นอยู่", ephemeral=True)
            
    bot_instance = bot
    return bot


async def process_commands(bot):
    """Process commands from web interface."""
    from web.server import command_queue
    
    logger.info("🎵 Waiting for commands from web...")
    
    while True:
        try:
            cmd = await asyncio.wait_for(command_queue.get(), timeout=1.0)
            
            func = cmd.get("function")
            args = cmd.get("args", {})
            
            logger.info(f"📥 Received: {func}({args})")
            
            # Get voice client
            # Get voice client
            voice_client = bot.voice_clients[0] if bot.voice_clients else None
            
            # Helper to find a channel with users
            def find_active_channel(guilds):
                for guild in guilds:
                    for vc in guild.voice_channels:
                        # Find channel with non-bot members
                        if any(not m.bot for m in vc.members):
                            return vc
                return None

            if func == "join":
                if voice_client:
                    await speak("ผมอยู่ในห้องแล่วครับ", voice_client)
                    continue
                
                channel = find_active_channel(bot.guilds)
                if channel:
                    logger.info(f"Joining {channel.name}...")
                    voice_client = await channel.connect()
                    
                    # Custom Join Sound: Find ANY audio file in assets
                    import os
                    from config import FFMPEG_PATH
                    
                    join_sound = None
                    assets_dir = "assets"
                    
                    if os.path.exists(assets_dir):
                        audio_files = []
                        for f in os.listdir(assets_dir):
                            if f.lower().endswith(('.mp3', '.m4a', '.wav', '.ogg')):
                                audio_files.append(os.path.join(assets_dir, f))
                        
                        if audio_files:
                            # Prioritize file with 'join' in name
                            for f in audio_files:
                                if "join" in os.path.basename(f).lower():
                                    join_sound = f
                                    break
                            # Fallback to first file
                            if not join_sound:
                                join_sound = audio_files[0]

                    if join_sound:
                        source = discord.PCMVolumeTransformer(
                            discord.FFmpegPCMAudio(join_sound, executable=FFMPEG_PATH)
                        )
                        source.volume = music_player.volume
                        voice_client.play(source)
                        logger.info(f"🎵 Playing join sound: {join_sound}")
                    else:
                        await speak("สวัสดีครับเจ้านาย", voice_client)
                else:
                    logger.warning("❌ No active voice channel found.")
                continue

            if not voice_client:
                logger.warning("⚠️ No voice client - use /join first!")
                continue

            if func == "leave":
                await speak("บ๊ายบายครับ", voice_client)
                await voice_client.disconnect()
                continue

            elif func == "move_channel":
                # Find a different channel with users
                current_channel = voice_client.channel
                target_channel = None
                
                for guild in bot.guilds:
                    for vc in guild.voice_channels:
                        if vc.id == current_channel.id:
                            continue
                        if any(not m.bot for m in vc.members):
                            target_channel = vc
                            break
                    if target_channel: break
                
                if target_channel:
                    await speak("กำลังย้ายห้องครับ", voice_client)
                    await voice_client.move_to(target_channel)
                    await asyncio.sleep(1) # Wait for move
                    await speak("ตามมาแล้วครับ", voice_client)
                else:
                    await speak("ไม่เจอห้องที่จะย้ายไปครับ", voice_client)
                continue

            if func == "play_music":
                song = args.get("song_name", "")
                
                # Send text feedback to channel (Last active channel or first text channel)
                if voice_client and voice_client.channel:
                    # Try to find a text channel to reply in
                    text_channel = voice_client.guild.system_channel or voice_client.guild.text_channels[0]
                    if text_channel:
                         await text_channel.send(f"🎤 **Jarvis ได้ยินว่า:** เปิดเพลง {song}\n▶️ **กำลังเล่นโดย:** {bot.user.name}")
                
                title = await music_player.play_music(song, voice_client)
                logger.info(f"🎵 Now playing: {title}")
                
            elif func == "stop_music":
                await music_player.stop_music(voice_client)
                
            elif func == "pause_music":
                await music_player.pause_music(voice_client)
                
            elif func == "resume_music":
                await music_player.resume_music(voice_client)
                
            elif func == "skip":
                await music_player.skip(voice_client)
                
            elif func == "volume_up":
                # Increase volume by 20%
                current_vol = int(music_player.volume * 100)
                new_vol = min(100, current_vol + 20)
                music_player.set_volume(new_vol, voice_client)
                logger.info(f"🔊 Volume up: {new_vol}%")
                
            elif func == "volume_down":
                # Decrease volume by 20%
                current_vol = int(music_player.volume * 100)
                new_vol = max(0, current_vol - 20)
                music_player.set_volume(new_vol, voice_client)
                logger.info(f"🔉 Volume down: {new_vol}%")

            elif func == "set_volume":
                music_player.set_volume(args.get("level", 50), voice_client)
                
        except asyncio.TimeoutError:
            continue
        except asyncio.CancelledError:
            logger.info("🛑 Command processor stopping...")
            break
        except Exception as e:
            logger.error(f"Command error: {e}")


async def run_bot():
    """Run the Discord bot."""
    bot = create_bot()
    if DISCORD_TOKEN:
        await bot.start(DISCORD_TOKEN)
    else:
        logger.error("DISCORD_TOKEN not set!")
