# Hướng Dẫn Sử Dụng Ứng Dụng Gemini Đa Luồng & Đa Tiến Trình với Xử lý Ảnh

## Giới Thiệu

Ứng dụng này là một giải pháp tiên tiến sử dụng kỹ thuật đa luồng (multithreading) và đa tiến trình (multiprocessing) để tương tác hiệu quả với Gemini API của Google. Ứng dụng cung cấp khả năng xử lý nhiều yêu cầu đồng thời, tối ưu hóa thời gian phản hồi và tận dụng tối đa tài nguyên hệ thống.

Ứng dụng hỗ trợ xử lý ảnh với Gemini API, cho phép người dùng tải lên hoặc dán ảnh vào cuộc trò chuyện. Đặc biệt, ứng dụng còn cung cấp các chỉ số hiệu suất chi tiết như thời gian xử lý, sử dụng CPU và bộ nhớ cho mỗi yêu cầu, giúp người dùng theo dõi và tối ưu hóa hiệu suất hệ thống.

## Lợi Ích Của Đa Luồng & Đa Tiến Trình

### Đa Luồng (Multithreading)
- **Xử lý đồng thời**: Cho phép gửi nhiều yêu cầu cùng lúc đến Gemini API
- **Tối ưu thời gian chờ**: Trong khi một luồng đang chờ phản hồi từ API, các luồng khác vẫn có thể hoạt động
- **Tăng hiệu suất I/O**: Lý tưởng cho các tác vụ bị giới hạn bởi I/O như gọi API

### Đa Tiến Trình (Multiprocessing)
- **Tận dụng nhiều CPU**: Phân phối tải xử lý trên nhiều lõi CPU
- **Xử lý song song thực sự**: Vượt qua giới hạn GIL (Global Interpreter Lock) của Python
- **Cô lập tài nguyên**: Mỗi tiến trình có không gian bộ nhớ riêng, tăng tính ổn định

## Kiến Trúc Hệ Thống

Ứng dụng được thiết kế theo mô hình module hóa với các thành phần chính:

1. **ThreadManager**: Quản lý các luồng để gửi yêu cầu đến Gemini API
   - Sử dụng hàng đợi (queue) để phân phối công việc giữa các luồng
   - Mỗi luồng xử lý một yêu cầu độc lập
   - Tự động mở rộng/thu hẹp số lượng luồng theo cấu hình

2. **ProcessManager**: Quản lý các tiến trình để xử lý dữ liệu phản hồi
   - Sử dụng các tiến trình riêng biệt để xử lý dữ liệu
   - Tận dụng tối đa sức mạnh đa lõi của CPU
   - Giao tiếp giữa các tiến trình thông qua hàng đợi được chia sẻ

3. **GeminiClient**: Giao tiếp với Gemini API
   - Xử lý việc gửi yêu cầu và nhận phản hồi
   - Quản lý lỗi và timeout
   - Định dạng dữ liệu phù hợp

4. **Giao Diện Web**: Cung cấp trải nghiệm người dùng trực quan
   - Giao diện thân thiện với người dùng dạng chat
   - Hỗ trợ tải lên và dán ảnh trực tiếp vào cuộc trò chuyện
   - Hiển thị kết quả theo thời gian thực
   - Hiển thị thông tin về tài nguyên sử dụng (CPU, RAM, thời gian xử lý)
   - Lưu trữ và hiển thị lịch sử cuộc trò chuyện

## Cách Sử Dụng

### Cài Đặt

1. Clone repository:
```
git clone <repository-url>
cd <repository-folder>
```

2. Cài đặt các thư viện cần thiết:
```
pip install -r requirements.txt
pip install psutil  # Cho tính năng theo dõi tài nguyên
```

3. Tạo file `.env` và thêm API key của Gemini:
```
GEMINI_API_KEY=your_gemini_api_key_here
```

### Chạy Ứng Dụng

#### Phiên Bản Web
```
python app.py
```
Sau đó truy cập `http://localhost:5000` trên trình duyệt.

#### Phiên Bản Dòng Lệnh Đầy Đủ
```
python main.py
```

#### Phiên Bản Đơn Giản (Chỉ Đa Luồng)
```
python simple_main.py
```

### Tùy Chỉnh Cấu Hình

Bạn có thể tùy chỉnh các thông số trong file `config.py`:

- `MAX_THREADS`: Số lượng luồng tối đa (mặc định: 5)
- `MAX_PROCESSES`: Số lượng tiến trình tối đa (mặc định: 3)
- `REQUEST_TIMEOUT`: Thời gian timeout cho mỗi yêu cầu (mặc định: 30 giây)
- `GEMINI_MODEL`: Mô hình Gemini được sử dụng (mặc định: "gemini-1.5-pro")

## Hiệu Suất & Tối Ưu Hóa

