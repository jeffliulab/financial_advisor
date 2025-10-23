"""
Backend service configuration.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Service Configuration
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))
BRAIN_SERVICE_URL = os.getenv("BRAIN_SERVICE_URL", "http://localhost:8001")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
