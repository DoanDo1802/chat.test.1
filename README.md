# Ứng dụng Gemini Đa luồng với Giao diện Web

Đây là một ứng dụng Python sử dụng đa luồng (multithreading) để tương tác với Gemini API của Google và cung cấp giao diện web đơn giản.

## Tính năng

- Sử dụng đa luồng để gửi nhiều yêu cầu đồng thời đến Gemini API
- Giao diện web đơn giản và thân thiện với người dùng
- Xem lịch sử các phản hồi

## Cài đặt

1. Clone repository này:
```
git clone <repository-url>
cd <repository-folder>
```

2. Cài đặt các thư viện cần thiết:
```
pip install -r requirements.txt
```

3. Tạo file `.env` từ file `.env.example` và thêm API key của Gemini:
```
cp .env.example .env
```

4. Mở file `.env` và thêm API key của bạn:
```
GEMINI_API_KEY=your_gemini_api_key_here
```

## Cách sử dụng

1. Chạy ứng dụng web:
```
python app.py
```

2. Mở trình duyệt và truy cập:
```
http://localhost:5000
```

3. Sử dụng giao diện web để:
   - Gửi một câu hỏi đơn lẻ
   - Xem lịch sử các phản hồi

4. Nếu muốn sử dụng phiên bản giao diện dòng lệnh:
```
python main.py
```

hoặc phiên bản đơn giản hơn chỉ sử dụng đa luồng:
```
python simple_main.py
```

## Cấu trúc dự án

- `app.py`: File chính để chạy ứng dụng web
- `templates/index.html`: Giao diện web
- `main.py`: Phiên bản giao diện dòng lệnh đầy đủ
- `simple_main.py`: Phiên bản đơn giản chỉ sử dụng đa luồng
- `gemini_client.py`: Chứa lớp để tương tác với API Gemini
- `thread_manager.py`: Quản lý đa luồng
- `process_manager.py`: Quản lý đa tiến trình
- `config.py`: Cấu hình API key và các thông số khác
- `requirements.txt`: Các thư viện cần thiết

## Tùy chỉnh

Bạn có thể tùy chỉnh các thông số trong file `config.py`:
- `MAX_THREADS`: Số lượng luồng tối đa
- `MAX_PROCESSES`: Số lượng tiến trình tối đa
- `REQUEST_TIMEOUT`: Thời gian timeout cho mỗi request
- `GEMINI_MODEL`: Mô hình Gemini muốn sử dụng

## Yêu cầu

- Python 3.7 trở lên
- API key của Gemini (đăng ký tại https://ai.google.dev/)
- Các thư viện: cập nhật trong requirements.txt 

