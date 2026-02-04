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
        
    def reset(self):
        """Clear conversation history."""
        self.history = []
        
    async def chat(self, message: str) -> dict:
        """Send message to LLM and get response with function call if any."""
        try:
            self.history.append({"role": "user", "content": message})
            
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    *self.history
                ],
                format="json"
            )
            
            content = response["message"]["content"]
            self.history.append({"role": "assistant", "content": content})
            
            # Parse JSON response
            try:
                result = json.loads(content)
                return {
                    "function": result.get("function"),
                    "args": result.get("args", {}),
                    "response": result.get("response", content)
                }
            except json.JSONDecodeError:
                return {
                    "function": None,
                    "args": {},
                    "response": content
                }
                
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return {
                "function": None,
                "args": {},
                "response": f"ขออภัยครับ เกิดข้อผิดพลาด: {str(e)}"
            }


async def process_command(text: str, llm: LLM = None) -> dict:
    """Process text command through LLM."""
    if llm is None:
        llm = LLM()
    return await llm.chat(text)


# Global instance
llm = LLM()
