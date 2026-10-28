import json
from pathlib import Path

from langchain_core.tools import tool

from careermail.career import (
    extract_job_info,
    load_master_profile,
    research_company_info,
    tailor_cv,
)
from careermail.core import storage
from careermail.core.observability import record_event
from careermail.email import client as gmail_client


def _dumps(data) -> str:
    return json.dumps(data, ensure_ascii=False)


def _primary_query(query: str) -> str:
    """Focus queries on the Primary inbox category by default to filter out noise."""
    q = (query or "").strip()
    low = q.lower()
    if any(token in low for token in ("category:", "label:", "in:")):
        return q
    return f"category:primary {q}".strip()


def _resolve_account(account):
    """Match account identifier against label, email, or id."""
    accounts = storage.list_gmail_accounts()
    if not accounts:
        return None, accounts
    if account is None or str(account).strip() == "":
        for item in accounts:
            if item["is_default"]:
                return item, accounts
        return accounts[0], accounts
    key = str(account).strip().lower()
    for item in accounts:
        identifiers = {
            str(item["id"]).lower(),
            (item["email"] or "").lower(),
            (item["label"] or "").lower(),
        }
        if key in identifiers:
            return item, accounts
    return None, accounts


@tool
def list_gmail_accounts() -> str:
    """
    List all connected Gmail accounts with their id, email, label, and default status.
    """
    return _dumps(storage.list_gmail_accounts())


@tool
def search_emails(query: str, max_results: int = 10, account: str | None = None) -> str:
    """
    Search emails using Gmail query syntax (e.g. 'from:hr@company.com', 'is:unread', 'subject:interview').
    Defaults to Primary inbox category unless specified otherwise.
    account: optional account identifier/label/email. If omitted, uses default account.
    """
    acct, _ = _resolve_account(account)
    if acct is None:
        return "ERROR: No connected Gmail account found."
    try:
        results = gmail_client.search_emails(
            _primary_query(query), max_results, account_id=acct["id"]
        )
    except Exception as e:
        return f"ERROR: {e}"
    return _dumps(results)


@tool
def read_email(message_id: str, account: str | None = None) -> str:
    """
    Fetch and read full content of a specific email by its message_id.
    account: the account containing the target email.
    """
    acct, _ = _resolve_account(account)
    if acct is None:
        return "ERROR: No connected Gmail account found."
    try:
        result = gmail_client.read_email(message_id, account_id=acct["id"])
    except Exception as e:
        return f"ERROR: {e}"
    return _dumps(result)


@tool
def request_send_email(
    to: str,
    subject: str,
    body: str,
    attachment_path: str | None = None,
    account: str | None = None,
) -> str:
    """
    Draft a regular email and queue it for sending. The email is NOT sent immediately;
    the user must confirm via the interactive button in Telegram.
    to: recipient email address.
    subject: email subject.
    body: email body text.
    attachment_path: optional local file path to attach.
    account: optional sender account label or email.
    """
    if not (to and subject and body):
        return "ERROR: to, subject, and body parameters are required."
    acct, accounts = _resolve_account(account)
    if acct is None:
        labels = ", ".join((a["label"] or a["email"]) for a in accounts) or "(empty)"
        return (
            "CLARIFICATION NEEDED: Multiple accounts exist ("
            f"{labels}). Please ask the user which account to send from."
        )
    draft_id = ""
    try:
        draft_id = gmail_client.create_draft(
            to, subject, body, attachment_path=attachment_path, account_id=acct["id"]
        )
    except Exception as exc:
        record_event("WARNING", "agent", f"create_draft failed (skipping draft): {exc}")

    pending_id = storage.create_pending_action(
        to,
        subject,
        body,
        account_id=acct["id"],
        draft_id=draft_id,
        attachment_path=attachment_path or "",
    )
    return _dumps(
        {
            "pending_id": pending_id,
            "from_account": acct["label"] or acct["email"],
            "has_attachment": bool(attachment_path),
            "draft_created": bool(draft_id),
            "message": "Draft created successfully. Prompt user to confirm sending in Telegram.",
        }
    )


