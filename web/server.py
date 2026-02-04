"""
Web Server - Voice input via browser
Handles STT and sends commands to Discord bot
"""
import asyncio
import base64
import tempfile
import os
import logging
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import uvicorn

from config import WEB_HOST, WEB_PORT
from ear.transcriber import transcriber
from brain.llm import llm

logger = logging.getLogger(__name__)


def parse_simple_command(text: str) -> dict | None:
    """
    Parse simple voice commands directly without LLM.
    Returns command dict or None if not a simple command.
    """
    text = text.lower().strip()
    
    # เปิดเพลง / play
    if any(kw in text for kw in ["เปิดเพลง", "เล่นเพลง", "play ", "เปิด เพลง"]):
        # Extract song name - remove command keywords
        song = text
        for kw in ["เปิดเพลง", "เล่นเพลง", "play", "เปิด เพลง", "หน่อย", "ให้หน่อย", "ครับ", "ค่ะ"]:
            song = song.replace(kw, "")
        song = song.strip()
        
        if song:
            return {
                "function": "play_music",
                "args": {"song_name": song},
                "response": f"กำลังเปิดเพลง {song} ครับ"
            }
    
    # หยุดเพลง / stop
    if any(kw in text for kw in ["หยุดเพลง", "หยุด", "stop", "ปิดเพลง"]):
        return {
            "function": "stop_music",
            "args": {},
            "response": "หยุดเพลงแล้วครับ"
        }
    
    # พักเพลง / pause
    if any(kw in text for kw in ["พักเพลง", "pause", "หยุดชั่วคราว"]):
        return {
            "function": "pause_music",
            "args": {},
            "response": "พักเพลงแล้วครับ"
        }
    
    # เล่นต่อ / resume
    if any(kw in text for kw in ["เล่นต่อ", "resume", "ต่อเพลง"]):
        return {
            "function": "resume_music",
            "args": {},
            "response": "เล่นต่อแล้วครับ"
        }
    
    # ข้ามเพลง / skip
    if any(kw in text for kw in ["ข้ามเพลง", "skip", "เพลงต่อไป", "ข้าม"]):
        return {
            "function": "skip",
            "args": {},
            "response": "ข้ามเพลงแล้วครับ"
        }
    
    # ปรับเสียง / volume
    if any(kw in text for kw in ["ปรับเสียง", "volume", "เสียง"]):
        import re
        numbers = re.findall(r'\d+', text)
        level = int(numbers[0]) if numbers else 50
        return {
            "function": "set_volume",
            "args": {"level": level},
            "response": f"ปรับเสียงเป็น {level} แล้วครับ"
        }
    
    return None

logger = logging.getLogger(__name__)

app = FastAPI(title="Jarvis Voice Assistant")

# Connected clients and command queue
connected_clients = set()
command_queue = asyncio.Queue()

# Serve static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def index():
    """Serve main page."""
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse({"error": "index.html not found"})


@app.get("/api/status")
async def get_status():
    """Get system status."""
    from hand.discord_bot import bot_instance
    
    discord_connected = False
    voice_connected = False
    
    if bot_instance:
        discord_connected = bot_instance.is_ready() if hasattr(bot_instance, 'is_ready') else False
        voice_connected = len(bot_instance.voice_clients) > 0 if hasattr(bot_instance, 'voice_clients') else False
    
    return {
        "discord": discord_connected,
        "voice": voice_connected,
        "llm": llm.model
    }


@app.websocket("/ws/voice")
async def voice_websocket(websocket: WebSocket):
    """WebSocket endpoint for voice input from browser."""
    await websocket.accept()
    connected_clients.add(websocket)
    logger.info("🌐 Web client connected")
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "audio":
                # Decode audio from browser
                audio_base64 = data.get("data", "")
                audio_bytes = base64.b64decode(audio_base64)
                
                # Save to temp file
                with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
                    f.write(audio_bytes)
                    temp_path = f.name
                
                try:
                    # Transcribe with Whisper
                    text = transcriber.transcribe(temp_path)
                    
                    if text:
                        logger.info(f"🎤 Heard: {text}")
                        
                        # Send transcription to client
                        await websocket.send_json({
                            "type": "transcription",
                            "text": text
                        })
                        
                        # Try simple command parser first (faster, no LLM needed)
                        result = parse_simple_command(text)
                        
                        if result:
                            logger.info(f"⚡ Simple command: {result['function']}")
                        else:
                            # No LLM - just return friendly message for unrecognized commands
                            logger.info(f"❓ Unknown command: {text}")
                            result = {
                                "function": None,
                                "response": f"ไม่เข้าใจคำสั่ง ลองพูดว่า 'เปิดเพลง [ชื่อเพลง]' ครับ"
                            }
                        
                        # Send response to client
                        await websocket.send_json({
                            "type": "response",
                            "text": result.get("response") if result else "ไม่เข้าใจครับ",
                            "function": result.get("function") if result else None,
                            "args": result.get("args") if result else None
                        })
                        
                        # Queue function for Discord execution
                        if result and result.get("function"):
                            await command_queue.put({
                                "function": result["function"],
                                "args": result.get("args", {}),
                                "response": result.get("response")
                            })
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "text": "ไม่ได้ยินครับ ลองพูดใหม่"
                        })
                        
                finally:
                    os.unlink(temp_path)
                    
    except WebSocketDisconnect:
        logger.info("🌐 Web client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        connected_clients.discard(websocket)


async def broadcast(message: dict):
    """Broadcast message to all connected web clients."""
    for client in connected_clients:
        try:
            await client.send_json(message)
        except:
            pass


async def run_server():
    """Run the web server."""
    config = uvicorn.Config(app, host=WEB_HOST, port=WEB_PORT, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()
