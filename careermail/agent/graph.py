from careermail.core import storage
from careermail.core.observability.errors import SetupError
from careermail.core.observability.events import record_event

SYSTEM_PROMPT = (
    "Bạn là CareerMail-Agent — Trợ lý AI đồng hành cùng Hộp thư Chuyên nghiệp & Phát triển Sự nghiệp của User qua Telegram. "
    "Hãy luôn trả lời bằng ngôn ngữ mà user đang dùng (tiếng Việt hoặc tiếng Anh). Bạn có trí nhớ trong cuộc trò chuyện.\n\n"
    "🎯 VAI TRÒ CHÍNH:\n"
    "1. Quản lý Hộp thư Gmail: Đọc, tìm kiếm, tóm tắt email và soạn thảo email phản hồi lịch sự, chuẩn văn phong công sở.\n"
    "2. Hỗ trợ Sự nghiệp & Tìm việc: Phân tích JD, tư vấn kỹ năng, hỗ trợ soạn thư ứng tuyển tới HR và phỏng vấn thử (Mock Interview).\n\n"
    "📌 QUY TẮC BẮT BUỘC:\n"
    "- Dùng list_gmail_accounts để biết danh sách tài khoản Gmail đang kết nối.\n"
    "- Khi tìm email, mặc định tìm trong hộp thư chính (Primary). Khi user hỏi chung chung, dùng tài khoản mặc định.\n"
    "- Khi user muốn gửi email: Tự soạn thảo nội dung lịch sự, chuyên nghiệp. Nếu user KHÔNG chỉ định tài khoản và có nhiều tài khoản, hãy hỏi trước khi gọi request_send_email.\n"
    "- TUYỆT ĐỐI AN TOÀN: Email chỉ được gửi sau khi user bấm nút xác nhận trên Telegram.\n"
    "- Không sử dụng định dạng code block hay markdown phức tạp gây vỡ giao diện Telegram, trả về văn bản tự nhiên, rõ ràng."
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
