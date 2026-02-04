"""
Function definitions for Jarvis
These are the actions Jarvis can perform
"""

FUNCTIONS = {
    "play_music": {
        "description": "เปิดเพลงจาก YouTube",
        "parameters": {
            "song_name": {"type": "string", "description": "ชื่อเพลงหรือศิลปิน"}
        }
    },
    "stop_music": {
        "description": "หยุดเพลงที่กำลังเล่น",
        "parameters": {}
    },
    "pause_music": {
        "description": "พักเพลง",
        "parameters": {}
    },
    "resume_music": {
        "description": "เล่นเพลงต่อ",
        "parameters": {}
    },
    "set_volume": {
        "description": "ปรับระดับเสียง",
        "parameters": {
            "level": {"type": "integer", "description": "ระดับเสียง 0-100"}
        }
    },
    "skip": {
        "description": "ข้ามเพลงปัจจุบัน",
        "parameters": {}
    },
    "queue": {
        "description": "เพิ่มเพลงเข้าคิว",
        "parameters": {
            "song_name": {"type": "string", "description": "ชื่อเพลง"}
        }
    }
}


def get_function_prompt():
    """Generate function list for system prompt."""
    lines = ["คุณสามารถเรียกใช้ฟังก์ชันต่อไปนี้:"]
    for name, info in FUNCTIONS.items():
        params = ", ".join(info["parameters"].keys())
        lines.append(f"- {name}({params}): {info['description']}")
    return "\n".join(lines)
