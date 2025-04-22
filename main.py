"""
Ứng dụng chính sử dụng đa luồng và đa tiến trình với Gemini API.
"""
import time
import os
from dotenv import load_dotenv
from thread_manager import ThreadManager
from process_manager import ProcessManager
from config import MAX_THREADS, MAX_PROCESSES

def clear_screen():
    """Xóa màn hình terminal."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """In tiêu đề ứng dụng."""
    print("=" * 80)
    print(" " * 25 + "ỨNG DỤNG GEMINI ĐA LUỒNG & ĐA TIẾN TRÌNH")
    print("=" * 80)
    print(f"Số luồng: {MAX_THREADS} | Số tiến trình: {MAX_PROCESSES}")
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
    # Tải biến môi trường
    load_dotenv()
    
    # Kiểm tra API key
    if not os.getenv("GEMINI_API_KEY"):
        print("Lỗi: GEMINI_API_KEY không được cấu hình!")
        print("Vui lòng tạo file .env với nội dung: GEMINI_API_KEY=your_api_key_here")
        return
    
    # Khởi tạo các manager
    thread_manager = ThreadManager()
    process_manager = ProcessManager()
    
    # Bắt đầu các luồng và tiến trình
    thread_manager.start()
    process_manager.start()
    
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
                    
                    # Lấy phản hồi
                    responses = thread_manager.get_responses()
                    
                    # Xử lý phản hồi bằng tiến trình
                    for response_data in responses:
                        process_manager.add_task(*response_data)
                    
                    # Đợi một chút để tiến trình xử lý
                    time.sleep(1)
                    
                    # Lấy và hiển thị phản hồi đã xử lý
                    processed_responses = process_manager.get_processed_responses()
                    for response_data in processed_responses:
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
                        
                        # Lấy phản hồi
                        responses = thread_manager.get_responses()
                        
                        # Xử lý phản hồi bằng tiến trình
                        for response_data in responses:
                            process_manager.add_task(*response_data)
                        
                        # Đợi một chút để tiến trình xử lý
                        time.sleep(2)
                        
                        # Lấy và hiển thị phản hồi đã xử lý
                        processed_responses = process_manager.get_processed_responses()
                        for response_data in processed_responses:
                            print_response(response_data)
                
                except ValueError as e:
                    print(f"\nLỗi: {str(e)}")
                
                input("\nNhấn Enter để tiếp tục...")
            
            elif choice == "3":
                # Xem các phản hồi đã xử lý
                print("\nĐang kiểm tra phản hồi mới...")
                
                # Lấy phản hồi từ thread manager
                responses = thread_manager.get_responses()
                
                # Xử lý phản hồi bằng tiến trình
                for response_data in responses:
                    process_manager.add_task(*response_data)
                
                # Đợi một chút để tiến trình xử lý
                time.sleep(1)
                
                # Lấy và hiển thị phản hồi đã xử lý
                processed_responses = process_manager.get_processed_responses()
                
                if processed_responses:
                    for response_data in processed_responses:
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
        # Dừng các luồng và tiến trình
        thread_manager.stop()
        process_manager.stop()
        print("\nĐã dừng tất cả các luồng và tiến trình.")
        print("Cảm ơn bạn đã sử dụng ứng dụng!")

if __name__ == "__main__":
    main()
