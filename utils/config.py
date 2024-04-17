# utils/config.py
import os
from dotenv import load_dotenv

# Load environment variables from a .env file if present
load_dotenv()

class Config:
    # Example configuration property
    TOKEN = os.getenv("TOKEN")
    DATABASE_URI = os.getenv("DATABASE_URI")
    # Add other configuration properties as needed

# Usage example
# config = Config()
# print(config.TELEGRAM_BOT_TOKEN)
