"""
Cấu hình cho ứng dụng đa luồng và đa tiến trình với Gemini API.
"""
import os
from dotenv import load_dotenv

# Tải biến môi trường từ file .env
load_dotenv()

# Cấu hình API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.0-flash-001"

# Cấu hình đa luồng
MAX_THREADS = 5  # Số lượng luồng tối đa

# Cấu hình đa tiến trình
MAX_PROCESSES = 3  # Số lượng tiến trình tối đa

# Cấu hình timeout
REQUEST_TIMEOUT = 30  # Thời gian timeout cho mỗi request (giây)
