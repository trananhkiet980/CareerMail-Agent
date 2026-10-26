import base64
import hashlib
import threading
from datetime import datetime, timezone

from cryptography.fernet import Fernet
from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    String,
    Text,
    create_engine,
    func,
    select,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from careermail.core import config

_lock = threading.Lock()
_engine = None

_ENCRYPTED_FIELDS = {
    "llm_api_key",
    "gcp_client_secret",
    "gmail_refresh_token",
    "bot_token",
}

_CONFIG_FIELDS = {
    "bot_token",
    "bot_username",
    "telegram_admin_id",
    "ui_language",
    "llm_provider",
    "llm_model",
    "llm_api_key",
    "llm_temperature",
    "llm_timeout",
    "llm_max_tokens",
    "llm_max_retries",
    "llm_base_url",
    "gcp_client_id",
    "gcp_client_secret",
}
_LANGUAGES = {"vi", "en"}


class Base(DeclarativeBase):
    pass


class AppConfig(Base):
    __tablename__ = "app_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bot_token: Mapped[str] = mapped_column(Text, default="")
    bot_username: Mapped[str] = mapped_column(String(128), default="")
    telegram_admin_id: Mapped[str] = mapped_column(String(64), default="")
    ui_language: Mapped[str] = mapped_column(String(8), default="vi")
    llm_provider: Mapped[str] = mapped_column(String(32), default="")
    llm_model: Mapped[str] = mapped_column(String(128), default="")
    llm_api_key: Mapped[str] = mapped_column(Text, default="")
    llm_temperature: Mapped[str] = mapped_column(String(16), default="")
    llm_timeout: Mapped[str] = mapped_column(String(16), default="")
    llm_max_tokens: Mapped[str] = mapped_column(String(16), default="")
    llm_max_retries: Mapped[str] = mapped_column(String(16), default="")
    llm_base_url: Mapped[str] = mapped_column(String(256), default="")
    gcp_client_id: Mapped[str] = mapped_column(Text, default="")
    gcp_client_secret: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[str] = mapped_column(String(64), default="")


class GmailAccount(Base):
    __tablename__ = "gmail_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(256), unique=True)
    label: Mapped[str] = mapped_column(String(64), default="")
    refresh_token: Mapped[str] = mapped_column(Text, default="")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class PendingAction(Base):
    __tablename__ = "pending_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    draft_id: Mapped[str] = mapped_column(String(256), default="")
    to_addr: Mapped[str] = mapped_column(Text)
    subject: Mapped[str] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text)
    attachment_path: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending, sent, cancelled, failed


class JobApplication(Base):
    __tablename__ = "job_applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_name: Mapped[str] = mapped_column(String(256), default="")
    job_title: Mapped[str] = mapped_column(String(256), default="")
    hr_email: Mapped[str] = mapped_column(String(256), default="")
    cv_path: Mapped[str] = mapped_column(Text, default="")
    applied_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    status: Mapped[str] = mapped_column(String(32), default="applied")  # applied, interviewing, offered, rejected
    notes: Mapped[str] = mapped_column(Text, default="")


