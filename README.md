# 📚 VocabApp - Ứng dụng học từ vựng tiếng Anh thông minh
## Chạy độc lập hoàn toàn

VocabApp đã được tách biệt hoàn toàn với VoiceAI, có Dockerfile, env riêng và cổng riêng.

### Cách chạy cục bộ (không Docker)

1) Mở PowerShell tại thư mục `vocab_app` và tạo venv riêng (nếu chưa có):

```
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

2) Tạo file `.env` từ mẫu và chỉnh sửa khóa bí mật (SECRET_KEY) cũng như API key nếu cần:

```
Copy-Item .env.example .env -Force
```

3) Chạy server:

```
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Mở http://localhost:8000

### Chạy bằng Docker (độc lập)

Tại thư mục gốc dự án (chứa thư mục `docker/`):

```
docker compose -f docker/docker-compose.yml up -d --build vocabapp
```

Hoặc build và chạy trực tiếp trong `vocab_app/`:

```
docker build -t vocabapp:latest .
docker run --rm -p 8000:8000 --env-file .env vocabapp:latest
```

### Ghi chú

- Thư mục `VocabApp/` rỗng có thể xóa để tránh nhầm lẫn.
- VoiceAI backend chạy cổng 8004; VocabApp chạy cổng 8000. Hai service độc lập nhau.
- Env của VocabApp không phụ thuộc env của VoiceAI.


Ứng dụng học từ vựng tiếng Anh giống Quizlet Pro với giao diện tiếng Việt. Hỗ trợ upload file CSV/XLSX, tự động nhận diện cột, 3 chế độ học tập, thống kê chi tiết, và **tích hợp AI** cho dịch thuật và kiểm tra ngữ pháp!

## ✨ Tính năng chính

### 📤 Upload & Import
- Upload file CSV hoặc XLSX
- Tự động nhận diện cột: Từ vựng (Term), Loại từ (POS), Nghĩa (Definition), Ví dụ (Example)
- Preview và điều chỉnh mapping trước khi import
- Hỗ trợ cả tiếng Anh và tiếng Việt trong header
- Kéo & Thả file trực tiếp vào vùng upload (drag & drop)
- Dán (Ctrl+V) ảnh hoặc file từ clipboard vào vùng upload

### 📚 Quản lý bộ từ
- Tạo, xem, sửa, xóa bộ từ (vocabulary sets)
- Thêm, sửa, xóa từ vựng trong bộ
- Tìm kiếm nhanh trong danh sách bộ từ và từ vựng
- Export bộ từ ra file CSV hoặc XLSX

### 🎯 3 chế độ học tập
1. **Flashcard**: Lật thẻ, đánh giá độ nhớ (0-5 sao)
2. **Fill-in-blank**: Điền từ còn thiếu vào chỗ trống
3. **Multiple Choice**: Chọn nghĩa đúng từ 4 đáp án

### 🧠 Spaced Repetition (SM-2)
- Thuật toán lặp lại cách quãng thông minh
- Tự động lên lịch ôn tập dựa trên độ khó và hiệu suất
- Ưu tiên từ sắp đến hạn ôn tập

### 🤖 Trợ lý AI (Mới!)
- **Dịch thuật**: Dịch từ và câu giữa Anh-Việt
- **Kiểm tra ngữ pháp**: Phát hiện và sửa lỗi ngữ pháp tiếng Anh
- **Tạo câu ví dụ**: Tự động tạo câu ví dụ tự nhiên cho từ vựng
- **Gợi ý từ đồng nghĩa**: Tìm các từ đồng nghĩa
- ⚠️ Yêu cầu OpenAI API key (xem [AI_FEATURES.md](AI_FEATURES.md))

### 📊 Thống kê & Dashboard
- Tổng số bộ từ và từ vựng
- Số từ đã học và từ cần ôn hôm nay
- Độ chính xác học tập (accuracy)
- Chuỗi ngày học liên tục (streak)

### 👤 Xác thực người dùng
- Đăng ký tài khoản mới
- Đăng nhập/Đăng xuất
- **🆕 Đăng nhập bằng Google, GitHub, Twitter** (OAuth 2.0)
- Dữ liệu riêng biệt cho mỗi người dùng
- Session-based authentication với cookie

### 🌐 Social Login (OAuth 2.0)
- **Google OAuth**: Đăng nhập nhanh bằng tài khoản Google
- **GitHub OAuth**: Đăng nhập cho developers
- **Twitter OAuth**: Đăng nhập bằng tài khoản Twitter
- ⚠️ Yêu cầu cấu hình credentials (xem [README_OAUTH.md](README_OAUTH.md))

## 🚀 Cài đặt và chạy (Windows PowerShell)

### Bước 1: Clone hoặc tải project

```powershell
cd C:\Users\YourName
# Giả sử đã có folder vocab_app
cd vocab_app
```

### Bước 2: Tạo môi trường ảo và cài đặt

```powershell
# Tạo virtual environment
python -m venv .venv

# Kích hoạt virtual environment
.\.venv\Scripts\Activate.ps1

# Cài đặt dependencies
pip install -r requirements.txt
```

