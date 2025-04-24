"""
Ứng dụng web đơn giản sử dụng Flask và đa luồng với Gemini API.
"""
import os
import time
import threading
import queue
import json
import psutil
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import google.generativeai as genai

# Import cấu hình từ config.py
from config import GEMINI_API_KEY, GEMINI_MODEL, MAX_THREADS, MAX_PROCESSES, REQUEST_TIMEOUT
from process_manager import ProcessManager

import base64
import os
from PIL import Image
import io

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

        # Context prompt mặc định
        self.context_prompt = "bạn là Nemo AI. Một Chat bot AI thân thiện với người dùng hãy sử dụng câu nói thân mật để giao tiếp với người dùng"

        # Tạo thư mục để lưu trữ ảnh tạm thời
        self.temp_image_dir = "static/temp_images"
        os.makedirs(self.temp_image_dir, exist_ok=True)

    def generate_response(self, prompt, image_data=None):
        """
        Gửi prompt đến Gemini API và nhận phản hồi.

        Args:
            prompt (str): Câu hỏi hoặc yêu cầu của người dùng
            image_data (str, optional): Dữ liệu ảnh dạng base64 hoặc đường dẫn đến file ảnh

        Returns:
            str: Phản hồi từ Gemini API
        """
        try:
            # Kết hợp context prompt với câu hỏi của người dùng
            full_prompt = f"{self.context_prompt}\n\nNgười dùng: {prompt}"

            # Nếu có ảnh, xử lý ảnh và gọi API Gemini với ảnh
            if image_data:
                # Xử lý ảnh
                if image_data.startswith('data:image'):
                    # Nếu là base64, chuyển đổi thành ảnh
                    image_data = image_data.split(',')[1]
                    image_bytes = base64.b64decode(image_data)
                    image = Image.open(io.BytesIO(image_bytes))
                elif os.path.isfile(image_data):
                    # Nếu là đường dẫn file, mở file
                    image = Image.open(image_data)
                else:
                    return "Lỗi: Định dạng ảnh không hợp lệ"

                # Tạo đường dẫn tạm thời để lưu ảnh
                timestamp = int(time.time() * 1000)
                temp_image_path = f"{self.temp_image_dir}/temp_{timestamp}.jpg"
                image.save(temp_image_path)

                # Tạo nội dung đa phương thức
                contents = [
                    full_prompt,
                    {"mime_type": "image/jpeg", "data": open(temp_image_path, "rb").read()}
                ]

                # Gọi API Gemini với nội dung đa phương thức
                response = self.model.generate_content(contents)

                # Xóa file ảnh tạm thời sau khi sử dụng
                try:
                    os.remove(temp_image_path)
                except:
                    pass

                return response.text
            else:
                # Gọi API Gemini chỉ với văn bản
                response = self.model.generate_content(full_prompt)
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
        self.responses_dict = {}  # Lưu trữ các phản hồi theo request_id

    def add_request(self, prompt, request_id=None, image_data=None):
        """
        Thêm một yêu cầu vào hàng đợi.

        Args:
            prompt (str): Câu hỏi hoặc yêu cầu của người dùng
            request_id: ID của yêu cầu (nếu có)
            image_data (str, optional): Dữ liệu ảnh dạng base64 hoặc đường dẫn đến file ảnh
        """
        if request_id is None:
            request_id = f"req_{int(time.time() * 1000)}"

        self.request_queue.put((request_id, prompt, image_data))
        return request_id

    def worker(self):
        """
        Hàm xử lý cho mỗi luồng.
        """
        while not self.stop_event.is_set():
            try:
                # Lấy yêu cầu từ hàng đợi với timeout để có thể kiểm tra stop_event
                request_id, prompt, image_data = self.request_queue.get(timeout=0.5)

                print(f"Luồng {threading.current_thread().name} đang xử lý yêu cầu: {request_id}")

                # Ghi lại thời gian bắt đầu và tài nguyên trước khi xử lý
                start_time = time.time()
                start_cpu = psutil.cpu_percent(interval=None)
                start_memory = psutil.Process().memory_info().rss / (1024 * 1024)  # MB

                # Gọi API Gemini với hoặc không có ảnh
                response = self.client.generate_response(prompt, image_data=image_data)

                # Tính toán thời gian và tài nguyên sử dụng
                end_time = time.time()
                end_cpu = psutil.cpu_percent(interval=None)
                end_memory = psutil.Process().memory_info().rss / (1024 * 1024)  # MB

                processing_time = round(end_time - start_time, 2)  # Thời gian xử lý (giây)
                cpu_usage = round((start_cpu + end_cpu) / 2, 1)  # Sử dụng CPU trung bình (%)
                memory_usage = round(end_memory - start_memory, 2)  # Sử dụng bộ nhớ (MB)

                # Tạo thông tin cơ bản về phản hồi
                basic_response = {
                    "id": request_id,
                    "prompt": prompt,
                    "response": response,
                    "thread": threading.current_thread().name,
                    "timestamp": time.strftime("%H:%M:%S"),
                    "has_image": image_data is not None,
                    "imageData": image_data,
                    "performance": {
                        "time": processing_time,
                        "cpu": cpu_usage,
                        "memory": memory_usage
                    }
                }

                # Đưa kết quả vào hàng đợi phản hồi
                self.response_queue.put((request_id, prompt, response))

                # Lưu thông tin cơ bản vào dictionary để theo dõi trạng thái
                self.responses_dict[request_id] = basic_response

                # Thêm nhiệm vụ xử lý vào ProcessManager
                global process_manager
                process_manager.add_task(request_id, prompt, response)

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
                    # Thu thập thông tin về tài nguyên sử dụng khi có lỗi
                    cpu_usage = psutil.cpu_percent(interval=None)
                    memory_usage = psutil.Process().memory_info().rss / (1024 * 1024)  # MB

                    processed_response = {
                        "id": request_id,
                        "prompt": prompt,
                        "response": error_msg,
                        "thread": threading.current_thread().name,
                        "timestamp": time.strftime("%H:%M:%S"),
                        "error": True,
                        "has_image": 'image_data' in locals() and image_data is not None,
                        "imageData": image_data if 'image_data' in locals() else None,
                        "performance": {
                            "time": 0,  # Không có thời gian xử lý do lỗi
                            "cpu": round(cpu_usage, 1),
                            "memory": round(memory_usage, 2)
                        }
                    }
                    self.response_queue.put(processed_response)
                    self.responses_dict[request_id] = processed_response
                    self.request_queue.task_done()

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

    def get_response(self, request_id):
        """
        Lấy phản hồi theo request_id.

        Args:
            request_id (str): ID của yêu cầu

        Returns:
            dict: Phản hồi đã xử lý hoặc None nếu không tìm thấy
        """
        return self.responses_dict.get(request_id)

    def get_raw_response(self, request_id):
        """
        Lấy phản hồi gốc (chưa xử lý) theo request_id.

        Args:
            request_id (str): ID của yêu cầu

        Returns:
            tuple: (request_id, prompt, response) hoặc None nếu không tìm thấy
        """
        for item in list(self.response_queue.queue):
            if isinstance(item, tuple) and len(item) >= 3 and item[0] == request_id:
                return item
        return None

    def get_all_responses(self):
        """
        Lấy tất cả các phản hồi.

        Returns:
            list: Danh sách các phản hồi
        """
        return list(self.responses_dict.values())

    def clear_all_responses(self):
        """
        Xóa tất cả các phản hồi.
        """
        self.responses_dict.clear()

    def wait_for_completion(self):
        """
        Đợi cho đến khi tất cả các yêu cầu được xử lý.
        """
        self.request_queue.join()

