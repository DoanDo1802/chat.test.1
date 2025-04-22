"""
Phiên bản đơn giản hơn của ứng dụng Gemini đa luồng.
Phiên bản này chỉ sử dụng đa luồng, không sử dụng đa tiến trình.
"""
import threading
import queue
import time
import os
import google.generativeai as genai

# Import cấu hình từ config.py
from config import GEMINI_API_KEY, GEMINI_MODEL, MAX_THREADS, REQUEST_TIMEOUT

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

    def generate_response(self, prompt):
        """
        Gửi prompt đến Gemini API và nhận phản hồi.

        Args:
            prompt (str): Câu hỏi hoặc yêu cầu của người dùng

        Returns:
            str: Phản hồi từ Gemini API
        """
        try:
            response = self.model.generate_content(prompt, timeout=REQUEST_TIMEOUT)
            return response.text
        except Exception as e:
            return f"Lỗi khi gọi Gemini API: {str(e)}"

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

                print(f"Luồng {threading.current_thread().name} đang xử lý yêu cầu: {request_id}")

                # Gọi API Gemini
                response = self.client.generate_response(prompt)

                # Xử lý phản hồi
                processed_response = self.process_response(prompt, response)

                # Đưa kết quả vào hàng đợi phản hồi
                self.response_queue.put((request_id, prompt, processed_response))

                # Đánh dấu công việc đã hoàn thành
                self.request_queue.task_done()

            except queue.Empty:
                # Hàng đợi trống, tiếp tục vòng lặp
                continue
            except Exception as e:
                # Xử lý lỗi và đưa vào hàng đợi phản hồi
                if 'request_id' in locals() and 'prompt' in locals():
                    error_msg = f"Lỗi xử lý: {str(e)}"
                    print(error_msg)
                    self.response_queue.put((request_id, prompt, error_msg))
                    self.request_queue.task_done()

    def process_response(self, prompt, response):
        """
        Xử lý phản hồi từ Gemini API.

        Args:
            prompt (str): Câu hỏi gốc
            response (str): Phản hồi từ Gemini API

        Returns:
            str: Phản hồi đã được xử lý
        """
        # Thêm thông tin về luồng xử lý
        processed = f"[Xử lý bởi luồng {threading.current_thread().name}]\n\n"

        # Thêm thông tin về câu hỏi
        processed += f"Câu hỏi: {prompt}\n\n"

        # Thêm phản hồi
        processed += f"Trả lời:\n{response}\n"

        # Thêm thời gian xử lý
        processed += f"\n[Hoàn thành lúc: {time.strftime('%H:%M:%S')}]"

        return processed

    def start(self, num_threads=MAX_THREADS):
        """
        Bắt đầu các luồng xử lý.

        Args:
            num_threads (int): Số lượng luồng cần tạo
        """
        self.stop_event.clear()
        for i in range(num_threads):
            thread = threading.Thread(target=self.worker, name=f"Thread-{i+1}", daemon=True)
            thread.start()
            self.threads.append(thread)
            print(f"Đã khởi động luồng {thread.name}")

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

def clear_screen():
    """Xóa màn hình terminal."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """In tiêu đề ứng dụng."""
    print("=" * 80)
    print(" " * 25 + "ỨNG DỤNG GEMINI ĐA LUỒNG")
    print("=" * 80)
    print(f"Số luồng: {MAX_THREADS}")
    print("-" * 80)

def print_response(response_data):
    """
    In phản hồi đã xử lý.

    Args:
        response_data (tuple): Dữ liệu phản hồi (request_id, prompt, response)
    """
    request_id, prompt, response = response_data
    print("\n" + "=" * 80)
    print(f"ID: {request_id}")
    print("-" * 80)
    print(response)
    print("=" * 80 + "\n")

def main():
    """Hàm chính của ứng dụng."""
    # Kiểm tra API key
    if not GEMINI_API_KEY:
        print("Lỗi: GEMINI_API_KEY không được cấu hình!")
        print("Vui lòng tạo file .env với nội dung: GEMINI_API_KEY=your_api_key_here")
        return

    # Khởi tạo thread manager
    thread_manager = ThreadManager()

    # Bắt đầu các luồng
    thread_manager.start()

    try:
        while True:
            clear_screen()
            print_header()

            # Menu chính
            print("\nMENU:")
            print("1. Gửi một câu hỏi")
            print("2. Gửi nhiều câu hỏi cùng lúc")
            print("3. Xem các phản hồi đã xử lý")
            print("4. Thoát")

            choice = input("\nChọn một tùy chọn (1-4): ")

            if choice == "1":
                # Gửi một câu hỏi
                prompt = input("\nNhập câu hỏi của bạn: ")
                if prompt:
                    print("\nĐang xử lý yêu cầu...")
                    request_id = thread_manager.add_request(prompt)
                    print(f"Đã thêm yêu cầu với ID: {request_id}")

                    # Đợi phản hồi
                    thread_manager.wait_for_completion()

                    # Lấy và hiển thị phản hồi
                    responses = thread_manager.get_responses()
                    for response_data in responses:
                        print_response(response_data)

                input("\nNhấn Enter để tiếp tục...")

            elif choice == "2":
                # Gửi nhiều câu hỏi cùng lúc
                num_questions = input("\nNhập số lượng câu hỏi: ")
                try:
                    num_questions = int(num_questions)
                    if num_questions <= 0:
                        raise ValueError("Số lượng câu hỏi phải lớn hơn 0")

                    questions = []
                    for i in range(num_questions):
                        prompt = input(f"\nNhập câu hỏi {i+1}: ")
                        if prompt:
                            questions.append(prompt)

                    if questions:
                        print("\nĐang xử lý các yêu cầu...")

                        # Thêm tất cả câu hỏi vào hàng đợi
                        request_ids = []
                        for prompt in questions:
                            request_id = thread_manager.add_request(prompt)
                            request_ids.append(request_id)
                            print(f"Đã thêm yêu cầu với ID: {request_id}")

                        # Đợi tất cả phản hồi
                        thread_manager.wait_for_completion()

                        # Lấy và hiển thị phản hồi
                        responses = thread_manager.get_responses()
                        for response_data in responses:
                            print_response(response_data)

                except ValueError as e:
                    print(f"\nLỗi: {str(e)}")

                input("\nNhấn Enter để tiếp tục...")

            elif choice == "3":
                # Xem các phản hồi đã xử lý
                print("\nĐang kiểm tra phản hồi mới...")

                # Lấy và hiển thị phản hồi
                responses = thread_manager.get_responses()

                if responses:
                    for response_data in responses:
                        print_response(response_data)
                else:
                    print("\nKhông có phản hồi mới.")

                input("\nNhấn Enter để tiếp tục...")

            elif choice == "4":
                # Thoát
                print("\nĐang dừng ứng dụng...")
                break

            else:
                print("\nTùy chọn không hợp lệ!")
                input("\nNhấn Enter để tiếp tục...")

    finally:
        # Dừng các luồng
        thread_manager.stop()
        print("\nĐã dừng tất cả các luồng.")
        print("Cảm ơn bạn đã sử dụng ứng dụng!")

if __name__ == "__main__":
    main()