def _fernet() -> Fernet:
    digest = hashlib.sha256(config.SECRET_KEY.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def _encrypt(value: str) -> str:
    if not value:
        return ""
    return _fernet().encrypt(value.encode()).decode()


def _decrypt(value: str) -> str:
    if not value:
        return ""
    try:
        return _fernet().decrypt(value.encode()).decode()
    except Exception:
        return ""


def _get_engine():
    global _engine
    if _engine is None:
        url = config.DATABASE_URL
        kwargs = {"pool_pre_ping": True}
        if url.startswith("sqlite"):
            kwargs["connect_args"] = {"check_same_thread": False}
        _engine = create_engine(url, **kwargs)
        Base.metadata.create_all(_engine)
    return _engine


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _get_or_create_config(session: Session) -> AppConfig:
    row = session.get(AppConfig, 1)
    if row is None:
        row = AppConfig(id=1)
        session.add(row)
        session.commit()
    return row


def _serialize_config(row: AppConfig) -> dict:
    data = {
        "bot_token": _decrypt(row.bot_token),
        "bot_username": row.bot_username,
        "telegram_admin_id": row.telegram_admin_id,
        "ui_language": row.ui_language or "vi",
        "llm_provider": row.llm_provider or "openai",
        "llm_model": row.llm_model,
        "llm_api_key": _decrypt(row.llm_api_key),
        "llm_temperature": row.llm_temperature,
        "llm_timeout": row.llm_timeout,
        "llm_max_tokens": row.llm_max_tokens,
        "llm_max_retries": row.llm_max_retries,
        "llm_base_url": row.llm_base_url,
        "gcp_client_id": row.gcp_client_id,
        "gcp_client_secret": _decrypt(row.gcp_client_secret),
        "updated_at": row.updated_at,
    }
    return data


def get_config() -> dict:
    with _lock, Session(_get_engine()) as session:
        row = _get_or_create_config(session)
        return _serialize_config(row)


def update_config(**fields) -> dict:
    with _lock, Session(_get_engine()) as session:
        row = _get_or_create_config(session)
        for key, value in fields.items():
            if key not in _CONFIG_FIELDS:
                continue
            if key == "ui_language" and value not in _LANGUAGES:
                continue
            val_str = "" if value is None else str(value).strip()
            if key in _ENCRYPTED_FIELDS:
                val_str = _encrypt(val_str) if val_str else ""
            setattr(row, key, val_str)
        row.updated_at = _now()
        session.commit()
        return _serialize_config(row)


def get_admin_id() -> int | None:
    """Lấy Admin ID: ưu tiên trong DB cấu hình trước, sau đó tới biến môi trường."""
    cfg = get_config()
    db_id = cfg.get("telegram_admin_id")
    if db_id:
        try:
            return int(db_id)
        except ValueError:
            pass
    return config.TELEGRAM_ADMIN_ID


# --- Gmail Accounts Management ---

def list_gmail_accounts() -> list[dict]:
    with _lock, Session(_get_engine()) as session:
        stmt = select(GmailAccount).order_by(GmailAccount.is_default.desc(), GmailAccount.id.asc())
        rows = session.scalars(stmt).all()
        return [
            {
                "id": r.id,
                "email": r.email,
                "label": r.label,
                "refresh_token": _decrypt(r.refresh_token),
                "is_default": bool(r.is_default),
                "created_at": r.created_at.isoformat() if r.created_at else "",
            }
            for r in rows
        ]


def get_gmail_account(account_id: int | None = None) -> dict | None:
    with _lock, Session(_get_engine()) as session:
        if account_id is not None:
            r = session.get(GmailAccount, account_id)
        else:
            r = session.scalar(select(GmailAccount).where(GmailAccount.is_default.is_(True)))
            if r is None:
                r = session.scalar(select(GmailAccount).order_by(GmailAccount.id.asc()))
        if r is None:
            return None
        return {
            "id": r.id,
            "email": r.email,
            "label": r.label,
            "refresh_token": _decrypt(r.refresh_token),
            "is_default": bool(r.is_default),
        }


def add_gmail_account(email: str, refresh_token: str, label: str = "") -> int:
    with _lock, Session(_get_engine()) as session:
        existing = session.scalar(select(GmailAccount).where(GmailAccount.email == email))
        enc_token = _encrypt(refresh_token)
        if existing:
            existing.refresh_token = enc_token
            if label:
                existing.label = label
            session.commit()
            return existing.id

        is_first = (session.scalar(select(func.count()).select_from(GmailAccount)) or 0) == 0
        new_account = GmailAccount(
            email=email,
            refresh_token=enc_token,
            label=label,
            is_default=is_first,
        )
        session.add(new_account)
        session.commit()
        return new_account.id


def set_default_gmail_account(account_id: int) -> None:
    with _lock, Session(_get_engine()) as session:
        accounts = session.scalars(select(GmailAccount)).all()
        for acct in accounts:
            acct.is_default = acct.id == account_id
        session.commit()


def delete_gmail_account(account_id: int) -> bool:
    with _lock, Session(_get_engine()) as session:
        acct = session.get(GmailAccount, account_id)
        if not acct:
            return False
        was_default = acct.is_default
        session.delete(acct)
        session.commit()
        if was_default:
            first = session.scalar(select(GmailAccount).order_by(GmailAccount.id.asc()))
            if first:
                first.is_default = True
                session.commit()
        return True


def count_gmail_accounts() -> int:
    with _lock, Session(_get_engine()) as session:
        return session.scalar(select(func.count()).select_from(GmailAccount)) or 0


# --- Pending Actions (Human-in-the-loop) ---

def create_pending_action(
    to_addr: str,
    subject: str,
    body: str,
    account_id: int | None = None,
    draft_id: str = "",
    attachment_path: str = "",
) -> int:
    with _lock, Session(_get_engine()) as session:
        action = PendingAction(
            account_id=account_id,
            draft_id=draft_id or "",
            to_addr=to_addr,
            subject=subject,
            body=body,
            attachment_path=attachment_path or "",
            status="pending",
        )
        session.add(action)
        session.commit()
        return action.id


def get_pending_action(action_id: int) -> dict | None:
    with _lock, Session(_get_engine()) as session:
        action = session.get(PendingAction, action_id)
        if not action:
            return None
        return {
            "id": action.id,
            "account_id": action.account_id,
            "draft_id": action.draft_id,
            "to_addr": action.to_addr,
            "subject": action.subject,
            "body": action.body,
            "attachment_path": action.attachment_path,
            "status": action.status,
            "created_at": action.created_at.isoformat() if action.created_at else "",
        }


def set_pending_action_status(action_id: int, status: str) -> bool:
    with _lock, Session(_get_engine()) as session:
        action = session.get(PendingAction, action_id)
        if not action:
            return False
        action.status = status
        session.commit()
        return True


def latest_pending_id() -> int:
    with _lock, Session(_get_engine()) as session:
        val = session.scalar(select(func.max(PendingAction.id)))
        return int(val or 0)


# --- Job Application Tracking ---

def record_job_application(
    company_name: str,
    job_title: str,
    hr_email: str,
    cv_path: str = "",
    notes: str = "",
) -> int:
    with _lock, Session(_get_engine()) as session:
        app = JobApplication(
            company_name=company_name,
            job_title=job_title,
            hr_email=hr_email,
            cv_path=cv_path,
            notes=notes,
            status="applied",
        )
        session.add(app)
        session.commit()
        return app.id


def list_job_applications() -> list[dict]:
    with _lock, Session(_get_engine()) as session:
        stmt = select(JobApplication).order_by(JobApplication.applied_at.desc())
        rows = session.scalars(stmt).all()
        return [
            {
                "id": r.id,
                "company_name": r.company_name,
                "job_title": r.job_title,
                "hr_email": r.hr_email,
                "cv_path": r.cv_path,
                "applied_at": r.applied_at.isoformat() if r.applied_at else "",
                "status": r.status,
                "notes": r.notes,
            }
            for r in rows
        ]


def setup_state() -> dict:
    cfg = get_config()
    bot_done = bool(cfg.get("bot_token"))
    llm_done = bool(cfg.get("llm_api_key"))
    gcp_done = bool(cfg.get("gcp_client_id") and cfg.get("gcp_client_secret"))
    gmail_done = count_gmail_accounts() > 0
    admin_done = bool(cfg.get("telegram_admin_id") or config.TELEGRAM_ADMIN_ID)
    all_done = bot_done and llm_done and gcp_done and gmail_done and admin_done
    return {
        "bot_configured": bot_done,
        "llm_configured": llm_done,
        "gcp_configured": gcp_done,
        "gmail_configured": gmail_done,
        "admin_configured": admin_done,
        "all_done": all_done,
    }