# Khởi tạo ứng dụng Flask
app = Flask(__name__)
CORS(app)  # Cho phép cross-origin requests

# Khởi tạo ThreadManager và ProcessManager
thread_manager = ThreadManager()
process_manager = ProcessManager()

# Bắt đầu các luồng và tiến trình
thread_manager.start()
process_manager.start()

print(f"Đã khởi động {MAX_THREADS} luồng và {MAX_PROCESSES} tiến trình")

@app.route('/')
def index():
    """Trang chủ."""
    return render_template('index.html')

@app.route('/api/ask', methods=['POST'])
def ask():
    """API endpoint để gửi câu hỏi và ảnh."""
    data = request.json
    prompt = data.get('prompt')
    image_data = data.get('image')

    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400

    # Tạo một request mới với prompt và ảnh (nếu có)
    request_id = thread_manager.add_request(prompt, image_data=image_data)

    return jsonify({
        "id": request_id,
        "status": "processing",
        "has_image": image_data is not None
    })

@app.route('/api/status/<request_id>', methods=['GET'])
def status(request_id):
    """API endpoint để kiểm tra trạng thái của yêu cầu."""
    # Kiểm tra xem yêu cầu có trong responses_dict không
    basic_response = thread_manager.get_response(request_id)

    if basic_response:
        # Kiểm tra xem có phản hồi đã xử lý từ ProcessManager không
        processed_responses = process_manager.get_processed_responses()

        # Tìm phản hồi đã xử lý với request_id tương ứng
        processed_response = None
        for resp in processed_responses:
            if resp[0] == request_id:
                processed_response = resp
                break

        if processed_response:
            # Nếu có phản hồi đã xử lý, cập nhật thông tin
            req_id, prompt, processed_text, processor_id = processed_response

            # Cập nhật phản hồi với thông tin đã xử lý
            updated_response = basic_response.copy()
            updated_response["response"] = processed_text
            updated_response["processed"] = True
            # Đảm bảo hiển thị nhất quán thông tin tiến trình
            updated_response["processor"] = f"Tiến trình {processor_id}"

            return jsonify({
                "status": "completed",
                "data": updated_response
            })
        else:
            # Nếu chưa có phản hồi đã xử lý, trả về phản hồi cơ bản
            return jsonify({
                "status": "completed",
                "data": basic_response,
                "processing_status": "waiting_for_process"
            })
    else:
        # Kiểm tra xem yêu cầu có đang được xử lý không
        queue_size = thread_manager.request_queue.qsize()
        return jsonify({
            "status": "processing",
            "queue_size": queue_size
        })

