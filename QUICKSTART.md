# 🚀 Quick Start - VocabApp

## Khởi động nhanh (5 phút)

### 1. Cài đặt và chạy

```powershell
# Mở PowerShell tại folder vocab_app
cd C:\Users\Admin\VoiceAI\vocab_app

# Kích hoạt virtual environment
.venv\Scripts\Activate.ps1

# Chạy server
uvicorn app.main:app --reload
```

### 2. Truy cập app

Mở trình duyệt: **http://localhost:8000**

### 3. Đăng ký tài khoản

- Click **Đăng ký**
- Nhập username và password
- Click **Đăng ký ngay**

### 4. Upload bộ từ đầu tiên

**Cách 1: Upload file CSV/XLSX**
- Click **Upload File**
- Chọn file CSV hoặc XLSX
- Preview và điều chỉnh mapping
- Click **Import**

**Cách 2: Tạo file mẫu**

Tạo file `my_words.csv`:
```csv
Term,POS,Definition,Example
happy,adj,vui vẻ,"I am happy today"
study,verb,học,"I study English every day"
book,noun,sách,"This is my favorite book"
```

### 5. Bắt đầu học

- Vào **Danh sách bộ từ**
- Click vào bộ từ vừa tạo
- Click **Bắt đầu học**
- Chọn chế độ:
  - **Flashcard**: Lật thẻ và đánh giá
  - **Điền từ**: Điền vào chỗ trống
  - **Trắc nghiệm**: Chọn đáp án đúng

### 6. Sử dụng AI (Tùy chọn)

**Setup OpenAI API Key:**

1. Lấy key tại: https://platform.openai.com/api-keys
2. Mở file `.env`:
   ```
   OPENAI_API_KEY=sk-your-key-here
   ```
3. Restart server (Ctrl+C và chạy lại uvicorn)

**Sử dụng:**
- Vào chi tiết bộ từ
- Click nút 🤖 ở góc dưới phải
- Chọn tab:
  - **Dịch**: Dịch từ/câu
  - **Ngữ pháp**: Kiểm tra lỗi
  - **Ví dụ**: Tạo câu ví dụ

---

## 🎯 Workflow học tập đề xuất

### Ngày 1: Setup
1. Upload 20-30 từ vựng
2. Học flashcard lần đầu (đánh giá thật)
3. Hệ thống sẽ lên lịch ôn lại

### Ngày 2-7: Ôn tập
1. Vào Dashboard xem "Cần ôn hôm nay"
2. Học các từ đến hạn
3. Thêm từ mới nếu muốn

### Hàng ngày:
- ⏰ Dành 10-15 phút
- 📊 Check Dashboard
- 🔥 Duy trì streak
- ✅ Học hết "Cần ôn hôm nay"

### Tips:
- Đánh giá trung thực (0-5) để thuật toán hoạt động tốt
- Không ôn quá nhiều từ trong 1 ngày (20-30 từ)
- Sử dụng AI để hiểu sâu hơn (dịch, ngữ pháp, ví dụ)
- Export bộ từ backup định kỳ

---

## 📱 Shortcuts

| Tính năng | Đường dẫn |
|-----------|-----------|
| Dashboard | http://localhost:8000/dashboard |
| Upload | http://localhost:8000/ |
| Danh sách bộ từ | http://localhost:8000/sets |
| Đăng xuất | http://localhost:8000/logout |

---

## ❓ FAQs

**Q: Làm sao biết từ nào cần ôn hôm nay?**
A: Vào Dashboard, xem số "Cần ôn hôm nay"

**Q: Tôi muốn học lại từ đã thuộc?**
A: Vào bộ từ → Click "Bắt đầu học" → Chọn mode bất kỳ

**Q: File CSV của tôi không nhận diện đúng?**
A: Ở trang preview, điều chỉnh mapping thủ công trong dropdown

**Q: AI không hoạt động?**
A: Kiểm tra file `.env` có `OPENAI_API_KEY` chưa? Đã restart server chưa?

**Q: Làm sao thêm từ vào bộ đã có?**
A: Vào chi tiết bộ từ → Scroll xuống form "Thêm từ mới" → Điền và Submit

**Q: Export bộ từ ở đâu?**
A: Vào chi tiết bộ từ → Click nút "Export CSV" hoặc "Export XLSX"

**Q: Tôi muốn xóa tài khoản?**
A: Hiện tại chưa có tính năng này. Có thể xóa file `data/users.json` (mất hết data)

---

Chúc bạn học tốt! 🎓📚
