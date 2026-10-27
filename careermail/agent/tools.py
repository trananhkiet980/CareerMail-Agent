import json

from langchain_core.tools import tool

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
    Draft an email and queue it for sending. The email is NOT sent immediately;
    the user must confirm via the interactive button in Telegram.
    to: recipient email address.
    subject: email subject.
    body: email body text.
    attachment_path: optional local file path to attach (such as a tailored CV PDF).
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


TOOLS = [list_gmail_accounts, search_emails, read_email, request_send_email]


def get_tools():
    return list(TOOLS)
