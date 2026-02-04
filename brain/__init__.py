"""Brain module - LLM with Function Calling"""
from .llm import LLM, process_command
from .functions import FUNCTIONS

__all__ = ['LLM', 'process_command', 'FUNCTIONS']
