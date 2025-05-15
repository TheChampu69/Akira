import os

class Config:
    API_ID = os.getenv("API_ID", "15657755")
    API_HASH = os.getenv("API_HASH", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    STREAMUP_API_KEY = os.getenv("STREAMUP_API_KEY", "")

    # Validate required environment variables
    @staticmethod
    def validate_config():
        required_vars = ["API_HASH", "BOT_TOKEN", "STREAMUP_API_KEY"]
        missing_vars = [var for var in required_vars if not getattr(Config, var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
