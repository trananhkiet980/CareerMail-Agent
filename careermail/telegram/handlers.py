import asyncio

from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.types import ErrorEvent, InlineKeyboardButton, InlineKeyboardMarkup

from careermail.agent.graph import SetupError, run_agent
from careermail.core import i18n, storage
from careermail.core.observability import AppError, record_event
from careermail.email import client as gmail_client

rt = Router()


def _is_admin(user_id: int | None) -> tuple[bool, str | None]:
    if user_id is None:
        return False, "User ID không xác định."
    admin_id = storage.get_admin_id()
    if admin_id is None:
        return (
            False,
            "⚠️ Bot chưa được cấu hình Telegram Admin ID.\n"
            "Vui lòng mở ứng dụng CareerMail-Agent trên máy tính để thiết lập Admin ID bảo mật.",
        )
    if user_id != admin_id:
        return False, i18n.t("no_permission")
    return True, None


def _hint(lang: str) -> str:
    return i18n.t("open_panel_hint", lang)


def _mask(value: str | None, show: int = 4) -> str:
    if not value:
        return "-"
    return f"...{value[-show:]}"


@rt.message(Command("start", "help"))
async def cmd_start(message: types.Message):
    allowed, err_msg = _is_admin(message.from_user.id)
    if not allowed:
        await message.answer(err_msg or "No permission")
        return
    lang = i18n.current_language()
    await message.answer(f"{i18n.t('start', lang)}\n\n{_hint(lang)}")


@rt.message(Command("setup"))
async def cmd_setup(message: types.Message):
    allowed, err_msg = _is_admin(message.from_user.id)
    if not allowed:
        await message.answer(err_msg or "No permission")
        return
    lang = i18n.current_language()
    state = storage.setup_state()
    steps = [
        (i18n.t("step_bot", lang), state["bot_configured"]),
        (i18n.t("step_admin", lang), state["admin_configured"]),
        (i18n.t("step_llm", lang), state["llm_configured"]),
        (i18n.t("step_gcp", lang), state["gcp_configured"]),
        (i18n.t("step_gmail", lang), state["gmail_configured"]),
    ]
    lines = [f"{'✅' if done else '⬜'} {name}" for name, done in steps]
    await message.answer(f"{i18n.t('setup_title', lang)}\n" + "\n".join(lines) + f"\n\n{_hint(lang)}")


@rt.message(Command("status"))
async def cmd_status(message: types.Message):
    allowed, err_msg = _is_admin(message.from_user.id)
    if not allowed:
        await message.answer(err_msg or "No permission")
        return
    lang = i18n.current_language()
    cfg = storage.get_config()
    state = storage.setup_state()
    email_cnt = storage.count_gmail_accounts()
    model = cfg.get("llm_model") or i18n.t("not_set", lang)
    provider = cfg.get("llm_provider") or "-"
    bot_name = cfg.get("bot_username") or "-"
    admin_id_str = cfg.get("telegram_admin_id") or "chưa cài đặt"

    text = (
        f"{i18n.t('status_title', lang)}\n"
        f"• {i18n.t('status_bot', lang)}: @{bot_name}\n"
        f"• {i18n.t('status_admin', lang)}: {admin_id_str}\n"
        f"• {i18n.t('status_llm', lang)}: {provider} / {model} / key {_mask(cfg.get('llm_api_key'))}\n"
        f"• {i18n.t('status_oauth', lang)}: {'✅' if state['gcp_configured'] else '⬜'}\n"
        f"• {i18n.t('status_gmail', lang)}: {'✅' if state['gmail_configured'] else '⬜'} ({email_cnt} tài khoản)\n"
    )
    if state["all_done"]:
        text += f"\n{i18n.t('all_ready', lang)}"
    else:
        text += f"\n{i18n.t('not_ready', lang)} {_hint(lang)}"
    await message.answer(text)


@rt.message(Command("accounts"))
async def cmd_accounts(message: types.Message):
    allowed, err_msg = _is_admin(message.from_user.id)
    if not allowed:
        await message.answer(err_msg or "No permission")
        return
    lang = i18n.current_language()
    accounts = storage.list_gmail_accounts()
    if not accounts:
        await message.answer(i18n.t("accounts_none", lang))
        return
    lines = []
    for account in accounts:
        name = account["label"] or account["email"]
        suffix = f"  ⭐ {i18n.t('account_default', lang)}" if account["is_default"] else ""
        lines.append(f"• {name} — {account['email']}{suffix}")
    await message.answer(f"{i18n.t('accounts_title', lang)}\n" + "\n".join(lines))


@rt.message(Command("applications"))
async def cmd_applications(message: types.Message):
    """Xem danh sách các công ty đã nộp hồ sơ."""
    allowed, err_msg = _is_admin(message.from_user.id)
    if not allowed:
        await message.answer(err_msg or "No permission")
        return
    apps = storage.list_job_applications()
    if not apps:
        await message.answer("📁 Bạn chưa nộp hồ sơ ứng tuyển công ty nào qua CareerMail-Agent.")
        return
    lines = ["📋 **Lịch sử nộp hồ sơ ứng tuyển:**\n"]
    for item in apps[:10]:
        lines.append(
            f"• **{item['company_name']}** — {item['job_title']}\n"
            f"  ✉️ HR: `{item['hr_email']}` | 📅 {item['applied_at'][:10]} | Trạng thái: {item['status']}"
        )
    await message.answer("\n".join(lines))


