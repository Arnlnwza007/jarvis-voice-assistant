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


from pydantic import BaseModel

class CommandRequest(BaseModel):
    text: str


@app.post("/api/command")
async def receive_command(request: CommandRequest):
    """
    Receive text command from external source (e.g. Siri Shortcuts).
    """
    logger.info(f"📱 API Command received: {request.text}")
    
    # Use Strict Matcher
    result = match_command_simple(request.text)
    
    if result:
        logger.info(f"✅ Command matched: {result['function']}")
        
        # Queue function for Discord execution
        await command_queue.put({
            "function": result["function"],
            "args": result["args"],
            "response": result["response"]
        })
        
        return {
            "status": "success",
            "command": result["function"],
            "response": result["response"]
        }
    else:
        logger.info(f"❌ Command ignored: {request.text}")
        return {
            "status": "ignored", 
            "message": "Unknown command"
        }


def match_command_simple(text: str) -> dict | None:
    """
    Match voice commands to intents using strict keyword lists.
    """
    cmd = text.strip().lower()
    
    # --- Keyword Definitions ---
    # Intent: play (Prefixes or Exact)
    PLAY_KEYWORDS = [
        "เล่น", "เปิด", "เริ่ม", "เริ่มเพลง", "เปิดเพลง", "เล่นเพลง", 
        "เปิดดนตรี", "เริ่มดนตรี", "เปิดให้หน่อย", "เริ่มให้หน่อย", 
        "เล่นเลย", "เปิดเลย", "เริ่มเลย", "เอาเพลง",
        "play", "start"
    ]
    
    # Intent: pause (Exact)
    PAUSE_KEYWORDS = [
        "หยุด", "พัก", "หยุดเพลง", "หยุดก่อน", "หยุดไว้ก่อน", 
        "พอ", "พอเพลง", "หยุดดนตรี", "หยุดชั่วคราว",
        "pause", "stop", "break"
    ]
    
    # Intent: resume (Exact)
    RESUME_KEYWORDS = [
        "ต่อ", "เล่นต่อ", "เปิดต่อ", "ไปต่อ", "ต่อเพลง", 
        "เล่นต่อเลย", "เอาต่อ",
        "resume", "continue", "unpause"
    ]
    
    # Intent: skip (Exact)
    SKIP_KEYWORDS = [
        "ข้าม", "เพลงถัดไป", "ถัดไป", "ข้ามเพลง", "เปลี่ยนเพลง", 
        "เปลี่ยน", "ไปเพลงหน้า", "เอาเพลงหน้า", "ข้ามเลย",
        "skip", "next"
    ]
    
    # Intent: join
    JOIN_KEYWORDS = [
        "เข้าห้อง", "เข้ามา", "มาในห้อง", "ตามมา",
        "มาห้องนี้", "เข้าช่อง",
        "join", "come here"
    ]

    # Intent: leave
    LEAVE_KEYWORDS = [
        "ออก", "ออกจากห้อง", "ออกไป",
        "ไปได้แล้ว", "เลิกเล่น",
        "leave", "disconnect", "bye"
    ]

    # Intent: move
    MOVE_KEYWORDS = [
        "ย้ายห้อง", "ย้ายมาห้องนี้",
        "ตามฉันมา", "เปลี่ยนห้อง",
        "ย้ายช่อง",
        "move"
    ]
    
    # Intent: Volume Up
    VOL_UP_KEYWORDS = [
        "เพิ่มเสียง", "ดังขึ้น", "เร่งเสียง", "เสียงเบาไป",
        "louder", "volume up"
    ]
    
    # Intent: Volume Down
    VOL_DOWN_KEYWORDS = [
        "ลดเสียง", "เบาลง", "เบาเสียง", "เสียงดังไป",
        "quieter", "volume down"
    ]

    # --- Matching Logic ---
    
    # Preprocessing: Remove polite particles and "bot"
    for noise in ["บอท", "ครับ", "ค่ะ", "jarvis", "จาวิส"]:
        cmd = cmd.replace(noise, "")
    cmd = cmd.strip()

    # Pattern: Set Volume (e.g. "เสียง 50")
    if any(cmd.startswith(p) for p in ["เสียง", "ปรับเสียง", "volume", "vol"]):
        import re
        match = re.search(r'\d+', cmd)
        if match:
            level = int(match.group())
            return {
                "function": "set_volume", 
                "args": {"level": level}, 
                "response": f"ปรับเสียงเป็น {level} เปอร์เซ็นต์ครับ"
            }

    # 1. Start with strict exact matches for simple commands
    
    # Join
    if cmd in JOIN_KEYWORDS:
        return {"function": "join", "args": {}, "response": "กำลังเข้าห้องครับ"}
        
    # Leave
    if cmd in LEAVE_KEYWORDS:
        return {"function": "leave", "args": {}, "response": "กำลังออกจากห้องครับ"}
        
    # Move
    if cmd in MOVE_KEYWORDS:
        return {"function": "move_channel", "args": {}, "response": "กำลังย้ายห้องครับ"}
        
    # Volume Up
    if cmd in VOL_UP_KEYWORDS:
        return {"function": "volume_up", "args": {}, "response": "เพิ่มเสียงให้ครับ"}
        
    # Volume Down
    if cmd in VOL_DOWN_KEYWORDS:
        return {"function": "volume_down", "args": {}, "response": "ลดเสียงให้ครับ"}
    
    # Resume
    if cmd in RESUME_KEYWORDS:
        return {"function": "resume_music", "args": {}, "response": "เล่นเพลงต่อครับ"}
        
    # Pause
    if cmd in PAUSE_KEYWORDS:
        return {"function": "pause_music", "args": {}, "response": "พักเพลงให้แล้วครับ"}
        
    # Skip
    if cmd in SKIP_KEYWORDS:
        return {"function": "skip", "args": {}, "response": "ข้ามเพลงครับ"}
    
    # Play (Exact match without song name -> Resume/Default action)
    if cmd in PLAY_KEYWORDS:
        return {"function": "resume_music", "args": {}, "response": "เล่นเพลงต่อครับ"}

    # 2. Check for "Play [song]" pattern (Prefix matching)
    for prefix in PLAY_KEYWORDS:
        if cmd.startswith(prefix):
            # Check if there is actual content after the keyword
            possible_song = cmd[len(prefix):].strip()
            if possible_song:
                return {
                    "function": "play_music", 
                    "args": {"song_name": possible_song}, 
                    "response": f"จัดให้ครับ กำลังค้นหา {possible_song}"
                }
    
    # 3. Other Utility Commands (Legacy)
    legacy_commands = {
        "เข้าห้อง": {"func": "join", "args": {}, "resp": "กำลังเข้าห้องเสียงครับ"},
        "มานี่": {"func": "join", "args": {}, "resp": "มาแล้วครับ"},
        "ออก": {"func": "leave", "args": {}, "resp": "บ๊ายบายครับ"},
        "ไปได้": {"func": "leave", "args": {}, "resp": "ผมไปก่อนนะครับ"},
        "เพิ่มเสียง": {"func": "volume_up", "args": {}, "resp": "เพิ่มเสียงให้ครับ"},
        "ดังขึ้น": {"func": "volume_up", "args": {}, "resp": "จัดให้ดังขึ้นครับ"},
        "ลดเสียง": {"func": "volume_down", "args": {}, "resp": "ลดเสียงให้ครับ"},
        "เบาลง": {"func": "volume_down", "args": {}, "resp": "เบาเสียงลงแล้วครับ"},
        "ล้างคิว": {"func": "clear_queue", "args": {}, "resp": "ล้างคิวเพลงเรียบร้อย"},
        "ดูคิว": {"func": "show_queue", "args": {}, "resp": "นี่คือคิวเพลงครับ"},
        "เปิดวนซ้ำ": {"func": "loop_on", "args": {}, "resp": "เปิดโหมดเล่นวนซ้ำครับ"},
        "ปิดวนซ้ำ": {"func": "loop_off", "args": {}, "resp": "ปิดโหมดเล่นวนซ้ำแล้วครับ"},
        "สถานะ": {"func": "show_status", "args": {}, "resp": "สถานะปัจจุบันครับ"},
        "เงียบ": {"func": "stop_music", "args": {}, "resp": "หยุดทุกอย่างครับ"}
    }
    
    if cmd in legacy_commands:
        c = legacy_commands[cmd]
        return {"function": c["func"], "args": c["args"], "response": c["resp"]}

    return None


