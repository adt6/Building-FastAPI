"""
Configuration constants for the clinical AI agent.
"""
from pathlib import Path

# --- Configuration ---
INSTRUCTIONS_FILE_PATH = Path("agent/prompts/clinical_instructions.md")  # Use Path object
HAIKU_LLM_TYPE = "haiku"
SONNET_LLM_TYPE = "sonnet"
MIXTRAL_LLM_TYPE = "mixtral_groq"
OPENAI_LLM_TYPE = "openai"

DEFAULT_LLM_TYPE = SONNET_LLM_TYPE  # Options: "haiku", "sonnet", "mixtral_groq", "openai"

FALLBACK_INSTRUCTIONS = "You are a helpful clinical assistant. Assume today's date is {{CURRENT_DATE}}."

# Model IDs (Use official IDs)
MODEL_ID_HAIKU = "claude-3-haiku-20240307"
MODEL_ID_SONNET = "claude-3-5-sonnet-20241022"
MODEL_ID_LLAMA_GROQ = "llama3-70b-8192"  # Verify correct Groq model ID if needed
MODEL_ID_GEMINI = "gemini-pro"  # Verify correct Gemini model ID if needed
MODEL_ID_MIXTRAL = "mistral-saba-24b"
MODEL_ID_OPENAI = "gpt-4o-mini"

# API Configuration
DEFAULT_API_BASE_URL = "http://localhost:8000/api/v2"