@app.route('/api/responses', methods=['GET'])
def responses():
    """API endpoint để lấy tất cả các phản hồi."""
    # Lấy tất cả phản hồi cơ bản từ ThreadManager
    basic_responses = thread_manager.get_all_responses()

    # Lấy tất cả phản hồi đã xử lý từ ProcessManager
    processed_responses = process_manager.get_processed_responses()

    # Tạo dictionary để tra cứu nhanh các phản hồi đã xử lý theo request_id
    processed_dict = {}
    processor_dict = {}
    for resp in processed_responses:
        req_id, _, processed_text, processor_id = resp
        processed_dict[req_id] = processed_text
        processor_dict[req_id] = processor_id

    # Cập nhật phản hồi cơ bản với thông tin đã xử lý (nếu có)
    for response in basic_responses:
        req_id = response["id"]
        if req_id in processed_dict:
            response["response"] = processed_dict[req_id]
            response["processed"] = True
            if req_id in processor_dict:
                # Đảm bảo hiển thị nhất quán thông tin tiến trình
                response["processor"] = f"Tiến trình {processor_dict[req_id]}"

    return jsonify(basic_responses)

@app.route('/api/responses/clear', methods=['POST'])
def clear_responses():
    """API endpoint để xóa tất cả các phản hồi."""
    thread_manager.clear_all_responses()
    # Không cần xóa phản hồi từ ProcessManager vì chúng sẽ tự động bị xóa khi lấy ra
    return jsonify({"status": "success", "message": "Đã xóa tất cả lịch sử chat"})

@app.route('/api/batch', methods=['POST'])
def batch():
    """API endpoint để gửi nhiều câu hỏi cùng lúc."""
    data = request.json
    prompts = data.get('prompts', [])

    if not prompts or not isinstance(prompts, list):
        return jsonify({"error": "Prompts array is required"}), 400

    request_ids = []
    for prompt in prompts:
        request_id = thread_manager.add_request(prompt)
        request_ids.append(request_id)

    return jsonify({
        "ids": request_ids,
        "status": "processing"
    })

if __name__ == '__main__':
    # Tạo thư mục templates nếu chưa tồn tại
    os.makedirs('templates', exist_ok=True)

    try:
        # Chạy ứng dụng Flask
        app.run(debug=True, host='0.0.0.0', port=5000)
    finally:
        # Đảm bảo dừng tất cả các luồng và tiến trình khi ứng dụng kết thúc
        thread_manager.stop()
        process_manager.stop()
        print("Đã dừng tất cả các luồng và tiến trình.")
