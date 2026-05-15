import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# RL Settings
MAX_ITERATIONS = 2  # Allows for refinement loop
TARGET_SCORE = 8
OUTPUT_DIR = "outputs"