async def process_text(text: str, websocket: WebSocket):
    """Process text command using pure logic (No LLM)."""
    
    # Use Strict Matcher
    result = match_command_simple(text)
    
    if result:
        logger.info(f"✅ Command matched: {result['function']}")
        
        # Send response to client
        await websocket.send_json({
            "type": "response",
            "text": result["response"],
            "function": result["function"],
            "args": result["args"]
        })
        
        # Queue function for Discord execution
        await command_queue.put({
            "function": result["function"],
            "args": result["args"],
            "response": result["response"]
        })
    else:
        logger.info(f"❌ Command ignored: {text}")
        await websocket.send_json({
            "type": "error",
            "text": "ไม่เข้าใจคำสั่งครับ (ลองพูด: เล่น, หยุด, ข้าม, ออก)"
        })


@app.websocket("/ws/voice")
async def voice_websocket(websocket: WebSocket):
    """WebSocket endpoint for voice and text input."""
    await websocket.accept()
    connected_clients.add(websocket)
    logger.info("Web client connected")
    
    try:
        while True:
            # Receive message
            message = await websocket.receive()
            if message["type"] == "websocket.disconnect":
                logger.info("WebSocket disconnect received")
                break
            
            # ... (rest of logic handles binary/json) ...
            
            audio_bytes = None
            
            if "bytes" in message and message["bytes"]:
                # Binary audio data (faster path)
                audio_bytes = message["bytes"]
            elif "text" in message and message["text"]:
                # JSON message
                import json
                try:
                    data = json.loads(message["text"])
                    if data.get("type") == "audio":
                        audio_base64 = data.get("data", "")
                        audio_bytes = base64.b64decode(audio_base64)
                    elif data.get("type") == "text":
                        # Text command direct handling
                        text_command = data.get("text", "").strip()
                        if text_command:
                            logger.info(f"Text command received: {text_command}")
                            await process_text(text_command, websocket)
                            continue
                except Exception as e:
                    logger.error(f"JSON parse error: {e}")
            
            if audio_bytes and len(audio_bytes) > 1000:
                # Save to temp file
                with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
                    f.write(audio_bytes)
                    temp_path = f.name
                
                logger.info(f"Audio received: {len(audio_bytes)} bytes")
                
                try:
                    # Transcribe with Whisper (run in thread to avoid blocking event loop)
                    # Force Thai language for better performance
                    text = await asyncio.to_thread(transcriber.transcribe, temp_path, language="th")
                    
                    if text:
                        logger.info(f"Heard: {text}")
                        
                        # Send transcription to client
                        await websocket.send_json({
                            "type": "transcription",
                            "text": text
                        })
                        
                        # Process text command
                        await process_text(text, websocket)
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "text": "ไม่ได้ยินครับ ลองพูดใหม่"
                        })
                        
                finally:
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
            elif audio_bytes:
                # Audio too short
                await websocket.send_json({
                    "type": "error",
                    "text": "เสียงสั้นเกินไป กดค้างนานขึ้นครับ"
                })
                    
    except WebSocketDisconnect:
        logger.info("Web client disconnected")
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
    try:
        await server.serve()
    except SystemExit:
        logger.error("Web server startup failed (port in use?)")
        raise
