from careermail.core import storage
from careermail.core.observability.errors import SetupError
from careermail.core.observability.events import record_event

SYSTEM_PROMPT = (
    "Bạn là CareerMail-Agent — Trợ lý AI đồng hành cùng Hộp thư Chuyên nghiệp & Phát triển Sự nghiệp của User qua Telegram. "
    "Hãy luôn trả lời bằng ngôn ngữ mà user đang dùng (tiếng Việt hoặc tiếng Anh). Bạn có trí nhớ ngắn hạn trong cuộc trò chuyện.\n\n"
    "🎯 NĂNG LỰC CỐT LÕI:\n"
    "1. Quản lý Hộp thư Gmail: Đọc, tìm kiếm (search_emails), tóm tắt email và soạn thư trả lời (request_send_email).\n"
    "2. Săn việc & Tự động Ứng tuyển:\n"
    "   - Khi user đưa link JD hoặc dán văn bản tuyển dụng (hoặc nói muốn ứng tuyển job): HÃY GỌI TOOL apply_for_job.\n"
    "   - Tool apply_for_job sẽ tự động đọc link/JD, bóc tách email HR, chọn track phù hợp nhất từ Master Profile, "
    "biên dịch file CV PDF và chuẩn bị thư ứng tuyển kèm nút xác nhận.\n"
    "   - Nếu tool trả về chưa có email HR, hãy thông báo cho user và đề nghị user cung cấp địa chỉ email HR để gửi.\n"
    "3. Nghiên cứu Công ty: Khi user hỏi về một công ty (mô hình, sản phẩm, văn hóa...), gọi tool research_company.\n"
    "4. Lịch sử Ứng tuyển: Khi user hỏi đã nộp những công ty nào, gọi tool list_applied_jobs.\n\n"
    "📌 NGUYÊN TẮC BẮT BUỘC:\n"
    "- Dùng list_gmail_accounts để biết danh sách tài khoản Gmail đang kết nối.\n"
    "- Khi tìm email thông thường, mặc định tìm trong hộp thư chính (Primary).\n"
    "- TUYỆT ĐỐI AN TOÀN (Human-in-the-loop): Mọi email (bao gồm cả thư ứng tuyển) chỉ được gửi đi sau khi user bấm nút xác nhận trong Telegram.\n"
    "- Trả lời tự nhiên, rõ ràng, ngắn gọn, định dạng văn bản dễ đọc trên màn hình điện thoại."
)

_memory = None


def _get_memory():
    global _memory
    if _memory is None:
        try:
            from langgraph.checkpoint.memory import InMemorySaver

            _memory = InMemorySaver()
        except Exception:
            from langgraph.checkpoint.memory import MemorySaver

            _memory = MemorySaver()
    return _memory


def reset_memory(conversation_id: str) -> None:
    memory = _get_memory()
    func = getattr(memory, "delete_thread", None)
    if callable(func):
        try:
            func(conversation_id)
        except Exception:
            pass


def _missing_setup_message(missing: str) -> str:
    guide = {
        "llm": "Bạn chưa cấu hình API key mô hình AI.",
        "gmail": "Bạn chưa kết nối tài khoản Gmail nào.",
    }
    head = guide.get(missing, "Cấu hình chưa hoàn tất.")
    return f"{head} Mở ứng dụng CareerMail-Agent trên máy tính để hoàn tất. Hoặc gõ /setup."


def run_agent(user_text: str, conversation_id: str | None = None):
    from langchain_core.messages import AIMessage

    from careermail.agent.llm import build_model

    cfg = storage.get_config()
    if not cfg.get("llm_api_key"):
        raise SetupError("llm", _missing_setup_message("llm"))
    if storage.count_gmail_accounts() == 0:
        raise SetupError("gmail", _missing_setup_message("gmail"))

    model = build_model()
    if model is None:
        raise SetupError("llm", _missing_setup_message("llm"))

    from langgraph.prebuilt import create_react_agent

    from careermail.agent.tools import get_tools

    agent = create_react_agent(
        model, get_tools(), prompt=SYSTEM_PROMPT, checkpointer=_get_memory()
    )
    before = storage.latest_pending_id()
    messages = [("user", user_text)]
    config = {"configurable": {"thread_id": conversation_id or "default"}}
    try:
        response = agent.invoke({"messages": messages}, config=config)
    except Exception as exc:
        record_event("ERROR", "agent", f"run_agent lỗi: {exc}", exc=exc)
        raise

    final_text = ""
    for message in response["messages"]:
        if isinstance(message, AIMessage) and message.content:
            final_text = str(message.content)

    after = storage.latest_pending_id()
    pending_id = after if after > before else None

    record_event("INFO", "agent", "run xong", pending=pending_id)
    return final_text, pending_id
