import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

class Config:
    MONGO_URI = os.getenv("MONGO_URI")
    SECRET_KEY = os.getenv("SECRET_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")