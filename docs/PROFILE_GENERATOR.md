# 🛠️ CareerMail-Agent: Hướng Dẫn Tự Động Tạo `master_profile.json`

Tài liệu này giúp bạn tạo file hồ sơ cá nhân (`data/master_profile.json`) chuẩn chỉnh chỉ trong **1 phút** bằng cách tận dụng các trợ lý AI mạnh mẽ như **Antigravity, ChatGPT, Claude hoặc Gemini**.

---

## 🚀 Hướng Dẫn Nhanh (3 Bước)

1. **Chuẩn bị dữ liệu của bạn:** Gom tất cả thông tin bạn có (file CV cũ dạng PDF/Word/Text, portfolio, link GitHub, hoặc mô tả các dự án bạn đã từng làm).
2. **Mở Trợ lý AI:** Mở Antigravity, ChatGPT, Claude hoặc Gemini.
3. **Copy & Dán:** Copy toàn bộ **CÂU PROMPT Ở PHẦN 2** bên dưới, dán kèm CV/thông tin của bạn vào khung chat của AI.
4. **Lưu file:** Copy đoạn JSON mà AI trả về, dán vào file `data/master_profile.json` trong thư mục CareerMail-Agent (bạn có thể tham khảo file mẫu `master_profile.example.json`).

---

## 📋 PHẦN 1: KHUNG DỮ LIỆU CHUẨN (`SCHEMA`)

Dưới đây là cấu trúc JSON mà hệ thống CareerMail-Agent sử dụng để biên dịch CV sang LaTeX và xuất PDF:

```json
{
  "personal_info": {
    "name": "Họ và Tên",
    "location": "Thành phố, Quốc gia",
    "phone": "Số điện thoại (kèm Zalo nếu có)",
    "email": "Email liên hệ chính",
    "github": "https://github.com/username",
    "linkedin": "https://www.linkedin.com/in/username"
  },
  "education": {
    "degree": "Tên bằng cấp (vd: Bachelor of Computer Science)",
    "institution": "Tên trường Đại học / Cao đẳng",
    "period": "Thời gian theo học (vd: September 2023 - September 2026)",
    "details": "Điểm GPA, xếp loại tốt nghiệp, thành tích học thuật nổi bật"
  },
  "certifications": [
    "Chứng chỉ ngoại ngữ (vd: English B1 APTIS / IELTS / TOEIC)",
    "Chứng chỉ chuyên môn (AWS, Google Cloud, Cisco... nếu có)"
  ],
  "default_track": "id_nhanh_mac_dinh",
  "tracks": {
    "ten_nhanh_1": {
      "display_title": "Tên chức danh định hướng (vd: AI / Machine Learning Engineer)",
      "summary": "Đoạn giới thiệu ngắn 3-4 câu làm nổi bật mục tiêu nghề nghiệp theo định hướng này.",
      "skills_categories": {
        "Programming Languages": "Python, SQL, Java...",
        "Core Technologies": "Kỹ năng chuyên sâu theo nhánh này...",
        "Frameworks & Tools": "Frameworks, Thư viện, Công cụ...",
        "Databases & Cloud": "Cơ sở dữ liệu, Docker, Cloud..."
      },
      "selected_project_ids": ["project_id_1", "project_id_2"]
    }
  },
  "experiences": [
    {
      "company": "Tên công ty",
      "role": "Vị trí đảm nhiệm (Intern, Junior, Lead...)",
      "period": "Thời gian làm việc (vd: July 2026 - September 2026)",
      "location": "Địa điểm làm việc (nếu có)",
      "bullet_points": [
        "{\\bf Nhiệm vụ/Thành tựu 1:} Mô tả hành động và kết quả đạt được.",
        "{\\bf Nhiệm vụ/Thành tựu 2:} Mô tả công nghệ và số liệu tối ưu."
      ]
    }
  ],
  "all_projects": [
    {
      "id": "project_id_1",
      "name": "Tên Dự Án",
      "role": "Vai trò của bạn (vd: Lead Developer, Solo Project...)",
      "period": "Thời gian thực hiện (vd: September 2026 - Present)",
      "github": "https://github.com/...",
      "demo": "https://...",
      "bullet_points": [
        "{\\bf Kiến trúc & Xử lý cốt lõi:} Mô tả bài toán kỹ thuật giải quyết.",
        "{\\bf Công nghệ & Tính năng chính:} Các thư viện, mô hình, giải pháp áp dụng.",
        "{\\bf Tối ưu & Kết quả đạt được:} Số liệu độ trễ, hiệu năng, người dùng."
      ]
    }
  ]
}
```

---

## 🤖 PHẦN 2: CÂU PROMPT DÀNH CHO AI

> *Hãy copy toàn bộ đoạn văn bản trong khung dưới đây, thay thế phần `[DÁN CV HOẶC DỰ ÁN CỦA BẠN VÀO ĐÂY]` bằng thông tin thực tế của bạn, rồi gửi cho AI.*

```text
Bạn là một Chuyên gia Cố vấn Nghề nghiệp và Kỹ sư Tuyển dụng cấp cao (Senior Career Coach & Tech Recruiter).
Dưới đây là toàn bộ thông tin cá nhân, CV cũ, kinh nghiệm và danh sách các dự án thực tế của tôi:

=== THÔNG TIN VÀ DỰ ÁN CỦA TÔI ===
[DÁN CV HOẶC DỰ ÁN CỦA BẠN VÀO ĐÂY]
===================================

Nhiệm vụ của bạn là:
1. Đọc và phân tích toàn bộ dữ liệu trên một cách cẩn thận.
2. Dựa vào năng lực thực tế của tôi, hãy tự động nhận diện từ 1 đến 3 ĐỊNH HƯỚNG VAI TRÒ (Role Tracks) phù hợp nhất với tôi (Ví dụ: Nếu tôi làm nhiều mảng, có thể chia thành 'backend_developer', 'frontend_developer', 'data_analyst', 'ai_engineer', 'mobile_developer'... tùy theo những gì tôi thực sự có. Nếu tôi chỉ chuyên sâu 1 mảng, hãy chỉ tạo 1 Track duy nhất).
3. Với mỗi Track:
   - Viết một đoạn tóm tắt Profile Summary chuyên nghiệp, súc tích (3-4 câu) theo đúng góc nhìn của vai trò đó.
   - Sắp xếp và làm nổi bật các nhóm kỹ năng (skills_categories) liên quan nhất lên đầu.
   - Chọn lọc ra 2 đến 3 dự án phù hợp nhất trong danh sách 'all_projects' để đưa vào 'selected_project_ids'.
4. Trình bày các gạch đầu dòng (bullet points) của Kinh nghiệm và Dự án theo chuẩn ATS: Bắt đầu bằng động từ hành động mạnh mẽ, nêu rõ bài toán kỹ thuật, công nghệ sử dụng và kết quả/số liệu đạt được (theo công thức XYZ/STAR). Sử dụng cú pháp LaTeX `{\bf Tiêu đề:}` ở đầu mỗi gạch đầu dòng.
5. RÀNG BUỘC CỐT LÕI:
   - Tuyệt đối CHỈ SỬ DỤNG thông tin có thật từ dữ liệu tôi đã cung cấp. Không được bịa đặt thêm công ty, dự án hay bằng cấp mà tôi chưa từng trải qua.
   - Đầu ra DUY NHẤT là một khối JSON hợp lệ theo đúng cấu trúc của PHẦN 1, không kèm theo lời giải thích bên ngoài.
```