@rt.message(Command("language"))
async def cmd_language(message: types.Message):
    allowed, err_msg = _is_admin(message.from_user.id)
    if not allowed:
        await message.answer(err_msg or "No permission")
        return
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Tiếng Việt 🇻🇳", callback_data="setlang:vi"),
                InlineKeyboardButton(text="English 🇬🇧", callback_data="setlang:en"),
            ]
        ]
    )
    await message.answer("Chọn ngôn ngữ hiển thị / Choose language:", reply_markup=keyboard)


@rt.callback_query(F.data.startswith("setlang:"))
async def on_set_language(callback: types.CallbackQuery):
    allowed, _ = _is_admin(callback.from_user.id)
    if not allowed:
        await callback.answer("No permission", show_alert=True)
        return
    lang = callback.data.split(":", 1)[1]
    storage.update_config(ui_language=lang)
    await callback.answer("Đã đổi ngôn ngữ / Language updated")
    await callback.message.edit_text(i18n.t("start", lang))


@rt.message(F.text, ~F.text.startswith("/"))
async def handle_chat(message: types.Message):
    allowed, err_msg = _is_admin(message.from_user.id)
    if not allowed:
        await message.answer(err_msg or "No permission")
        return

    lang = i18n.current_language()
    try:
        reply, pending_id = await asyncio.to_thread(run_agent, message.text, str(message.chat.id))
    except SetupError as exc:
        key = "missing_llm" if exc.missing == "llm" else "missing_gmail"
        await message.answer(f"{i18n.t(key, lang)} {_hint(lang)}")
        return
    except AppError as exc:
        ref = record_event("ERROR", "bot", exc.message, code=exc.code, exc=exc)
        await message.answer(i18n.t("error_with_ref", lang).format(ref=ref))
        return
    except Exception as exc:
        ref = record_event("ERROR", "bot", f"chat lỗi: {exc}", exc=exc)
        await message.answer(i18n.t("error_with_ref", lang).format(ref=ref))
        return

    reply_markup = None
    if pending_id:
        reply_markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=i18n.t("button_send", lang), callback_data=f"confirm_send:{pending_id}"
                    ),
                    InlineKeyboardButton(
                        text=i18n.t("button_cancel", lang), callback_data=f"cancel_send:{pending_id}"
                    ),
                ]
            ]
        )
    await message.answer(reply or "OK", reply_markup=reply_markup)


@rt.callback_query(F.data.startswith("confirm_send:"))
async def on_confirm_send(callback: types.CallbackQuery):
    allowed, _ = _is_admin(callback.from_user.id)
    if not allowed:
        await callback.answer(i18n.t("no_permission"), show_alert=True)
        return
    lang = i18n.current_language()
    action_id = int(callback.data.split(":", 1)[1])
    action = storage.get_pending_action(action_id)
    if not action or action["status"] != "pending":
        await callback.answer(i18n.t("already_processed", lang))
        return

    try:
        if action.get("draft_id"):
            await asyncio.to_thread(
                gmail_client.send_draft, action["draft_id"], action.get("account_id")
            )
        else:
            await asyncio.to_thread(
                gmail_client.send_email,
                action["to_addr"],
                action["subject"],
                action["body"],
                attachment_path=action.get("attachment_path"),
                account_id=action.get("account_id"),
            )
        storage.set_pending_action_status(action_id, "sent")
        await callback.answer(i18n.t("sent_ok", lang))
        new_text = (
            f"{callback.message.text or ''}\n\n"
            f"✅ {i18n.t('sent_to', lang)} {action['to_addr']} — {i18n.t('subject', lang)}: {action['subject']}"
        )
        await callback.message.edit_text(new_text)
    except Exception as exc:
        storage.set_pending_action_status(action_id, "failed")
        ref = record_event("ERROR", "bot", f"send_email lỗi: {exc}", exc=exc, action=action_id)
        await callback.answer(i18n.t("send_failed", lang), show_alert=True)
        await callback.message.edit_text(
            f"{callback.message.text or ''}\n\n❌ {i18n.t('send_failed_detail', lang)} (mã {ref})"
        )


@rt.callback_query(F.data.startswith("cancel_send:"))
async def on_cancel_send(callback: types.CallbackQuery):
    allowed, _ = _is_admin(callback.from_user.id)
    if not allowed:
        await callback.answer(i18n.t("no_permission"), show_alert=True)
        return
    lang = i18n.current_language()
    action_id = int(callback.data.split(":", 1)[1])
    action = storage.get_pending_action(action_id)
    storage.set_pending_action_status(action_id, "cancelled")
    if action and action.get("draft_id"):
        try:
            await asyncio.to_thread(
                gmail_client.delete_draft, action["draft_id"], action.get("account_id")
            )
        except Exception as exc:
            record_event("WARNING", "bot", f"delete_draft lỗi: {exc}")
    await callback.answer(i18n.t("cancelled", lang))
    await callback.message.edit_text(f"{callback.message.text or ''}\n\n❌ {i18n.t('cancelled_note', lang)}")


@rt.message(Command("reset"))
async def cmd_reset(message: types.Message):
    allowed, err_msg = _is_admin(message.from_user.id)
    if not allowed:
        await message.answer(err_msg or "No permission")
        return
    from careermail.agent.graph import reset_memory

    reset_memory(str(message.chat.id))
    await message.answer(i18n.t("memory_reset", i18n.current_language()))


@rt.errors()
async def on_unhandled_error(event: ErrorEvent):
    record_event("ERROR", "bot", f"unhandled: {event.exception}", exc=event.exception)
    return True
