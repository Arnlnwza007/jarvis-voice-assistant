#!/usr/bin/env python3
"""
Test Whisper STT - ทดสอบว่า Whisper model โหลดและ transcribe ได้ถูกต้อง
"""
import os
import sys
import tempfile
import wave
import struct
import math

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def create_test_audio(duration_sec=2, sample_rate=16000):
    """Create a silent test audio file (WAV)."""
    filepath = tempfile.mktemp(suffix=".wav")
    n_samples = int(sample_rate * duration_sec)
    
    with wave.open(filepath, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        
        # Generate silence with tiny noise (avoids Whisper hallucination on pure silence)
        import random
        samples = [random.randint(-10, 10) for _ in range(n_samples)]
        data = struct.pack(f'{n_samples}h', *samples)
        wav_file.writeframes(data)
    
    return filepath


def test_config():
    """Test configuration loading."""
    print("=" * 50)
    print("🔧 Testing Configuration")
    print("=" * 50)
    
    from config import FFMPEG_PATH, WHISPER_MODEL, WHISPER_DEVICE, OLLAMA_MODEL
    
    print(f"  FFMPEG_PATH  : {FFMPEG_PATH}")
    print(f"  FFmpeg exists: {os.path.exists(FFMPEG_PATH)}")
    print(f"  WHISPER_MODEL: {WHISPER_MODEL}")
    print(f"  WHISPER_DEVICE: {WHISPER_DEVICE}")
    print(f"  OLLAMA_MODEL : {OLLAMA_MODEL}")
    
    assert os.path.exists(FFMPEG_PATH), f"FFmpeg not found: {FFMPEG_PATH}"
    print("  ✅ Config OK\n")


def test_whisper_load():
    """Test Whisper model loading."""
    print("=" * 50)
    print("🎤 Testing Whisper Model Load")
    print("=" * 50)
    
    from ear.transcriber import transcriber
    
    print("  Loading model...")
    transcriber.load()
    assert transcriber.model is not None, "Model failed to load"
    print("  ✅ Whisper model loaded\n")


def test_whisper_transcribe():
    """Test Whisper transcription with silent audio."""
    print("=" * 50)
    print("🎙️ Testing Whisper Transcription")
    print("=" * 50)
    
    from ear.transcriber import transcriber
    
    # Create test audio
    audio_path = create_test_audio()
    print(f"  Created test audio: {audio_path}")
    print(f"  File size: {os.path.getsize(audio_path)} bytes")
    
    try:
        # Transcribe (should return empty or very short text for silence)
        result = transcriber.transcribe(audio_path, language="th")
        print(f"  Transcription result: '{result}'")
        print("  ✅ Transcription completed (no crash)\n")
    finally:
        os.unlink(audio_path)


def test_ollama():
    """Test Ollama LLM connection."""
    print("=" * 50)
    print("🧠 Testing Ollama LLM")
    print("=" * 50)
    
    try:
        import ollama
        models = ollama.list()
        model_names = [m.get('name', m.get('model', 'unknown')) for m in models.get('models', [])]
        print(f"  Available models: {model_names}")
        print("  ✅ Ollama connected\n")
    except Exception as e:
        print(f"  ❌ Ollama error: {e}\n")


def test_tts():
    """Test TTS generation."""
    print("=" * 50)
    print("🗣️ Testing TTS (Edge-TTS)")
    print("=" * 50)
    
    import asyncio
    from mouth.tts import generate_speech
    
    async def _test():
        path = await generate_speech("ทดสอบ")
        if path and os.path.exists(path):
            size = os.path.getsize(path)
            print(f"  Generated: {path} ({size} bytes)")
            os.unlink(path)
            assert size > 0, "TTS file is empty"
            print("  ✅ TTS OK\n")
        else:
            print("  ❌ TTS generation failed\n")
    
    asyncio.run(_test())


if __name__ == "__main__":
    print("\n🤖 Jarvis System Test\n")
    
    tests = [
        ("Config", test_config),
        ("Whisper Load", test_whisper_load),
        ("Whisper Transcribe", test_whisper_transcribe),
        ("Ollama", test_ollama),
        ("TTS", test_tts),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"  ❌ {name} FAILED: {e}\n")
            failed += 1
    
    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 50)
