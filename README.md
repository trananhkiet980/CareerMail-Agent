# CareerMail-Agent

> **AI Career & Smart Inbox Assistant** — Trợ lý AI đồng hành cùng Hộp thư Chuyên nghiệp & Phát triển Sự nghiệp của bạn qua Telegram.

Chạy ngầm dưới khay hệ thống (System Tray) máy tính cá nhân (local-first). Bạn cấu hình các API keys một lần duy nhất trên giao diện Desktop Settings, sau đó tương tác hoàn toàn qua Telegram trên điện thoại mọi lúc mọi nơi.

---

### ✨ Tính Năng Nổi Bật

1. **Smart Inbox Assistant (Quản lý hộp thư chuyên nghiệp):**
   * Tóm tắt nhanh các email quan trọng trong ngày (tập trung vào Primary Inbox, bỏ qua thư rác/quảng cáo).
   * Tìm kiếm email cũ, hóa đơn, tài liệu theo ngôn ngữ tự nhiên.
   * Soạn thảo email phản hồi đối tác, khách hàng chuẩn văn phong công sở.
   * Hỗ trợ gửi kèm **File đính kèm** (Attachments).

2. **Career & Job Hunter (Săn việc & Phát triển sự nghiệp):**
   * Đọc hiểu bài đăng tuyển dụng (JD) từ văn bản hoặc link web (TopCV, LinkedIn, ITviec...).
   * Tự động điều chỉnh CV cá nhân bằng **LaTeX** cho khớp với JD (chuẩn ATS) dựa trên dữ liệu thật (chống bịa đặt dự án).
   * Bóc tách email liên hệ của HR để gửi thư ứng tuyển trực tiếp kèm CV PDF.
   * Tra cứu thông tin văn hóa/sản phẩm công ty và đóng vai người phỏng vấn thử (Mock Interview).

3. **Bảo mật & Kiểm duyệt an toàn (Human-in-the-loop):**
   * **Bảo mật tuyệt đối:** Chỉ cho phép duy nhất tài khoản Telegram Admin ID đã cấu hình điều khiển bot, chặn 100% người lạ trên mạng.
   * **An toàn khi gửi thư:** Tuyệt đối không bao giờ tự ý gửi mail ngầm. Mọi email quan trọng hoặc hồ sơ ứng tuyển đều được gửi bản nháp + file PDF về Telegram để bạn duyệt trước khi gửi đi.
   * Mã hóa bảo mật đối xứng Fernet toàn bộ token, khóa bí mật trên SQLite cục bộ.

---

### 🚀 Hướng Dẫn Sử Dụng Nhanh

#### 1. Cài đặt môi trường
Khuyến nghị sử dụng Python 3.11 hoặc 3.12:

```bash
cd K:\.check\CareerMail-Agent
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

#### 2. Khởi chạy ứng dụng
```bash
python -m careermail
```

Cửa sổ **CareerMail-Agent Settings** sẽ xuất hiện:
* **Tab Telegram & Bảo mật:**
  * Nhập `Bot Token` tạo từ [@BotFather](https://t.me/BotFather).
  * Nhập `Telegram Admin ID` (lấy số ID của bạn từ [@userinfobot](https://t.me/userinfobot)) để bảo vệ bot.
  * Bấm **Lưu & Khởi động Bot**.
* **Tab Mô hình AI:**
  * Chọn nhà cung cấp (OpenAI, Gemini, Claude, DeepSeek) và dán API Key.
* **Tab Google / Gmail:**
  * Dán nội dung `client_secret.json` từ Google Cloud Console (loại Desktop app).
  * Bấm **Thêm tài khoản Gmail** và xác thực trên trình duyệt.

Sau khi thiết lập xong, bạn có thể đóng cửa sổ lại, ứng dụng sẽ thu nhỏ xuống chạy ngầm dưới khay hệ thống (System Tray). Bạn chỉ việc mở Telegram trên điện thoại để chat với bot!
