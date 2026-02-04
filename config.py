"""
Jarvis Configuration
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
BASE_DIR = Path(__file__).parent

# Discord
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Web Server
WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
WEB_PORT = int(os.getenv("WEB_PORT", "8080"))

# STT (Whisper)
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "medium")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cuda")

# LLM (Ollama)
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "typhoon2:8b")

# TTS
TTS_VOICE = os.getenv("TTS_VOICE", "th-TH-PremwadeeNeural")
TTS_ENABLED = os.getenv("TTS_ENABLED", "true").lower() == "true"

# Lavalink Server (Free hosting)
LAVALINK_URI = os.getenv("LAVALINK_URI", "http://lavalink.devamop.in:80")
LAVALINK_PASSWORD = os.getenv("LAVALINK_PASSWORD", "DevamOP")

# System Prompt
SYSTEM_PROMPT = """คุณคือ Jarvis ผู้ช่วย AI ตอบสั้น ภาษาไทย ลงท้าย "ครับ"

ฟังก์ชันที่เรียกได้:
- play_music(song_name): เปิดเพลง
- stop_music(): หยุดเพลง
- pause_music(): พักเพลง
- resume_music(): เล่นต่อ
- set_volume(level): ปรับเสียง 0-100
- skip(): ข้ามเพลง

ตอบเป็น JSON:
{"function": "play_music", "args": {"song_name": "ชื่อเพลง"}, "response": "กำลังเปิดเพลงครับ"}

ถ้าไม่ต้องเรียกฟังก์ชัน:
{"function": null, "response": "คำตอบ"}"""
