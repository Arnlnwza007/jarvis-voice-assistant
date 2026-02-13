"""
LLM - Local Language Model using Ollama
Handles Thai language understanding and function calling
"""
import json
import logging
import ollama
from config import OLLAMA_MODEL, SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class LLM:
    """Local LLM using Ollama."""
    
    def __init__(self, model: str = None):
        self.model = model or OLLAMA_MODEL
        self.history = []
        self.system_prompt = """You are NOT a chatbot.
You are NOT an assistant.
You are a strict voice command filter for a Discord music bot.

Your job is ONLY to validate and normalize voice commands.

You MUST follow these rules:
1. Accept ONLY exact predefined Thai commands.
2. Do NOT interpret natural language.
3. Do NOT guess user intent.
4. Do NOT explain anything.
5. Do NOT generate extra text.
6. If input does not exactly match allowed commands, return: IGNORE
7. Output must be a single word command in lowercase.
8. No JSON. No additional characters.

Allowed Commands (Exact Match Only):
เล่น → play
หยุด → pause
ต่อ → resume
ข้าม → skip
เข้าห้อง → join
ออก → leave
เพิ่มเสียง → volume_up
ลดเสียง → volume_down
ล้างคิว → clear
ดูคิว → queue
เปิดวนซ้ำ → loop_on
ปิดวนซ้ำ → loop_off
สถานะ → status

If input does not EXACTLY match one of the allowed commands:
Output: IGNORE
"""

    async def chat(self, user_input: str) -> dict:
        """Chat with LLM and return command."""
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        try:
            response = ollama.chat(
                model=self.model,
                messages=messages,
                options={"temperature": 0.0}
            )
            
            content = response['message']['content'].strip()
            
            # Map simple text output to functions
            mapping = {
                "play": "resume_music",  # 'เล่น' map to resume contextually or play if modified
                "pause": "pause_music",
                "resume": "resume_music",
                "skip": "skip_music",
                "join": "join",
                "leave": "leave",
                "volume_up": "volume_up",     # Need to implement
                "volume_down": "volume_down", # Need to implement
                "clear": "clear_queue",
                "queue": "show_queue",
                "loop_on": "loop_on",
                "loop_off": "loop_off",
                "status": "show_status",
                "IGNORE": None
            }
            
            # Special case for 'play' which might need logic, but for now map strictly
            # Note: The prompt maps 'เล่น' -> 'play'
            if content == "play":
                 # 'เล่น' in this strict context usually means resume or play (but no args allowed per prompt rules)
                 # So we map it to resume_music for now, or could map to a generic play
                 func_name = "resume_music" 
            elif content in mapping:
                func_name = mapping[content]
            else:
                func_name = None
                
            if func_name:
                return {
                    "function": func_name,
                    "args": {},
                    "response": f"รับทราบ: {content}"
                }
            else:
                return {
                    "function": None,
                    "args": {},
                    "response": "คำสั่งไม่ถูกต้อง (IGNORE)"
                }
                
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return {"function": None, "args": {}, "response": "Error"}


async def process_command(text: str, llm: LLM = None) -> dict:
    """Process text command through LLM."""
    if llm is None:
        llm = LLM()
    return await llm.chat(text)


# Global instance
llm = LLM()
