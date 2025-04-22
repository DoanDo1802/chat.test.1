// Biến toàn cục để theo dõi các yêu cầu đang xử lý
const pendingRequests = new Set();
const chatMessages = [];

// Biến lưu trữ dữ liệu ảnh hiện tại
let currentImageData = null;

// Hàm để gửi một câu hỏi
async function askQuestion(prompt, imageData = null) {
    try {
        // Hiển thị tin nhắn người dùng ngay lập tức
        addUserMessage(prompt, imageData);

        // Hiển thị trạng thái đang nhập
        showTypingIndicator();

        // Tạo body request
        const requestBody = { prompt };

        // Thêm ảnh nếu có
        if (imageData) {
            requestBody.image = imageData;
        }

        const response = await fetch('/api/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });

        const data = await response.json();

        if (data.id) {
            pendingRequests.add(data.id);
            pollStatus(data.id);
            return data.id;
        }
    } catch (error) {
        console.error('Error asking question:', error);
        hideTypingIndicator();
        addBotMessage("Đã xảy ra lỗi khi gửi tin nhắn. Vui lòng thử lại.");
    }
    return null;
}

// Hàm để kiểm tra trạng thái của một yêu cầu
async function checkStatus(requestId) {
    try {
        const response = await fetch(`/api/status/${requestId}`);
        return await response.json();
    } catch (error) {
        console.error('Error checking status:', error);
        return { status: 'error' };
    }
}

// Hàm để lấy tất cả các phản hồi
async function getAllResponses() {
    try {
        const response = await fetch('/api/responses');
        return await response.json();
    } catch (error) {
        console.error('Error getting responses:', error);
        return [];
    }
}

// Hàm để liên tục kiểm tra trạng thái của một yêu cầu
function pollStatus(requestId) {
    const interval = setInterval(async () => {
        const statusData = await checkStatus(requestId);

        if (statusData.status === 'completed') {
            clearInterval(interval);
            pendingRequests.delete(requestId);

            // Ẩn trạng thái đang nhập
            hideTypingIndicator();

            // Hiển thị phản hồi từ bot
            addBotMessage(statusData.data.response, statusData.data);
        }
    }, 1000);
}

// Hiển thị trạng thái đang nhập
function showTypingIndicator() {
    // Kiểm tra xem đã có indicator chưa
    if (document.getElementById('typing-indicator')) {
        document.getElementById('typing-indicator').remove();
    }

    // Tạo một indicator mới
    const indicatorHtml = `
        <div class="typing-indicator" id="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;

    const chatContainer = document.getElementById('chat-messages');
    chatContainer.insertAdjacentHTML('afterbegin', indicatorHtml);
}

// Ẩn trạng thái đang nhập
function hideTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
        indicator.remove();
    }
}

// Thêm tin nhắn người dùng vào khung chat
function addUserMessage(message, imageData = null) {
    const timestamp = new Date().toLocaleTimeString();

    // Tạo phần hiển thị ảnh nếu có
    let imageHtml = '';
    if (imageData) {
        imageHtml = `
            <div class="message-image">
                <img src="${imageData}" alt="Ảnh đính kèm" class="attached-image">
            </div>
        `;
    }

    const messageHtml = `
        <div class="message message-user">
            <div class="message-content">${message}</div>
            ${imageHtml}
            <div class="message-time">${timestamp}</div>
        </div>
    `;

    const chatContainer = document.getElementById('chat-messages');
    chatContainer.insertAdjacentHTML('afterbegin', messageHtml);

    // Lưu tin nhắn vào mảng
    chatMessages.unshift({
        type: 'user',
        content: message,
        timestamp: timestamp,
        imageData: imageData
    });
}

// Thêm tin nhắn bot vào khung chat
function addBotMessage(message, responseData = null) {
    const timestamp = new Date().toLocaleTimeString();
    let threadInfo = '';

    if (responseData) {
        let performanceInfo = '';
        if (responseData.performance) {
            performanceInfo = ` | Thời gian: ${responseData.performance.time}s | CPU: ${responseData.performance.cpu}% | RAM: ${responseData.performance.memory}MB`;
        }
        threadInfo = `<div class="thread-info">ID: ${responseData.id} | Xử lý bởi: ${responseData.thread}${performanceInfo}</div>`;
    }

    const messageHtml = `
        <div class="message message-bot">
            <div class="message-content">${marked.parse(message)}</div>
            ${threadInfo}
            <div class="message-time">${timestamp}</div>
        </div>
    `;

    const chatContainer = document.getElementById('chat-messages');
    chatContainer.insertAdjacentHTML('afterbegin', messageHtml);

    // Lưu tin nhắn vào mảng
    chatMessages.unshift({
        type: 'bot',
        content: message,
        timestamp: timestamp,
        responseData: responseData
    });
}

// Hàm để hiển thị modal lịch sử chat
async function showHistoryModal() {
    // Hiển thị modal
    const historyModal = new bootstrap.Modal(document.getElementById('historyModal'));
    historyModal.show();

    // Lấy và hiển thị lịch sử chat
    await loadHistoryToModal();
}

// Hàm để xóa tất cả lịch sử chat
async function clearAllHistory() {
    try {
        const response = await fetch('/api/responses/clear', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();

        if (result.status === 'success') {
            // Xóa nội dung trong modal
            const historyContainer = document.getElementById('history-container');
            historyContainer.innerHTML = `
                <div class="alert alert-success">
                    ${result.message}
                </div>
                <div class="alert alert-info">
                    Chưa có lịch sử cuộc trò chuyện nào.
                </div>
            `;
        }
    } catch (error) {
        console.error('Error clearing history:', error);
    }
}

// Hàm để tải lịch sử chat vào modal
async function loadHistoryToModal() {
    const responses = await getAllResponses();

    if (responses.length === 0) {
        // Nếu không có tin nhắn nào, hiển thị thông báo
        const historyContainer = document.getElementById('history-container');
        historyContainer.innerHTML = `
            <div class="alert alert-info">
                Chưa có lịch sử cuộc trò chuyện nào.
            </div>
        `;
        return;
    }

    // Xóa nội dung cũ trong modal
    const historyContainer = document.getElementById('history-container');
    historyContainer.innerHTML = `
        <div class="text-center py-5">
            <div class="loading"></div>
            <p class="mt-2">Đang tải lịch sử cuộc trò chuyện...</p>
        </div>
    `;

    // Sắp xếp các phản hồi theo thời gian (mới nhất lên đầu)
    responses.sort((a, b) => b.id.localeCompare(a.id));

    // Tạo HTML cho lịch sử chat
    let historyHTML = '';

    if (responses.length === 0) {
        historyHTML = `
            <div class="alert alert-info">
                Chưa có lịch sử cuộc trò chuyện nào.
            </div>
        `;
    } else {
        responses.forEach(response => {
            historyHTML += `
                <div class="card mb-3">
                    <div class="card-header d-flex justify-content-between">
                        <div>ID: ${response.id}</div>
                        <div class="text-muted small">${response.timestamp}</div>
                    </div>
                    <div class="card-body">
                        <h6 class="card-subtitle mb-2 text-muted">
                            Xử lý bởi: ${response.thread}
                            ${response.performance ? ` | Thời gian: ${response.performance.time}s | CPU: ${response.performance.cpu}% | RAM: ${response.performance.memory}MB` : ''}
                        </h6>
                        <h5 class="card-title">Câu hỏi:</h5>
                        <p class="card-text">${response.prompt}</p>
                        ${response.has_image && response.imageData ? `
                        <div class="history-image-container">
                            <img src="${response.imageData}" alt="Ảnh đính kèm" class="history-image">
                        </div>` : ''}
                        <h5 class="card-title">Trả lời:</h5>
                        <div class="card-text">${marked.parse(response.response)}</div>
                    </div>
                    <div class="card-footer">
                        <button class="btn btn-sm btn-primary load-conversation" data-id="${response.id}">
                            <i class="fas fa-comment"></i> Tải vào cuộc trò chuyện
                        </button>
                    </div>
                </div>
            `;
        });
    }

    // Hiển thị lịch sử chat trong modal
    historyContainer.innerHTML = historyHTML;

    // Thêm sự kiện cho các nút "Tải vào cuộc trò chuyện"
    document.querySelectorAll('.load-conversation').forEach(button => {
        button.addEventListener('click', function() {
            const responseId = this.getAttribute('data-id');
            loadConversationFromHistory(responseId, responses);
            // Đóng modal
            bootstrap.Modal.getInstance(document.getElementById('historyModal')).hide();
        });
    });
}

// Hàm để tải cuộc trò chuyện từ lịch sử
function loadConversationFromHistory(responseId, responses) {
    // Tìm phản hồi theo ID
    const response = responses.find(r => r.id === responseId);
    if (!response) return;

    // Xóa cuộc trò chuyện hiện tại
    clearChat(false); // false = không hiển thị tin nhắn chào mừng

    // Thêm tin nhắn người dùng và phản hồi vào cuộc trò chuyện
    const imageData = response.has_image && response.imageData ? response.imageData : null;
    addUserMessage(response.prompt, imageData);
    addBotMessage(response.response, response);
}

// Xóa lịch sử chat
function clearChat(showWelcomeMessage = true) {
    document.getElementById('chat-messages').innerHTML = '';
    chatMessages.length = 0;

    // Hiển thị tin nhắn chào mừng nếu cần
    if (showWelcomeMessage) {
        addBotMessage("Lịch sử chat đã được xóa. Bạn có thể bắt đầu cuộc trò chuyện mới!");
    }
}



// Hàm gửi tin nhắn
async function sendMessage() {
    const promptInput = document.getElementById('prompt');
    const prompt = promptInput.value.trim();

    if (prompt) {
        document.getElementById('submit-btn').disabled = true;
        promptInput.value = '';
        promptInput.style.height = 'auto';

        // Gửi câu hỏi với hoặc không có ảnh
        await askQuestion(prompt, currentImageData);

        // Xóa ảnh sau khi gửi
        if (currentImageData) {
            removeImage();
        }

        document.getElementById('submit-btn').disabled = false;
        promptInput.focus();
    }
}

// Hàm để xử lý tải lên ảnh
function handleImageUpload() {
    const input = document.getElementById('image-upload');
    input.click();
}

// Hàm để hiển thị ảnh đã chọn
function displaySelectedImage(file) {
    const reader = new FileReader();
    reader.onload = function(e) {
        currentImageData = e.target.result;
        document.getElementById('image-preview').src = e.target.result;
        document.getElementById('image-preview-container').classList.remove('d-none');
    };
    reader.readAsDataURL(file);
}

// Hàm để xóa ảnh đã chọn
function removeImage() {
    currentImageData = null;
    document.getElementById('image-preview').src = '#';
    document.getElementById('image-preview-container').classList.add('d-none');
    document.getElementById('image-upload').value = '';
}

// Hàm để xử lý paste ảnh
function handlePaste(e) {
    // Kiểm tra xem có dữ liệu ảnh trong clipboard không
    const items = (e.clipboardData || e.originalEvent.clipboardData).items;

    for (let i = 0; i < items.length; i++) {
        if (items[i].type.indexOf('image') !== -1) {
            // Lấy file ảnh từ clipboard
            const blob = items[i].getAsFile();
            // Hiển thị ảnh đã paste
            displaySelectedImage(blob);
            // Ngăn chặn hành vi paste mặc định
            e.preventDefault();
            break;
        }
    }
}

// Xử lý sự kiện khi trang được tải
document.addEventListener('DOMContentLoaded', () => {
    // Xử lý sự kiện gửi tin nhắn
    document.getElementById('submit-btn').addEventListener('click', sendMessage);

    // Xử lý sự kiện nhấn Enter để gửi tin nhắn
    document.getElementById('prompt').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Xử lý sự kiện xem lịch sử chat
    document.getElementById('history-btn').addEventListener('click', showHistoryModal);

    // Xử lý sự kiện xóa chat hiện tại
    document.getElementById('clear-chat-btn').addEventListener('click', () => clearChat(true));

    // Xử lý sự kiện xóa tất cả lịch sử chat
    document.addEventListener('click', function(e) {
        if (e.target && e.target.id === 'clear-history-btn' ||
            (e.target.parentElement && e.target.parentElement.id === 'clear-history-btn')) {
            // Hiển thị hộp thoại xác nhận
            if (confirm('Bạn có chắc chắn muốn xóa tất cả lịch sử chat?')) {
                clearAllHistory();
            }
        }
    });

    // Tự động điều chỉnh chiều cao của textarea
    const promptInput = document.getElementById('prompt');
    promptInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });

    // Xử lý sự kiện tải lên ảnh
    document.getElementById('image-btn').addEventListener('click', handleImageUpload);

    // Xử lý sự kiện khi chọn file ảnh
    document.getElementById('image-upload').addEventListener('change', function() {
        if (this.files && this.files[0]) {
            displaySelectedImage(this.files[0]);
        }
    });

    // Xử lý sự kiện xóa ảnh
    document.getElementById('remove-image-btn').addEventListener('click', removeImage);

    // Xử lý sự kiện paste ảnh
    document.addEventListener('paste', handlePaste);

    // Hiển thị tin nhắn chào mừng khi trang được tải
    addBotMessage("Xin chào! Tôi là Nemo AI. Bạn có thể hỏi tôi bất cứ điều gì.");
});
