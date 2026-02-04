"""
Gemini Live Standalone Test
Test the Gemini Live API directly without Discord
"""
import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from services.gemini_live_service import GeminiLiveService


async def main():
    print("=" * 50)
    print("  JARVIS - Gemini Live Test")
    print("=" * 50)
    print()
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key or api_key == 'your_gemini_api_key_here':
        print("❌ กรุณาใส่ GEMINI_API_KEY ใน .env file")
        print("   รับ API Key ได้ที่: https://aistudio.google.com/apikey")
        return
        
    print("✅ GEMINI_API_KEY found")
    print()
    
    service = GeminiLiveService()
    
    try:
        await service.initialize()
        print()
        print("🎤 เริ่มการสนทนา... (กด Ctrl+C เพื่อหยุด)")
        print("   พูดใส่ไมค์ได้เลยครับ")
        print()
        
        await service.run_conversation(voice="Zephyr")
        
    except KeyboardInterrupt:
        print("\n\n👋 หยุดการสนทนา")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
