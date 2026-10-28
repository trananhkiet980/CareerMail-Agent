import re
from urllib.parse import urlparse

import requests
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

from careermail.core.observability import record_event

# Regex for detecting email addresses
EMAIL_REGEX = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
)

# Common non-HR or asset false-positive extensions/domains
IGNORED_EMAIL_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".css", ".js"}
IGNORED_DOMAINS = {"example.com", "domain.com", "sentry.io", "w3.org"}


def is_url(text: str) -> bool:
    """Check if the given string is an HTTP/HTTPS URL."""
    try:
        parsed = urlparse(text.strip())
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def fetch_url_content(url: str, timeout: int = 15) -> str:
    """Fetch and extract readable plain text from a webpage URL."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()

    html = resp.text
    if BeautifulSoup is not None:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg"]):
            tag.decompose()
        lines = (line.strip() for line in soup.get_text().splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        return "\n".join(chunk for chunk in chunks if chunk)

    # Regex fallback when BeautifulSoup is not available
    clean = re.sub(r"<(script|style|nav|footer|header)[\s\S]*?</\1>", "", html, flags=re.IGNORECASE)
    clean = re.sub(r"<[^>]+>", " ", clean)
    clean = re.sub(r"\s+", " ", clean)
    return clean.strip()


def extract_candidate_emails(text: str) -> list[str]:
    """Find all valid email addresses in text, filtering out obvious noise."""
    raw_matches = EMAIL_REGEX.findall(text)
    valid_emails = []
    seen = set()

    for email in raw_matches:
        low = email.lower()
        if low in seen:
            continue
        domain = low.split("@")[-1]
        if domain in IGNORED_DOMAINS:
            continue
        if any(low.endswith(ext) for ext in IGNORED_EMAIL_EXTS):
            continue
        seen.add(low)
        valid_emails.append(email)

    # Sort so that emails containing 'hr', 'recruitment', 'tuyendung', 'career', 'jobs' are prioritized
    priority_keywords = ("hr", "recruitment", "tuyendung", "career", "job", "contact")
    valid_emails.sort(
        key=lambda e: any(kw in e.lower() for kw in priority_keywords),
        reverse=True,
    )
    return valid_emails


def extract_job_info(raw_input: str) -> dict:
    """
    Parse a JD from either a URL or raw text.
    Returns:
        dict: {
            "is_url": bool,
            "source_url": str,
            "text": str,
            "primary_email": str,
            "candidate_emails": list[str],
            "company_name": str,
            "job_title": str
        }
    """
    text = raw_input.strip()
    source_url = ""
    is_link = False

    # Check if input starts with or contains a URL
    url_match = re.search(r"https?://[^\s]+", text)
    if url_match:
        source_url = url_match.group(0).rstrip(".,;)")
        is_link = True
        try:
            fetched_text = fetch_url_content(source_url)
            # Combine fetched text with any custom text user provided
            text = f"URL: {source_url}\n\n{text}\n\n=== NỘI DUNG TỪ TRANG WEB ===\n{fetched_text}"
            record_event("INFO", "jd_extractor", f"Cào thành công nội dung từ {source_url}")
        except Exception as exc:
            record_event("WARNING", "jd_extractor", f"Không thể cào link {source_url}: {exc}")

    # Extract emails
    emails = extract_candidate_emails(text)
    primary_email = emails[0] if emails else ""

    # Heuristic extraction for company name and job title
    company_name = ""
    job_title = ""

    # Check common company patterns
    company_patterns = [
        r"(?:công ty|tập đoàn|doanh nghiệp|company)\s*[:\-]?\s*([^\n,.]+)",
        r"(?:tại|ở)\s+([A-Z0-9][A-Za-z0-9\s&]+(?:JSC|Corp|Company|Technology|Ltd|Group))",
    ]
    for pattern in company_patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            company_name = m.group(1).strip()
            break

    # Check common job title patterns
    title_patterns = [
        r"(?:vị trí|chức danh|tuyển dụng|hiring|role|position)\s*[:\-]?\s*([^\n,.]+)",
        r"((?:Senior|Junior|Lead|Intern|Mid)?\s*(?:AI|Python|Backend|Frontend|Fullstack|Data|DevOps|Software)\s*(?:Engineer|Developer|Specialist))",
    ]
    for pattern in title_patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            job_title = m.group(1).strip()
            break

    return {
        "is_url": is_link,
        "source_url": source_url,
        "text": text,
        "primary_email": primary_email,
        "candidate_emails": emails,
        "company_name": company_name or "Công ty Tuyển dụng",
        "job_title": job_title or "Software / AI Engineer",
    }