@tool
def apply_for_job(
    job_input: str,
    target_track: str | None = None,
    override_hr_email: str | None = None,
    account: str | None = None,
) -> str:
    """
    Automate the end-to-end job application workflow:
    1. Parse JD from URL link or text description.
    2. Extract HR contact email, company name, and job title.
    3. Tailor candidate CV (ATS LaTeX template) to the best matching Track and compile to PDF.
    4. Generate a polite, highly persuasive Cover Letter email.
    5. Save application action pending user confirmation in Telegram.

    job_input: URL link to job posting (TopCV, ITviec, LinkedIn, etc.) OR full JD text.
    target_track: optional track ID to force (e.g. 'ai_engineer', 'backend_developer', 'automation_engineer').
    override_hr_email: optional HR email if specified by user.
    account: optional Gmail sender account.
    """
    # 1. Parse JD info
    jd_info = extract_job_info(job_input)
    hr_email = override_hr_email or jd_info.get("primary_email", "")
    company_name = jd_info.get("company_name", "Công ty Tuyển dụng")
    job_title = jd_info.get("job_title", "Software / AI Engineer")

    # 2. Tailor CV and Compile PDF
    try:
        pdf_path, track_used, track_title = tailor_cv(
            jd_text=jd_info["text"],
            target_track=target_track,
            company_name=company_name,
            template_name="classic",
        )
    except Exception as exc:
        record_event("ERROR", "agent", f"tailor_cv error: {exc}", exc=exc)
        return f"LỖI TẠO CV: {exc}"

    # 3. Resolve sender account
    acct, accounts = _resolve_account(account)
    if acct is None:
        sender_label = "(mặc định)"
        account_id = None
    else:
        sender_label = acct["label"] or acct["email"]
        account_id = acct["id"]

    # 4. Draft Cover Letter
    subject = f"[Ứng Tuyển] {job_title} - {load_master_profile().get('personal_info', {}).get('name', 'Ứng viên')}"
    personal = load_master_profile().get("personal_info", {})
    name = personal.get("name", "Ứng viên")
    phone = personal.get("phone", "")
    email = personal.get("email", "")

    cover_letter = (
        f"Kính gửi Bộ phận Tuyển dụng {company_name},\n\n"
        f"Tôi là {name}. Qua tìm hiểu về vị trí {job_title} tại {company_name}, "
        f"tôi rất hào hứng nộp hồ sơ ứng tuyển vì nhận thấy định hướng và yêu cầu của Quý công ty "
        f"rất phù hợp với nền tảng kỹ thuật và các dự án thực tế của tôi.\n\n"
        f"Tôi xin gửi kèm bản CV chi tiết (được định dạng theo định hướng {track_title}) đính kèm trong thư này. "
        f"Rất mong có cơ hội được trao đổi trực tiếp cùng Quý công ty trong buổi phỏng vấn sắp tới.\n\n"
        f"Trân trọng,\n"
        f"{name}\n"
        f"Số điện thoại: {phone}\n"
        f"Email: {email}"
    )

    # 5. Create Pending Action
    draft_id = ""
    if hr_email:
        try:
            draft_id = gmail_client.create_draft(
                to_addr=hr_email,
                subject=subject,
                body=cover_letter,
                attachment_path=str(pdf_path),
                account_id=account_id,
            )
        except Exception as exc:
            record_event("WARNING", "agent", f"create_draft for job application failed: {exc}")

    pending_id = storage.create_pending_action(
        to_addr=hr_email or "[CẦN BỔ SUNG EMAIL HR]",
        subject=subject,
        body=cover_letter,
        account_id=account_id,
        draft_id=draft_id,
        attachment_path=str(pdf_path),
    )

    return _dumps(
        {
            "pending_id": pending_id,
            "company_name": company_name,
            "job_title": job_title,
            "hr_email": hr_email,
            "track_used": track_used,
            "track_title": track_title,
            "pdf_path": str(pdf_path),
            "pdf_filename": Path(pdf_path).name,
            "subject": subject,
            "cover_letter": cover_letter,
            "has_email": bool(hr_email),
            "sender_account": sender_label,
            "message": (
                f"Đã chuẩn bị xong hồ sơ ứng tuyển vị trí {job_title} tại {company_name}.\n"
                f"File CV PDF đã được biên dịch thành công theo định hướng {track_title}.\n"
                f"HR Email: {hr_email or 'Chưa tìm thấy email trong JD. Hãy yêu cầu user cung cấp email HR trước khi gửi.'}"
            ),
        }
    )


@tool
def research_company(company_name: str) -> str:
    """
    Search online for background information about a company (products, business model, culture, tech stack).
    company_name: the name of the company to look up.
    """
    return research_company_info(company_name)


@tool
def list_applied_jobs() -> str:
    """
    List all previous companies and jobs applied through CareerMail-Agent.
    """
    return _dumps(storage.list_job_applications())


TOOLS = [
    list_gmail_accounts,
    search_emails,
    read_email,
    request_send_email,
    apply_for_job,
    research_company,
    list_applied_jobs,
]


def get_tools():
    return list(TOOLS)
