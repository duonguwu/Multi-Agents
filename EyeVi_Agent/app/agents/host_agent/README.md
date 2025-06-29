# Host Agent - Orchestrator Agent với A2A Protocol

Host Agent là agent chính trong hệ thống Multi-Agent, sử dụng A2A (Agent-to-Agent) protocol để giao tiếp. Có nhiệm vụ nhận message từ user, phân tích và điều phối tới các agent chuyên biệt (Advisor, Search, Order Agent).

## 🎯 Chức Năng Chính

- **Phân tích yêu cầu**: Sử dụng LangChain + Google Gemini để hiểu và phân loại yêu cầu từ user
- **Điều phối thông minh**: Tự động chọn agent phù hợp để xử lý yêu cầu
- **A2A Communication**: Sử dụng A2A protocol để giao tiếp với các agent khác
- **File Upload Support**: Hỗ trợ upload và xử lý files (ảnh, document) kèm theo message
- **Chat History Management**: Lưu trữ và quản lý lịch sử hội thoại theo session
- **Context Awareness**: Duy trì context qua các cuộc hội thoại để tư vấn hiệu quả hơn

## 🏗️ Kiến Trúc
![Kiến trúc hệ thống](HostAgent.png)


## 🚀 Cài Đặt và Chạy

### 1. Cài đặt dependencies

```bash
cd host_agent
pip install -r requirements.txt
```

### 2. Cấu hình environment variables

```bash
# Copy file example và cấu hình
cp env.example .env

# Chỉnh sửa file .env
nano .env
```

**Các biến bắt buộc:**
- `GOOGLE_API_KEY`: API key của Google Gemini

