from careermail.core.observability import record_event


def research_company_info(company_name: str, max_results: int = 5) -> str:
    """
    Search the web for business model, products, tech stack, and workplace culture of a target company.
    """
    company = company_name.strip()
    if not company or company.lower() in ("công ty tuyển dụng", "company"):
        return "Vui lòng cung cấp tên công ty cụ thể để tra cứu."

    query = f"{company} công ty sản phẩm dịch vụ công nghệ"
    results = []

    try:
        from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            raw = list(ddgs.text(query, max_results=max_results))
            for item in raw:
                title = item.get("title", "")
                snippet = item.get("body", "")
                link = item.get("href", "")
                results.append(f"• **{title}**\n  {snippet}\n  Nguồn: {link}")

        if not results:
            # Fallback search without Vietnamese keywords
            with DDGS() as ddgs:
                raw = list(ddgs.text(f"{company} software company profile", max_results=max_results))
                for item in raw:
                    results.append(f"• **{item.get('title')}**\n  {item.get('body')}\n  Nguồn: {item.get('href')}")

    except ImportError:
        return (
            "Tính năng tra cứu thông tin qua mạng cần cài đặt thêm thư viện 'duckduckgo-search'.\n"
            "Chạy lệnh: `pip install duckduckgo-search` trong môi trường venv để kích hoạt."
        )
    except Exception as exc:
        record_event("WARNING", "research", f"DuckDuckGo search error: {exc}")
        return f"Không thể tra cứu trực tiếp qua mạng: {exc}. Bạn có thể cung cấp thêm thông tin về công ty để tôi phân tích."

    if not results:
        return f"Không tìm thấy thông tin công khai nổi bật về '{company}'. Có thể đây là công ty mới thành lập hoặc hoạt động kín tiếng."

    output = f"🔍 **Thông tin tra cứu về '{company}':**\n\n" + "\n\n".join(results)
    return output
