# Jarvis Discord Bot

ระบบ Jarvis AI Discord Bot ที่รองรับการสนทนาด้วยเสียง

## Features

- 🎤 **Speech-to-Text (STT)**: ใช้ Whisper แปลงเสียงพูดเป็นข้อความ
- 🧠 **AI Brain (LLM)**: ใช้ Ollama + DeepSeek-R1 ประมวลผลและตอบคำถาม
- 🔊 **Text-to-Speech (TTS)**: ใช้ Edge-TTS แปลงข้อความเป็นเสียง
- 🎵 **Music Player**: เล่นเพลงจาก YouTube ผ่าน Discord

## Prerequisites

- Python 3.10+
- FFmpeg (มี binary รวมมาให้แล้ว หรือ `brew install ffmpeg`)
- Ollama (with model installed, e.g. `ollama pull deepseek-r1:8b`)

## Installation

### macOS
```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy .env.example to .env and fill in your Discord token
cp .env.example .env

# 4. Run the bot
python app.py
```

### Windows
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

## Architecture

```
🌐 Web (Push-to-talk) → 👂 Ear (Whisper STT) → 🧠 Brain (Ollama LLM)
                                                       ↓
                         🤚 Hand (Discord Bot) ← Command Queue
                              ↓
                         🗣️ Mouth (Edge-TTS) + 🎵 Music (yt-dlp)
```

## Commands

- `/join` - Join your voice channel
- `/leave` - Leave voice channel
- `/play [song]` - Play music from YouTube
- `/stop` - Stop music

## Voice Commands (via Web)

- "เปิดเพลง [ชื่อเพลง]" - เปิดเพลง
- "หยุดเพลง" - หยุดเพลง
- "พักเพลง" - พักเพลงชั่วคราว
- "เล่นต่อ" - เล่นเพลงต่อ
- "ข้ามเพลง" - ข้ามเพลงปัจจุบัน
- หรือพูดอะไรก็ได้ Jarvis จะตอบผ่าน LLM

## Configuration (.env)

```env
DISCORD_TOKEN=your_token_here
OLLAMA_MODEL=deepseek-r1:8b
WHISPER_MODEL=medium
WHISPER_DEVICE=cpu
TTS_VOICE=th-TH-NiwatNeural
WEB_PORT=8080
```