### Bước 3: Cấu hình Supabase và AI

```powershell
# Copy file .env mẫu
copy .env.example .env

# Mở .env và dán Supabase DATABASE_URL vào đó
# Thêm OpenAI API key nếu muốn dùng AI
notepad .env
```

### Bước 4: Chạy server

```powershell
# Start development server với auto-reload
uvicorn app.main:app --reload
```

### Bước 5: Mở trình duyệt

Truy cập: **http://localhost:8000**

Lần đầu tiên sẽ redirect đến trang đăng ký. Tạo tài khoản và bắt đầu học! 🎉

## 📁 Cấu trúc thư mục

```
app/
  main.py              # FastAPI app + routes
  auth.py              # User authentication
  storage.py           # JSON storage layer
  detect.py            # Column detection algorithm
  ai_helper.py         # AI features (OpenAI integration)
  templates/           # Jinja2 templates (Vietnamese UI)
    login.html         # Login page
    register.html      # Registration page
    dashboard.html     # Statistics dashboard
    upload.html        # File upload page
    sets_list.html     # List all vocabulary sets
    set_detail.html    # Set detail with terms table
    set_edit.html      # Edit set info
    term_edit.html     # Edit term
    study_mode.html    # Choose study mode
    study.html         # Flashcard mode
    study_fill.html    # Fill-in-blank mode
    study_choice.html  # Multiple choice mode
data/                  # Local JSON storage
  users.json           # User accounts
  sets.json            # Vocabulary sets
  terms.json           # Vocabulary terms
  progress.json        # Learning progress
.env                   # Environment variables (API keys)
.env.example           # Example .env file
requirements.txt       # Python dependencies
README.md              # This file
AI_FEATURES.md         # AI features documentation
```

## 🔌 API Endpoints

### Authentication
- `GET /login` - Trang đăng nhập
- `POST /login` - Xử lý đăng nhập
- `GET /register` - Trang đăng ký
- `POST /register` - Xử lý đăng ký
- `POST /logout` - Đăng xuất

### OAuth 2.0 (🆕)
- `GET /auth/google` - Bắt đầu Google OAuth flow
- `GET /auth/google/callback` - Google OAuth callback
- `GET /auth/github` - Bắt đầu GitHub OAuth flow
- `GET /auth/github/callback` - GitHub OAuth callback
- `GET /auth/twitter` - Bắt đầu Twitter OAuth flow
- `GET /auth/twitter/callback` - Twitter OAuth callback

### Dashboard
- `GET /dashboard` - Trang thống kê tổng quan

### Upload & Import
- `GET /` - Trang upload file
- `POST /preview` - Preview và detect columns
- `POST /import` - Import vocabulary set

### Vocabulary Sets
- `GET /sets` - Danh sách bộ từ
- `GET /sets/{id}` - Chi tiết bộ từ
- `GET /sets/{id}/edit` - Trang sửa bộ từ
- `POST /sets/{id}/edit` - Xử lý sửa bộ từ
- `POST /sets/{id}/delete` - Xóa bộ từ
- `GET /sets/{id}/export?format=csv|xlsx` - Export bộ từ
- `POST /sets/{id}/add-term` - Thêm từ vào bộ

### Terms
- `GET /terms/{id}/edit` - Trang sửa từ
- `POST /terms/{id}/edit` - Xử lý sửa từ
- `POST /terms/{id}/delete` - Xóa từ

### Study Modes
- `GET /study/{id}?mode=select` - Chọn chế độ học
- `GET /study/{id}?mode=flashcard` - Flashcard mode
- `GET /study/{id}?mode=fill` - Fill-in-blank mode
- `GET /study/{id}?mode=choice` - Multiple choice mode
- `POST /api/next` - Lấy term tiếp theo (spaced repetition)
- `POST /api/answer` - Submit flashcard answer (rating)
- `POST /api/choice` - Get term for multiple choice

### AI Features (🆕)
- `POST /api/ai/translate` - Dịch văn bản
- `POST /api/ai/grammar` - Kiểm tra ngữ pháp
- `POST /api/ai/example` - Tạo câu ví dụ
- `POST /api/ai/synonyms` - Gợi ý từ đồng nghĩa
- `GET /api/ai/status` - Kiểm tra trạng thái AI

## 🛠️ Công nghệ sử dụng

- **Backend**: FastAPI (Python 3.11+)
- **Frontend**: Jinja2 Templates + Vanilla JavaScript
- **Storage**: PostgreSQL qua Supabase hoặc SQLite cục bộ khi chưa cấu hình `DATABASE_URL`
- **AI**: OpenAI API (GPT-3.5-turbo)
- **Authentication**: Session-based with itsdangerous
- **File Processing**: openpyxl (XLSX), csv (CSV)
- **Algorithm**: SM-2 Spaced Repetition

## 📝 Dependencies

