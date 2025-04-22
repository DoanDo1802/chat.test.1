"""
Module để tương tác với Gemini API.
"""
import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL, REQUEST_TIMEOUT

class GeminiClient:
    """
    Lớp để tương tác với Gemini API.
    """
    def __init__(self):
        """
        Khởi tạo client với API key từ cấu hình.
        """
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY không được cấu hình. Vui lòng kiểm tra file .env")

        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(GEMINI_MODEL)

    def generate_response(self, prompt, image_data=None):
        """
        Gửi prompt và ảnh (nếu có) đến Gemini API và nhận phản hồi.

        Args:
            prompt (str): Câu hỏi hoặc yêu cầu của người dùng
            image_data (str, optional): Dữ liệu ảnh dạng base64

        Returns:
            str: Phản hồi từ Gemini API
        """
        try:
            if image_data:
                # Xử lý khi có ảnh
                parts = [
                    {"mime_type": "image/jpeg", "data": image_data.split(',')[1] if ',' in image_data else image_data},
                    {"text": prompt}
                ]
                response = self.model.generate_content(parts, timeout=REQUEST_TIMEOUT)
            else:
                # Xử lý khi không có ảnh
                response = self.model.generate_content(prompt, timeout=REQUEST_TIMEOUT)

            return response.text
        except Exception as e:
            return f"Lỗi khi gọi Gemini API: {str(e)}"
