from careermail.core import storage

MESSAGES = {
    "vi": {
        "start": (
            "Xin chào! Tôi là CareerMail-Agent — Trợ lý AI đồng hành cùng Hộp thư & Sự nghiệp của bạn.\n\n"
            "✨ Bạn có thể yêu cầu tôi:\n"
            "• 'Tóm tắt email mới nhất hôm nay'\n"
            "• 'Tìm kiếm hóa đơn hoặc thư từ sếp'\n"
            "• 'Ứng tuyển job này: [Dán link/text JD]'\n"
            "• 'Tối ưu CV cho vị trí [Tên Job]'\n"
            "• 'Tìm hiểu công ty [Tên công ty]'\n"
            "• 'Phỏng vấn thử tôi vị trí Python Engineer'\n\n"
            "Gõ /help để xem danh sách lệnh."
        ),
        "open_panel_hint": "Mở ứng dụng CareerMail-Agent trên máy tính để hoàn tất cấu hình.",
        "step_bot": "Cấu hình Telegram Bot Token",
        "step_admin": "Cấu hình Telegram Admin ID (Bảo mật)",
        "step_llm": "Cấu hình API Key mô hình AI",
        "step_gcp": "Cấu hình Google OAuth Client",
        "step_gmail": "Kết nối tài khoản Gmail",
        "setup_title": "Trạng thái cấu hình CareerMail-Agent:",
        "status_title": "Trạng thái hoạt động hiện tại:",
        "status_bot": "Bot",
        "status_admin": "Admin ID",
        "status_llm": "Mô hình AI",
        "status_oauth": "Google OAuth",
        "status_gmail": "Gmail đã kết nối",
        "all_ready": "✅ Mọi thứ đã sẵn sàng hoạt động!",
        "not_ready": "⚠️ Cần hoàn tất cấu hình để sử dụng.",
        "not_connected": "chưa kết nối",
        "not_set": "chưa thiết lập",
        "accounts_title": "Danh sách tài khoản Gmail đã kết nối:",
        "accounts_none": "Chưa có tài khoản Gmail nào. Mở ứng dụng để thêm.",
        "account_default": "Mặc định",
        "missing_llm": "Chưa cấu hình API Key AI.",
        "missing_gmail": "Chưa kết nối tài khoản Gmail nào.",
        "no_permission": "⛔ Bạn không có quyền truy cập bot này. Chỉ Telegram Admin được phép.",
        "button_send": "🚀 Xác nhận Gửi Email",
        "button_cancel": "❌ Hủy bỏ",
        "sent_ok": "Đã gửi email thành công!",
        "sent_to": "Đã gửi đến",
        "subject": "Tiêu đề",
        "send_failed": "Gửi email thất bại",
        "send_failed_detail": "Lỗi khi gửi email",
        "cancelled": "Đã hủy",
        "cancelled_note": "Yêu cầu gửi email đã bị hủy.",
        "already_processed": "Yêu cầu này đã được xử lý trước đó.",
        "memory_reset": "Đã xóa trí nhớ ngắn hạn của cuộc trò chuyện.",
        "error_with_ref": "Có lỗi xảy ra (Mã sự cố: {ref}). Vui lòng kiểm tra tab Logs trong ứng dụng.",
        "oauth_ok_title": "Kết nối Gmail thành công!",
        "oauth_fail_title": "Kết nối Gmail thất bại",
        "oauth_google_error": "Lỗi từ Google:",
        "oauth_missing_code": "Không nhận được authorization code từ Google.",
        "oauth_exchange_error": "Không thể đổi mã xác thực:",
        "oauth_profile_error": "Không thể lấy thông tin email:",
        "oauth_connected": "Đã kết nối thành công tài khoản",
    },
    "en": {
        "start": (
            "Hello! I am CareerMail-Agent — Your Personal AI Career & Smart Inbox Assistant.\n\n"
            "✨ You can ask me:\n"
            "• 'Summarize my latest emails today'\n"
            "• 'Search for invoices or boss emails'\n"
            "• 'Apply for this job: [Paste JD link/text]'\n"
            "• 'Tailor my CV for [Job Title]'\n"
            "• 'Research company [Company Name]'\n"
            "• 'Mock interview me for Python Engineer'\n\n"
            "Type /help to see all commands."
        ),
        "open_panel_hint": "Open CareerMail-Agent Settings window on your PC to complete setup.",
        "step_bot": "Configure Telegram Bot Token",
        "step_admin": "Configure Telegram Admin ID (Security)",
        "step_llm": "Configure AI Model API Key",
        "step_gcp": "Configure Google OAuth Client",
        "step_gmail": "Connect Gmail Account",
        "setup_title": "CareerMail-Agent Setup Status:",
        "status_title": "Current Status:",
        "status_bot": "Bot",
        "status_admin": "Admin ID",
        "status_llm": "AI Model",
        "status_oauth": "Google OAuth",
        "status_gmail": "Connected Gmail",
        "all_ready": "✅ All systems ready!",
        "not_ready": "⚠️ Configuration needed before use.",
        "not_connected": "not connected",
        "not_set": "not set",
        "accounts_title": "Connected Gmail Accounts:",
        "accounts_none": "No Gmail account connected. Open Settings to add one.",
        "account_default": "Default",
        "missing_llm": "AI Model API key is not configured.",
        "missing_gmail": "No Gmail account is connected.",
        "no_permission": "⛔ Access denied. Only configured Telegram Admin can access this bot.",
        "button_send": "🚀 Confirm & Send Email",
        "button_cancel": "❌ Cancel",
        "sent_ok": "Email sent successfully!",
        "sent_to": "Sent to",
        "subject": "Subject",
        "send_failed": "Failed to send email",
        "send_failed_detail": "Error sending email",
        "cancelled": "Cancelled",
        "cancelled_note": "Email sending request was cancelled.",
        "already_processed": "This request was already processed.",
        "memory_reset": "Short-term conversation memory has been cleared.",
        "error_with_ref": "An error occurred (Ref: {ref}). Please check the Logs tab in the app.",
        "oauth_ok_title": "Gmail Connected Successfully!",
        "oauth_fail_title": "Gmail Connection Failed",
        "oauth_google_error": "Google error:",
        "oauth_missing_code": "Missing authorization code from Google.",
        "oauth_exchange_error": "Failed to exchange authorization code:",
        "oauth_profile_error": "Failed to fetch email profile:",
        "oauth_connected": "Successfully connected account",
    },
}


def current_language() -> str:
    try:
        cfg = storage.get_config()
        return cfg.get("ui_language") or "vi"
    except Exception:
        return "vi"


def t(key: str, lang: str | None = None) -> str:
    lang = lang or current_language()
    table = MESSAGES.get(lang, MESSAGES["vi"])
    return table.get(key, MESSAGES["vi"].get(key, key))