**Các biến tùy chọn:**
- `HOST`: Host server (mặc định: 0.0.0.0)
- `PORT`: Port server (mặc định: 8080)
- `ADVISOR_AGENT_URL`: URL của Advisor Agent A2A server (mặc định: http://localhost:10001)
- `SEARCH_AGENT_URL`: URL của Search Agent A2A server (mặc định: http://localhost:10002)
- `ORDER_AGENT_URL`: URL của Order Agent A2A server (mặc định: http://localhost:10003)

**MySQL Configuration (tùy chọn - cho real-time logging):**
- `MYSQL_HOST`: MySQL host (mặc định: localhost)
- `MYSQL_PORT`: MySQL port (mặc định: 3306)
- `MYSQL_USER`: MySQL username (mặc định: root)
- `MYSQL_PASSWORD`: MySQL password
- `MYSQL_DATABASE`: Database name (mặc định: chat_db)

**Redis Configuration (tùy chọn):**
- `REDIS_HOST`: Redis host (mặc định: localhost)
- `REDIS_PORT`: Redis port (mặc định: 6379)
- `REDIS_PASSWORD`: Redis password
- `REDIS_DB`: Redis database number (mặc định: 0)

### 3. Setup MySQL Database (Tùy chọn)

**Để bật real-time message logging:**

```bash
# 1. Tạo database và table
mysql -u root -p < setup_mysql.sql

# 2. Configure environment variables trong .env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=chat_db
```

**MySQL sẽ tự động lưu:**
- Tất cả messages từ user và AI responses
- Rich metadata: files, agent info, analysis data
- Session tracking và user history

**Nếu không có MySQL:** System vẫn hoạt động bình thường với Redis + LangChain memory.

### 4. Chạy server

```bash
# Cách 1: Chạy trực tiếp
python run_server.py

# Cách 2: Chạy với uvicorn
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

## 📡 API Endpoints

### 1. Health Check
```http
GET /
GET /health
```

### 2. Chat với User (Chỉ 1 endpoint duy nhất)
```http
POST /chat
Content-Type: multipart/form-data
```

**Chỉ có text:**
```http
POST /chat
Content-Type: multipart/form-data

message: "Tôi muốn tìm kính cận thị cho nam"
user_id: "optional_user_id"
session_id: "session_123"
```

**Text + Files (ảnh, document):**
```http
POST /chat
Content-Type: multipart/form-data

message: "Phân tích ảnh này giúp tôi"
user_id: "optional_user_id"
session_id: "session_123"
files: [file1.jpg, file2.png]
```

Response:
```json
{
    "response": "Kết quả từ agent hoặc trả lời trực tiếp",
    "agent_used": "Search Agent",
    "status": "success",
    "timestamp": "2024-01-01T12:00:00"
}
```

### 3. Kiểm tra trạng thái agents
```http
GET /agents/status
```

### 5. Quản lý Chat History
```http
# Lấy lịch sử chat
GET /sessions/{session_id}/history

# Xóa lịch sử chat
DELETE /sessions/{session_id}/history

# Liệt kê các session đang active
GET /sessions
```

## 🧠 Logic Điều Phối

Host Agent sử dụng LangChain + Google Gemini để phân tích message và quyết định:

1. **Yêu cầu tư vấn** → Advisor Agent
   - "Tôi bị cận thị nên chọn kính nào?"
   - "Kính chống ánh sáng xanh có hiệu quả không?"

2. **Yêu cầu tìm kiếm** → Search Agent
   - "Tìm kính cận thị màu đen"
   - "Kính giống như trong ảnh này"

3. **Yêu cầu đặt hàng/thông tin sản phẩm** → Order Agent
   - "Xem thông tin sản phẩm ID 123"
   - "Tạo đơn hàng với 2 sản phẩm"

4. **Câu hỏi chung** → Trả lời trực tiếp
   - "Xin chào"
   - "Cảm ơn"

## 🧪 Testing

```bash
# Chạy test client
cd client
python test_client.py
```

Test client sẽ thực hiện các test cases:
- Health check
- Agents status
- Chat với các loại yêu cầu khác nhau
- File upload và xử lý
- Chat history management

## 📝 Logs

Server sẽ ghi log chi tiết về:
- Quá trình phân tích message
- Agent được chọn
- Kết quả từ các agent
- Lỗi và exception

Example log:
```
2024-01-01 12:00:00 - host_agent - INFO - 📨 Nhận message từ user: Tôi muốn tìm kính cận thị...
2024-01-01 12:00:01 - host_agent - INFO - 🤖 Orchestrator response: {"selected_agent": "Search Agent"...}
2024-01-01 12:00:02 - host_agent - INFO - 📤 Gửi message tới Search Agent: Tôi muốn tìm kính cận thị...
2024-01-01 12:00:03 - host_agent - INFO - 📥 Nhận response từ Search Agent: Đây là kết quả tìm kiếm...
2024-01-01 12:00:04 - host_agent - INFO - ✅ Xử lý thành công, agent được sử dụng: Search Agent
```

## 🔧 Troubleshooting

### Lỗi thường gặp:

1. **GOOGLE_API_KEY không được set**
   ```
   Solution: Thêm GOOGLE_API_KEY vào file .env
   ```

2. **Không kết nối được tới agent khác**
   ```
   Solution: Kiểm tra URL và port của các agent trong .env
   ```

3. **Lỗi parse JSON từ orchestrator**
   ```
   Solution: Kiểm tra prompt template và model response
   ```

## 📚 Documentation

**📋 [Complete API Documentation](API_DOCUMENTATION.md)** - Comprehensive guide với tất cả endpoints, examples, và usage instructions

### **🚀 Key Features**
- ✅ **MySQL Real-time Logging**: Mỗi message tự động save vào MySQL với rich metadata
- ✅ **LangChain Memory Integration**: Advanced conversation memory management  
- ✅ **Triple Storage Strategy**: Redis + LangChain + MySQL cho optimal performance
- ✅ **Multi-modal Support**: Text + file upload processing
- ✅ **Agent Orchestration**: Intelligent routing tới specialized agents
- ✅ **Enhanced Error Handling**: Graceful fallback mechanisms

## 🔄 Development

Khi phát triển thêm tính năng:

1. **Thêm agent mới**: Cập nhật `agents_config` trong `HostServer`
2. **Thay đổi logic điều phối**: Chỉnh sửa prompt template
3. **Thêm endpoint**: Cập nhật `main.py`
4. **Database changes**: Update MySQL schema trong `setup_mysql.sql`

## 📚 Dependencies

### **Core Dependencies**
- **FastAPI**: Web framework cho REST API
- **LangChain**: LLM integration và conversation memory management
- **Google Gemini**: LLM cho việc phân tích và điều phối
- **A2A SDK**: Agent-to-Agent communication protocol
- **httpx**: HTTP client cho A2A communication
- **uvicorn**: ASGI server

### **Storage & Database**
- **Redis**: Session management và caching
- **SQLAlchemy**: Database ORM với async support
- **aiomysql**: Async MySQL connector
- **pymysql**: MySQL driver

### **Development & Testing**
- **python-multipart**: File upload support
- **python-dotenv**: Environment configuration
- **Postman**: API testing với provided collection

## 🤝 Contributing

1. Fork repository
2. Tạo feature branch
3. Commit changes
4. Push và tạo Pull Request

## 📄 License

MIT License 