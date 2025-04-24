"""
Module quản lý đa tiến trình để xử lý dữ liệu từ Gemini API.
"""
import multiprocessing as mp
from config import MAX_PROCESSES
import time
import os
import queue

# Đặt phương thức khởi tạo tiến trình cho macOS
if os.name != 'nt':  # Không phải Windows
    mp.set_start_method('fork', force=True)

class ProcessManager:
    """
    Quản lý các tiến trình để xử lý dữ liệu từ Gemini API.
    """
    def __init__(self):
        """
        Khởi tạo ProcessManager với các hàng đợi và danh sách tiến trình.
        """
        # Sử dụng Manager để tạo các hàng đợi có thể chia sẻ giữa các tiến trình
        self.manager = mp.Manager()
        self.input_queue = self.manager.Queue()
        self.output_queue = self.manager.Queue()
        self.processes = []

    @staticmethod
    def post_processor(input_queue, output_queue, processor_id):
        """
        Hàm xử lý cho mỗi tiến trình.

        Args:
            input_queue: Hàng đợi đầu vào
            output_queue: Hàng đợi đầu ra
            processor_id (int): ID của tiến trình
        """
        print(f"Tiến trình {processor_id} đã bắt đầu")

        while True:
            try:
                # Lấy dữ liệu từ hàng đợi đầu vào
                data = input_queue.get(timeout=1.0)

                # Kiểm tra tín hiệu dừng
                if data == "STOP":
                    print(f"Tiến trình {processor_id} nhận tín hiệu dừng")
                    break

                # Giải nén dữ liệu
                request_id, prompt, response = data

                # Xử lý dữ liệu (ví dụ: định dạng, phân tích, v.v.)
                processed_response = ProcessManager.process_response(prompt, response, processor_id)

                # Đưa kết quả đã xử lý vào hàng đợi đầu ra
                # Thông tin tiến trình được truyền qua processor_id
                output_queue.put((request_id, prompt, processed_response, processor_id))

            except queue.Empty:
                # Hàng đợi trống, tiếp tục vòng lặp
                continue
            except Exception as e:
                # Xử lý lỗi
                print(f"Lỗi trong tiến trình {processor_id}: {str(e)}")

        print(f"Tiến trình {processor_id} đã kết thúc")

    @staticmethod
    def process_response(prompt, response, processor_id):
        """
        Xử lý phản hồi từ Gemini API.

        Args:
            prompt (str): Câu hỏi gốc
            response (str): Phản hồi từ Gemini API
            processor_id (int): ID của tiến trình xử lý

        Returns:
            str: Phản hồi đã được xử lý
        """
        # Mô phỏng xử lý nặng bằng cách ngủ một chút
        time.sleep(0.2)

        # Thêm thông tin về câu hỏi
        processed = f"Câu hỏi: {prompt}\n\n"

        # Thêm phản hồi (không thêm "Trả lời:" để tránh trùng lặp)
        processed += f"{response}"

        # Thông tin về tiến trình xử lý được chuyển xuống phần chữ nhỏ phía dưới
        # sẽ được xử lý trong app.py

        return processed

    def start(self, num_processes=MAX_PROCESSES):
        """
        Bắt đầu các tiến trình xử lý.

        Args:
            num_processes (int): Số lượng tiến trình cần tạo
        """
        for i in range(num_processes):
            process = mp.Process(
                target=ProcessManager.post_processor,
                args=(self.input_queue, self.output_queue, i)
            )
            process.daemon = True
            process.start()
            self.processes.append(process)

    def stop(self):
        """
        Dừng tất cả các tiến trình.
        """
        # Gửi tín hiệu dừng đến tất cả các tiến trình
        for _ in range(len(self.processes)):
            self.input_queue.put("STOP")

        # Đợi tất cả các tiến trình kết thúc
        for process in self.processes:
            process.join(timeout=2.0)
            if process.is_alive():
                process.terminate()

        self.processes = []

    def add_task(self, request_id, prompt, response):
        """
        Thêm một nhiệm vụ xử lý vào hàng đợi.

        Args:
            request_id: ID của yêu cầu
            prompt (str): Câu hỏi gốc
            response (str): Phản hồi từ Gemini API
        """
        self.input_queue.put((request_id, prompt, response))

    def get_processed_responses(self):
        """
        Lấy các phản hồi đã xử lý từ hàng đợi đầu ra.

        Returns:
            list: Danh sách các phản hồi đã xử lý
        """
        responses = []
        while not self.output_queue.empty():
            # Lấy dữ liệu từ hàng đợi (request_id, prompt, processed_response, processor_id)
            data = self.output_queue.get()

            # Trả về toàn bộ dữ liệu bao gồm processor_id
            responses.append(data)

        return responses