```txt
fastapi>=0.110.0
uvicorn[standard]>=0.22.0
jinja2>=3.1.3
python-multipart>=0.0.9
openpyxl>=3.1.5
pydantic>=1.10.13
itsdangerous>=2.1.2
openai>=1.3.0
python-dotenv>=1.0.0
authlib>=1.6.0          # OAuth 2.0 client
httpx>=0.28.0           # Async HTTP for OAuth
cryptography>=46.0.0    # OAuth encryption
```

## 🤖 Sử dụng AI Features

Xem hướng dẫn chi tiết tại [AI_FEATURES.md](AI_FEATURES.md)

**TL;DR:**
1. Lấy OpenAI API key tại https://platform.openai.com/api-keys
2. Thêm vào file `.env`: `OPENAI_API_KEY=sk-your-key`
3. Restart server
4. Click nút 🤖 ở góc dưới phải trong trang chi tiết bộ từ

## 🔐 Sử dụng Social Login (OAuth)

Xem hướng dẫn chi tiết tại [README_OAUTH.md](README_OAUTH.md)

**TL;DR:**
1. **Google**: Lấy credentials từ https://console.cloud.google.com/apis/credentials
2. **GitHub**: Lấy credentials từ https://github.com/settings/developers
3. **Twitter**: Lấy credentials từ https://developer.twitter.com/en/portal/dashboard
4. Thêm vào file `.env`:
   ```
   GOOGLE_CLIENT_ID=your-client-id
   GOOGLE_CLIENT_SECRET=your-client-secret
   GITHUB_CLIENT_ID=your-client-id
   GITHUB_CLIENT_SECRET=your-client-secret
   TWITTER_CLIENT_ID=your-client-id
   TWITTER_CLIENT_SECRET=your-client-secret
   ```
5. Restart server
6. Click icon Google/GitHub/Twitter trên trang login

## 📊 Thuật toán Spaced Repetition (SM-2)

VocabApp sử dụng thuật toán SM-2 để tối ưu hóa việc ôn tập:

### Cách hoạt động:
1. **Đánh giá (Rating)**:
   - 0-2: Quên hoàn toàn → Reset về ngày 1
   - 3: Khó nhớ → Tăng chậm
   - 4: Nhớ tốt → Tăng bình thường
   - 5: Nhớ hoàn hảo → Tăng nhanh

2. **Easiness Factor**: Từ 1.3 đến 4.0
   - Dễ nhớ → easiness cao → khoảng cách ngày lớn
   - Khó nhớ → easiness thấp → ôn lại sớm hơn

3. **Interval (Khoảng cách ngày)**:
   - Lần 1: 1 ngày
   - Lần 2: 6 ngày
   - Lần 3+: interval × easiness factor

### Ưu tiên học:
1. Từ đến hạn ôn (next_review ≤ today)
2. Từ chưa học lần nào (repetitions = 0)
3. Từ còn xa nhất (future reviews)

## 🎨 Giao diện

- **Theme**: Gradient tím (#667eea → #764ba2)
- **Responsive**: Tối ưu cho desktop và mobile
- **Modern UI**: Card-based layout, smooth animations
- **Vietnamese**: Toàn bộ UI bằng tiếng Việt

## 🔒 Bảo mật

- Password hashing với bcrypt
- Session-based authentication (7 ngày)
- **OAuth 2.0**: Đăng nhập an toàn qua Google/GitHub/Twitter
- User data isolation
- API key stored in `.env` (not in code)
- `.env` in `.gitignore` (không commit lên Git)
- **HTTPS required**: OAuth providers yêu cầu HTTPS cho production

## ⚠️ Lưu ý

### Về dữ liệu:
- App lưu dữ liệu local trong `data/` folder (JSON files)
- Không có database nên không phù hợp cho production lớn
- Với >10,000 từ hoặc >100 users, nên chuyển sang SQLite/Postgres

### Về AI:
- OpenAI API **có phí** (~$0.002/1K tokens)
- Free tier có giới hạn: ~$5 credits khi đăng ký mới
- Set usage limits để tránh chi phí cao: https://platform.openai.com/usage

### Về file upload:
- Max file size: Không giới hạn mặc định (configure trong FastAPI)
- Supported formats: CSV, XLSX
- Encoding: UTF-8 recommended
- Hỗ trợ drag & drop + paste: Di chuột kéo file vào khung hoặc dùng Ctrl+V sau khi chụp ảnh màn hình

## 🚧 Roadmap (Tương lai)

- [ ] Chuyển sang database (SQLite/Postgres)
- [ ] Export Anki flashcards (.apkg)
- [ ] Học theo nhóm (shared sets)
- [ ] Mobile app (React Native)
- [ ] Text-to-Speech cho phát âm
- [ ] Image flashcards
- [ ] Thống kê chi tiết hơn (charts)
- [ ] Dark mode
- [ ] Import từ Quizlet

## 📞 Hỗ trợ

Gặp vấn đề? Kiểm tra:
1. Server logs (terminal chạy uvicorn)
2. Browser console (F12)
3. File `.env` có đúng API key không
4. Virtual environment đã activate chưa

## 📄 License

MIT License - Free to use and modify

---

Made with ❤️ using FastAPI + OpenAI
