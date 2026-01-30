import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-3-flash-preview"
REQUEST_TIMEOUT = 30  # seconds
MAX_HEADLINES = 5
