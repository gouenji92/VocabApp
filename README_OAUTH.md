# 🔐 Hướng dẫn cấu hình OAuth Social Login

VocabApp hỗ trợ đăng nhập bằng **Google**, **GitHub**, và **Twitter**. Làm theo các bước dưới đây để kích hoạt.

---

## 📋 Yêu cầu

- Đã cài đặt dependencies: `authlib`, `httpx`, `cryptography`
- File `.env` đã được tạo (copy từ `.env.example`)

---

## 🔧 Cấu hình từng Provider

### 1️⃣ Google OAuth

**Bước 1: Truy cập Google Cloud Console**
- Mở: https://console.cloud.google.com/apis/credentials
- Đăng nhập bằng tài khoản Google

**Bước 2: Tạo hoặc chọn Project**
- Nếu chưa có, tạo project mới (ví dụ: "VocabApp")

**Bước 3: Tạo OAuth 2.0 Client ID**
1. Click **"+ CREATE CREDENTIALS"** → **"OAuth client ID"**
2. Nếu chưa có OAuth consent screen, cấu hình:
   - User Type: **External** (cho testing)
   - App name: **VocabApp**
   - User support email: Email của bạn
   - Authorized domains: `127.0.0.1` (cho local testing)
   - Scopes: `email`, `profile`, `openid`
3. Application type: **Web application**
4. Name: **VocabApp Local**
5. **Authorized redirect URIs**: Thêm URL sau
   ```
   http://127.0.0.1:8000/auth/google/callback
   ```
6. Click **CREATE**

**Bước 4: Copy credentials vào `.env`**
```env
GOOGLE_CLIENT_ID=123456789-abc...xyz.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abc123xyz...
```

**Bước 5: Test**
- Restart server
- Vào http://127.0.0.1:8000/login
- Click icon Google → Sẽ redirect đến Google login

---

### 2️⃣ GitHub OAuth

**Bước 1: Truy cập GitHub Settings**
- Mở: https://github.com/settings/developers
- Click **"OAuth Apps"** → **"New OAuth App"**

**Bước 2: Điền thông tin**
- Application name: **VocabApp**
- Homepage URL: `http://127.0.0.1:8000`
- Application description: *Ứng dụng học từ vựng* (optional)
- **Authorization callback URL**: 
  ```
  http://127.0.0.1:8000/auth/github/callback
  ```
- Click **"Register application"**

**Bước 3: Generate Client Secret**
- Click **"Generate a new client secret"**
- Copy ngay (chỉ hiển thị 1 lần!)

**Bước 4: Copy credentials vào `.env`**
```env
GITHUB_CLIENT_ID=Ov23liRyrhRMclCWnR67
GITHUB_CLIENT_SECRET=b64307927ded8cd8de9ebcaa59d979aa3256d458
```

**Bước 5: Test**
- Restart server
- Click icon GitHub → Sẽ redirect đến GitHub authorize

---

### 3️⃣ Twitter OAuth

**Bước 1: Truy cập Twitter Developer Portal**
- Mở: https://developer.twitter.com/en/portal/dashboard
- Đăng nhập (cần tài khoản Twitter Developer)

**Bước 2: Tạo App**
1. Click **"+ Create Project"** (nếu chưa có)
2. Project name: **VocabApp**
3. Click **"+ Add App"** → **Create App**
4. App name: **VocabApp-Local**
5. Environment: **Development**

**Bước 3: Cấu hình OAuth 2.0**
1. Vào app settings → **"User authentication settings"**
2. Click **"Set up"**
3. App permissions: **Read**
4. Type of App: **Web App**
5. App info:
   - Callback URI / Redirect URL:
     ```
     http://127.0.0.1:8000/auth/twitter/callback
     ```
   - Website URL: `http://127.0.0.1:8000`
6. Click **"Save"**

**Bước 4: Copy credentials vào `.env`**
- Sau khi save, sẽ thấy **Client ID** và **Client Secret**
```env
TWITTER_CLIENT_ID=VGhpc0lzQW5FeGFtcGxl...
TWITTER_CLIENT_SECRET=ThisIsAnExampleSecret123...
```

**Bước 5: Test**
- Restart server
- Click icon Twitter → Sẽ redirect đến Twitter authorize

---

## 🚀 Khởi động server

```bash
# Activate virtual environment
.venv\Scripts\activate

# Install dependencies (nếu chưa)
pip install authlib httpx cryptography

# Run server
uvicorn app.main:app --reload
```

Truy cập: http://127.0.0.1:8000/login

---

## 🐛 Xử lý lỗi thường gặp

### ❌ "Phương thức đăng nhập này chưa được cấu hình"
- **Nguyên nhân**: Credentials chưa được thêm vào `.env` hoặc vẫn là placeholder
- **Giải pháp**: Kiểm tra file `.env`, đảm bảo không còn `your-google-client-id-here`

### ❌ "redirect_uri_mismatch"
- **Nguyên nhân**: URL callback trong `.env` khác với URL đã đăng ký trên provider
- **Giải pháp**: 
  - Kiểm tra lại **Authorized redirect URIs** trên Google/GitHub/Twitter
  - Phải khớp chính xác: `http://127.0.0.1:8000/auth/{provider}/callback`
  - Không dùng `localhost`, phải là `127.0.0.1`

### ❌ "invalid_client"
- **Nguyên nhân**: Client ID hoặc Client Secret sai
- **Giải pháp**: Copy lại credentials, chú ý không có space thừa

### ❌ OAuth callback không tạo session
- **Kiểm tra logs** trong terminal để xem lỗi cụ thể
- Đảm bảo `SECRET_KEY` trong `.env` được set

---

## 🔐 Production Deployment

Khi deploy lên production (Heroku, Railway, Vercel...):

1. **Cập nhật redirect URIs** với domain thật:
   ```
   https://yourdomain.com/auth/google/callback
   https://yourdomain.com/auth/github/callback
   https://yourdomain.com/auth/twitter/callback
   ```

2. **Set environment variables** trên hosting platform

3. **HTTPS bắt buộc** - OAuth providers yêu cầu HTTPS cho production

4. **Update OAuth consent screen** (Google) với domain verify

---

## 📚 Tài liệu tham khảo

- Google OAuth: https://developers.google.com/identity/protocols/oauth2
- GitHub OAuth: https://docs.github.com/en/apps/oauth-apps
- Twitter OAuth 2.0: https://developer.twitter.com/en/docs/authentication/oauth-2-0
- Authlib: https://docs.authlib.org/

---

## 💡 Tips

- **Development**: Dùng `127.0.0.1:8000` thay vì `localhost` để tránh lỗi redirect
- **Multiple environments**: Tạo nhiều OAuth apps (Local, Staging, Production)
- **Security**: Không commit file `.env` vào git (đã có trong `.gitignore`)
- **Testing**: Tạo test accounts riêng cho development

---

🎉 **Chúc bạn cấu hình thành công!**
