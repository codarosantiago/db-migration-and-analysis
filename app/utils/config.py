import os
from dotenv import load_dotenv
import logging

load_dotenv()  # Load environment variables from .env file

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn")

POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
if POSTGRES_PASSWORD is None:
    raise ValueError("Environment variable POSTGRES_PASSWORD is not set")
