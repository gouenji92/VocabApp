# 🤖 Hướng dẫn sử dụng tính năng AI

## Giới thiệu

VocabApp hiện có tích hợp Trợ lý AI với 3 tính năng chính:
- 🌐 **Dịch thuật**: Dịch từ và câu giữa Anh-Việt
- ✅ **Kiểm tra ngữ pháp**: Phát hiện và sửa lỗi ngữ pháp tiếng Anh
- 💡 **Tạo câu ví dụ**: Tạo câu ví dụ tự nhiên cho từ vựng

## Cài đặt OpenAI API Key

### Bước 1: Lấy API Key

1. Truy cập https://platform.openai.com/
2. Đăng ký hoặc đăng nhập tài khoản
3. Vào **API Keys** (https://platform.openai.com/api-keys)
4. Click **Create new secret key**
5. Copy API key (bắt đầu với `sk-...`)

### Bước 2: Cấu hình trong VocabApp

1. Mở file `.env` trong thư mục gốc của VocabApp
2. Tìm dòng: `# OPENAI_API_KEY=sk-your-key-here`
3. Bỏ dấu `#` và thay thế bằng API key thật của bạn:
   ```
   OPENAI_API_KEY=sk-proj-abc123xyz...
   ```
4. Lưu file

### Bước 3: Khởi động lại server

```powershell
# Stop server (Ctrl+C nếu đang chạy)
# Start lại server
.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

## Sử dụng Trợ lý AI

### Truy cập

1. Vào trang chi tiết bộ từ (click vào bất kỳ bộ từ nào)
2. Tìm nút 🤖 màu tím ở góc dưới bên phải
3. Click để mở bảng điều khiển AI

### Tính năng 1: Dịch thuật

1. Chọn tab **Dịch**
2. Nhập từ hoặc câu cần dịch
3. Chọn hướng dịch:
   - **Anh → Việt**: Dịch từ tiếng Anh sang tiếng Việt
   - **Việt → Anh**: Dịch từ tiếng Việt sang tiếng Anh
4. Click **Dịch ngay**
5. Xem kết quả bên dưới

**Ví dụ:**
- Input: "happiness"
- Direction: Anh → Việt
- Output: "hạnh phúc, niềm vui"

### Tính năng 2: Kiểm tra ngữ pháp

1. Chọn tab **Ngữ pháp**
2. Nhập câu tiếng Anh cần kiểm tra
3. Click **Kiểm tra ngữ pháp**
4. Xem phân tích lỗi và câu được sửa

**Ví dụ:**
- Input: "She don't like apples"
- Output: 
  ```
  Corrected: She doesn't like apples
  
  Error: Subject-verb agreement error. "She" is third person 
  singular and requires "doesn't" instead of "don't".
  ```

### Tính năng 3: Tạo câu ví dụ

1. Chọn tab **Ví dụ**
2. Nhập từ vựng cần tạo câu ví dụ
3. (Tùy chọn) Nhập loại từ (noun, verb, adj, adv...)
4. Click **Tạo câu ví dụ**
5. Xem câu ví dụ được tạo

**Ví dụ:**
- Word: "diligent"
- POS: "adj"
- Output: "She is a diligent student who always completes her homework on time."

## Chi phí sử dụng

- OpenAI API **KHÔNG MIỄN PHÍ** (có free tier nhỏ khi đăng ký mới)
- Model sử dụng: **GPT-3.5-turbo** (rẻ nhất, ~$0.002/1K tokens)
- Ước tính: ~500-1000 requests với $5

### Kiểm tra sử dụng:
- Truy cập: https://platform.openai.com/usage
- Xem Usage và Billing

### Giới hạn chi phí:
1. Vào **Settings** → **Billing** → **Usage limits**
2. Set hard limit (ví dụ: $5/month)
3. Set soft limit để nhận email cảnh báo

## Troubleshooting

### Lỗi: "AI features not enabled"

**Nguyên nhân**: Chưa cấu hình OPENAI_API_KEY

**Giải pháp**:
1. Kiểm tra file `.env` có dòng `OPENAI_API_KEY=sk-...`
2. Đảm bảo không có dấu `#` ở đầu dòng
3. Restart server

### Lỗi: "Invalid API Key"

**Nguyên nhân**: API key sai hoặc đã expire

**Giải pháp**:
1. Tạo API key mới tại https://platform.openai.com/api-keys
2. Cập nhật lại trong file `.env`
3. Restart server

### Lỗi: "Rate limit exceeded"

**Nguyên nhân**: Gọi API quá nhiều/nhanh

**Giải pháp**:
1. Đợi 1 phút rồi thử lại
2. Nếu dùng free tier, nâng cấp lên paid account
3. Kiểm tra usage limits

### Lỗi: "Insufficient quota"

**Nguyên nhân**: Đã hết credits/quota

**Giải pháp**:
1. Vào https://platform.openai.com/billing
2. Add payment method và top-up credits

## Lưu ý bảo mật

⚠️ **QUAN TRỌNG**:
- **KHÔNG** commit file `.env` lên Git/GitHub
- **KHÔNG** chia sẻ API key với người khác
- **KHÔNG** hard-code API key vào source code
- File `.env` đã được thêm vào `.gitignore`

## Tắt tính năng AI

Nếu không muốn dùng AI:

1. Mở file `.env`
2. Thêm dấu `#` trước `OPENAI_API_KEY`:
   ```
   # OPENAI_API_KEY=sk-...
   ```
3. Restart server
4. Nút 🤖 vẫn hiện nhưng sẽ báo "Set OPENAI_API_KEY to enable AI features"

## Alternative: Sử dụng dịch vụ khác

Nếu không muốn dùng OpenAI, có thể thay đổi code trong `app/ai_helper.py` để dùng:
- Google Translate API (miễn phí có giới hạn)
- DeepL API (chất lượng cao cho dịch thuật)
- Local models (Llama, GPT4All - miễn phí nhưng cần GPU)

## Hỗ trợ

Có vấn đề? Kiểm tra:
1. Server logs (terminal chạy uvicorn)
2. Browser console (F12 → Console tab)
3. File `app/ai_helper.py` - hàm `is_ai_enabled()`

Chúc bạn học tốt! 📚✨
