"""
Module quản lý đa luồng để xử lý các yêu cầu đến Gemini API.
"""
import threading
import queue
import time
from gemini_client import GeminiClient
from config import MAX_THREADS

class ThreadManager:
    """
    Quản lý các luồng để xử lý yêu cầu đến Gemini API.
    """
    def __init__(self):
        """
        Khởi tạo ThreadManager với hàng đợi và danh sách luồng.
        """
        self.request_queue = queue.Queue()
        self.response_queue = queue.Queue()
        self.threads = []
        self.client = GeminiClient()
        self.stop_event = threading.Event()
    
    def add_request(self, prompt, request_id=None):
        """
        Thêm một yêu cầu vào hàng đợi.
        
        Args:
            prompt (str): Câu hỏi hoặc yêu cầu của người dùng
            request_id: ID của yêu cầu (nếu có)
        """
        if request_id is None:
            request_id = f"req_{int(time.time() * 1000)}"
        
        self.request_queue.put((request_id, prompt))
        return request_id
    
    def worker(self):
        """
        Hàm xử lý cho mỗi luồng.
        """
        while not self.stop_event.is_set():
            try:
                # Lấy yêu cầu từ hàng đợi với timeout để có thể kiểm tra stop_event
                request_id, prompt = self.request_queue.get(timeout=0.5)
                
                # Gọi API Gemini
                response = self.client.generate_response(prompt)
                
                # Đưa kết quả vào hàng đợi phản hồi
                self.response_queue.put((request_id, prompt, response))
                
                # Đánh dấu công việc đã hoàn thành
                self.request_queue.task_done()
                
            except queue.Empty:
                # Hàng đợi trống, tiếp tục vòng lặp
                continue
            except Exception as e:
                # Xử lý lỗi và đưa vào hàng đợi phản hồi
                if 'request_id' in locals() and 'prompt' in locals():
                    self.response_queue.put((request_id, prompt, f"Lỗi xử lý: {str(e)}"))
                    self.request_queue.task_done()
    
    def start(self, num_threads=MAX_THREADS):
        """
        Bắt đầu các luồng xử lý.
        
        Args:
            num_threads (int): Số lượng luồng cần tạo
        """
        self.stop_event.clear()
        for _ in range(num_threads):
            thread = threading.Thread(target=self.worker, daemon=True)
            thread.start()
            self.threads.append(thread)
    
    def stop(self):
        """
        Dừng tất cả các luồng.
        """
        self.stop_event.set()
        for thread in self.threads:
            thread.join(timeout=1.0)
        self.threads = []
    
    def get_responses(self, block=False, timeout=None):
        """
        Lấy các phản hồi từ hàng đợi.
        
        Args:
            block (bool): Có chặn cho đến khi có phản hồi không
            timeout (float): Thời gian timeout nếu block=True
            
        Returns:
            list: Danh sách các phản hồi
        """
        responses = []
        try:
            while True:
                response = self.response_queue.get(block=block, timeout=timeout)
                responses.append(response)
                self.response_queue.task_done()
                # Nếu không block, chỉ lấy một phản hồi
                if not block:
                    break
        except queue.Empty:
            pass
        
        return responses
    
    def wait_for_completion(self):
        """
        Đợi cho đến khi tất cả các yêu cầu được xử lý.
        """
        self.request_queue.join()
