# Jarvis Discord Bot

ระบบ Jarvis AI Discord Bot ที่รองรับการสนทนาด้วยเสียง

## Features

- 🎤 **Speech-to-Text (STT)**: ใช้ Whisper แปลงเสียงพูดเป็นข้อความ
- 🧠 **AI Brain (LLM)**: ใช้ Ollama + Llama 3 ประมวลผลและตอบคำถาม
- 🔊 **Text-to-Speech (TTS)**: ใช้ Edge-TTS แปลงข้อความเป็นเสียง

## Prerequisites

- Python 3.10+
- FFmpeg
- Ollama (with Llama 3 model installed)

## Installation

1. Clone the repository
2. Create virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and fill in your Discord token
5. Run the bot:
   ```bash
   python main.py
   ```

## Commands

- `/join` - Join your voice channel
- `/leave` - Leave voice channel
- `/listen` - Start listening mode
- `/stop` - Stop listening
- `/ask [text]` - Ask Jarvis via text

## Wake Word

Say "Jarvis" followed by your command to activate voice interaction.