### Theo Dõi Tài Nguyên
Ứng dụng bao gồm các công cụ theo dõi hiệu suất để giám sát:
- Thời gian xử lý cho mỗi yêu cầu (hiển thị bằng giây)
- Sử dụng CPU (hiển thị bằng phần trăm)
- Sử dụng bộ nhớ RAM (hiển thị bằng MB)
- Thông tin về luồng xử lý

Các thông tin này được hiển thị trực tiếp trong giao diện người dùng của ứng dụng, giúp người dùng theo dõi hiệu suất và tài nguyên sử dụng trong thời gian thực.

### Mẹo Tối Ưu Hóa
- **Điều chỉnh số luồng**: Tăng `MAX_THREADS` nếu tác vụ chủ yếu là I/O-bound
- **Điều chỉnh số tiến trình**: Tăng `MAX_PROCESSES` nếu có nhiều lõi CPU và tác vụ xử lý nặng
- **Cân bằng tài nguyên**: Tổng số luồng và tiến trình không nên vượt quá gấp đôi số lõi CPU

## Ví Dụ Sử Dụng

### Xử Lý Đơn Yêu Cầu
```python
from thread_manager import ThreadManager

# Khởi tạo thread manager
thread_manager = ThreadManager()
thread_manager.start()

# Thêm yêu cầu
request_id = thread_manager.add_request("Hãy giải thích về trí tuệ nhân tạo")

# Đợi hoàn thành
thread_manager.wait_for_completion()

# Lấy kết quả
responses = thread_manager.get_responses()
for response_data in responses:
    print(response_data)

# Dừng thread manager
thread_manager.stop()
```

### Xử Lý Nhiều Yêu Cầu Đồng Thời
```python
from thread_manager import ThreadManager
from process_manager import ProcessManager
import time

# Khởi tạo managers
thread_manager = ThreadManager()
process_manager = ProcessManager()

# Bắt đầu
thread_manager.start()
process_manager.start()

# Thêm nhiều yêu cầu
questions = [
    "Hãy giải thích về đa luồng trong Python",
    "Hãy giải thích về đa tiến trình trong Python",
    "So sánh đa luồng và đa tiến trình"
]

request_ids = []
for prompt in questions:
    request_id = thread_manager.add_request(prompt)
    request_ids.append(request_id)

# Đợi hoàn thành
thread_manager.wait_for_completion()

# Lấy phản hồi
responses = thread_manager.get_responses()

# Xử lý phản hồi bằng tiến trình
for response_data in responses:
    process_manager.add_task(*response_data)

# Đợi tiến trình xử lý
time.sleep(2)

# Lấy kết quả đã xử lý
processed_responses = process_manager.get_processed_responses()
for response_data in processed_responses:
    print(response_data)

# Dừng managers
thread_manager.stop()
process_manager.stop()
```

## Xử Lý Lỗi & Khắc Phục Sự Cố

### Các Lỗi Thường Gặp

1. **API Key Không Hợp Lệ**
   - Kiểm tra file `.env` và đảm bảo `GEMINI_API_KEY` được cấu hình đúng

2. **Quá Nhiều Yêu Cầu**
   - Giảm `MAX_THREADS` để tránh vượt quá giới hạn API

3. **Tiêu Thụ Bộ Nhớ Cao**
   - Giảm `MAX_PROCESSES` nếu ứng dụng sử dụng quá nhiều RAM

4. **Timeout Khi Gọi API**
   - Tăng `REQUEST_TIMEOUT` trong `config.py`

## Tính Năng Xử Lý Ảnh

Ứng dụng hỗ trợ xử lý ảnh với Gemini API, cho phép người dùng:

- Tải lên ảnh từ máy tính
- Dán ảnh trực tiếp từ clipboard (copy-paste)
- Gửi ảnh kèm với câu hỏi đến Gemini API
- Xem lại ảnh trong lịch sử cuộc trò chuyện

## Theo Dõi Hiệu Suất

Ứng dụng cung cấp các chỉ số hiệu suất chi tiết cho mỗi yêu cầu:

- **Thời gian xử lý**: Đo thời gian cần thiết để xử lý mỗi yêu cầu (giây)
- **Sử dụng CPU**: Đo mức sử dụng CPU trung bình trong quá trình xử lý (%)
- **Sử dụng RAM**: Đo lượng bộ nhớ được sử dụng cho mỗi yêu cầu (MB)
- **Thông tin luồng**: Hiển thị luồng nào đã xử lý yêu cầu

Các thông tin này được hiển thị trực tiếp trong giao diện người dùng, giúp theo dõi và tối ưu hóa hiệu suất hệ thống.

## Kết Luận

Ứng dụng Gemini Đa Luồng & Đa Tiến Trình với Xử lý Ảnh cung cấp một giải pháp mạnh mẽ để tương tác với Gemini API, tận dụng tối đa sức mạnh của kỹ thuật lập trình đồng thời. Bằng cách kết hợp đa luồng, đa tiến trình, xử lý ảnh và theo dõi tài nguyên, ứng dụng đạt được hiệu suất tối ưu và khả năng mở rộng cao, phù hợp cho cả ứng dụng cá nhân và doanh nghiệp.
