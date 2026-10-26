import threading
import tkinter as tk
import webbrowser
from tkinter import messagebox, simpledialog, ttk
from tkinter.scrolledtext import ScrolledText

from careermail.core import config, storage
from careermail.desktop import autostart
from careermail.email import client as gmail_client
from careermail.email import oauth

PROVIDERS = {
    "openai": ("OpenAI", ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "gpt-4.1"]),
    "deepseek": ("DeepSeek", ["deepseek-chat", "deepseek-reasoner"]),
    "anthropic": (
        "Claude",
        [
            "claude-3-7-sonnet-latest",
            "claude-3-5-sonnet-latest",
            "claude-3-5-haiku-latest",
        ],
    ),
    "google_genai": (
        "Gemini",
        ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash", "gemini-1.5-flash"],
    ),
}

STRINGS = {
    "vi": {
        "title": "CareerMail-Agent",
        "tab_bot": "Telegram & Bảo mật",
        "tab_model": "Mô hình AI",
        "tab_gmail": "Google / Gmail",
        "tab_logs": "Nhật ký",
        "bot_token": "Bot Token",
        "admin_id": "Telegram Admin ID (Bảo mật)",
        "admin_hint": "Lấy ID số của bạn từ bot @userinfobot trên Telegram. Chỉ duy nhất ID này mới có quyền ra lệnh cho bot.",
        "save_start": "Lưu & Khởi động Bot",
        "bot_running": "Bot đang chạy: @{u}",
        "bot_stopped": "Bot đang dừng",
        "autostart": "Khởi động cùng Windows",
        "provider": "Nhà cung cấp AI",
        "model": "Mô hình (Model)",
        "api_key": "API Key",
        "temperature": "Temperature",
        "timeout": "Timeout (giây)",
        "max_tokens": "Max Tokens",
        "max_retries": "Max Retries",
        "save": "Lưu cấu hình",
        "saved": "Đã lưu thành công.",
        "model_current": "Đang dùng: {provider} · {model} · key {key} · temp {temperature}",
        "gcp_current": "OAuth Client ID: {client_id}",
        "gcp_hint": "Dán file client_secret.json tải từ Google Cloud Console (Desktop app).",
        "paste_json": "Nội dung client_secret.json",
        "client_id": "Client ID",
        "client_secret": "Client Secret",
        "accounts": "Danh sách tài khoản Gmail",
        "add_account": "Thêm tài khoản Gmail",
        "set_default": "Đặt làm mặc định",
        "rename": "Đổi nhãn",
        "remove": "Xoá tài khoản",
        "col_label": "Nhãn",
        "col_email": "Địa chỉ Email",
        "col_default": "Mặc định",
        "refresh": "Làm mới",
        "level_all": "Tất cả",
        "need_gcp": "Cần cấu hình Google OAuth Client trước khi thêm tài khoản.",
        "opened_browser": "Đã mở trình duyệt Google để xác thực. Hoàn tất đăng nhập rồi quay lại ứng dụng.",
        "label_prompt": "Nhập nhãn cho tài khoản (vd: Cá nhân, Công việc):",
        "confirm_remove": "Bạn có chắc chắn muốn xoá tài khoản Gmail này?",
        "error": "Lỗi",
        "info": "Thông báo",
        "language": "Ngôn ngữ / Language",
        "quit": "Thoát ứng dụng",
        "logs_hint": "Nhật ký hoạt động (lưu trữ 30 ngày gần nhất).",
    },
    "en": {
        "title": "CareerMail-Agent",
        "tab_bot": "Telegram & Security",
        "tab_model": "AI Model",
        "tab_gmail": "Google / Gmail",
        "tab_logs": "Logs",
        "bot_token": "Bot Token",
        "admin_id": "Telegram Admin ID (Security)",
        "admin_hint": "Get your numeric user ID from @userinfobot on Telegram. Only this ID will have access to control the bot.",
        "save_start": "Save & Start Bot",
        "bot_running": "Bot is running: @{u}",
        "bot_stopped": "Bot stopped",
        "autostart": "Start with Windows",
        "provider": "AI Provider",
        "model": "Model",
        "api_key": "API Key",
        "temperature": "Temperature",
        "timeout": "Timeout (s)",
        "max_tokens": "Max Tokens",
        "max_retries": "Max Retries",
        "save": "Save Settings",
        "saved": "Saved successfully.",
        "model_current": "Active: {provider} · {model} · key {key} · temp {temperature}",
        "gcp_current": "Active OAuth Client: {client_id}",
        "gcp_hint": "Paste contents of client_secret.json (Google Cloud Console Desktop app).",
        "paste_json": "client_secret.json content",
        "client_id": "Client ID",
        "client_secret": "Client Secret",
        "accounts": "Connected Gmail Accounts",
        "add_account": "Add Gmail Account",
        "set_default": "Set as Default",
        "rename": "Rename Label",
        "remove": "Remove Account",
        "col_label": "Label",
        "col_email": "Email Address",
        "col_default": "Default",
        "refresh": "Refresh",
        "level_all": "All",
        "need_gcp": "Please configure Google OAuth Client first.",
        "opened_browser": "Opened browser for Google authorization. Complete sign in and return here.",
        "label_prompt": "Label for this account (e.g., Personal, Work):",
        "confirm_remove": "Remove this Gmail account?",
        "error": "Error",
        "info": "Info",
        "language": "Language",
        "quit": "Exit",
        "logs_hint": "Recent logs (retained for 30 days).",
    },
}


class SettingsWindow:
    def __init__(self, app) -> None:
        self.app = app
        self.root = tk.Tk()
        self.root.title("CareerMail-Agent")
        self.root.geometry("780x640")
        self.root.minsize(720, 560)

        # App icon
        icon_path = config.paths.resource_path("assets", "icon.ico")
        if icon_path.is_file():
            try:
                self.root.iconbitmap(default=str(icon_path))
            except Exception:
                pass

        self._style = ttk.Style(self.root)
        try:
            self._style.theme_use("clam")
        except Exception:
            pass

        self._build_ui()
        self._load_data()

    def t(self, key: str, **kwargs) -> str:
        lang = storage.get_config().get("ui_language") or "vi"
        raw = STRINGS.get(lang, STRINGS["vi"]).get(key, key)
        return raw.format(**kwargs) if kwargs else raw

    def _build_ui(self) -> None:
        top_bar = ttk.Frame(self.root, padding=(14, 10))
        top_bar.pack(fill=tk.X)

        title_lbl = ttk.Label(
            top_bar, text="CareerMail-Agent", font=("Segoe UI", 14, "bold")
        )
        title_lbl.pack(side=tk.LEFT)

        subtitle_lbl = ttk.Label(
            top_bar,
            text="— AI Career & Smart Inbox Assistant",
            font=("Segoe UI", 10),
            foreground="#64748b",
        )
        subtitle_lbl.pack(side=tk.LEFT, padx=(6, 0))

        # Language switcher
        self._lang_var = tk.StringVar(value=storage.get_config().get("ui_language") or "vi")
        lang_cb = ttk.Combobox(
            top_bar,
            textvariable=self._lang_var,
            values=["vi", "en"],
            width=5,
            state="readonly",
        )
        lang_cb.pack(side=tk.RIGHT)
        lang_cb.bind("<<ComboboxSelected>>", self._on_language_change)
        ttk.Label(top_bar, text="🌐 ").pack(side=tk.RIGHT)

        # Notebook (Tabs)
        self.nb = ttk.Notebook(self.root)
        self.nb.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 10))

        self.tab_bot = ttk.Frame(self.nb, padding=16)
        self.tab_model = ttk.Frame(self.nb, padding=16)
        self.tab_gmail = ttk.Frame(self.nb, padding=16)
        self.tab_logs = ttk.Frame(self.nb, padding=16)

        self.nb.add(self.tab_bot, text=self.t("tab_bot"))
        self.nb.add(self.tab_model, text=self.t("tab_model"))
        self.nb.add(self.tab_gmail, text=self.t("tab_gmail"))
        self.nb.add(self.tab_logs, text=self.t("tab_logs"))

        self._build_tab_bot()
        self._build_tab_model()
        self._build_tab_gmail()
        self._build_tab_logs()

    # --- TAB 1: TELEGRAM & SECURITY ---
    def _build_tab_bot(self) -> None:
        f = self.tab_bot

        # Bot Token
        ttk.Label(f, text=self.t("bot_token"), font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 4))
        self.ent_bot_token = ttk.Entry(f, width=64, show="*")
        self.ent_bot_token.pack(anchor=tk.W, pady=(0, 14))

        # Telegram Admin ID
        ttk.Label(f, text=self.t("admin_id"), font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 4))
        self.ent_admin_id = ttk.Entry(f, width=32)
        self.ent_admin_id.pack(anchor=tk.W, pady=(0, 4))

        hint_lbl = ttk.Label(
            f,
            text=self.t("admin_hint"),
            font=("Segoe UI", 8),
            foreground="#64748b",
            wraplength=650,
        )
        hint_lbl.pack(anchor=tk.W, pady=(0, 16))

        # Buttons & Status
        btn_row = ttk.Frame(f)
        btn_row.pack(anchor=tk.W, pady=(0, 16))

        self.btn_save_bot = ttk.Button(btn_row, text=self.t("save_start"), command=self._save_bot)
        self.btn_save_bot.pack(side=tk.LEFT, padx=(0, 10))

        self.lbl_bot_status = ttk.Label(btn_row, text="", font=("Segoe UI", 9, "italic"))
        self.lbl_bot_status.pack(side=tk.LEFT)

        # Autostart checkbox
        self.var_autostart = tk.BooleanVar(value=autostart.is_enabled())
        chk_autostart = ttk.Checkbutton(
            f,
            text=self.t("autostart"),
            variable=self.var_autostart,
            command=self._toggle_autostart,
        )
        chk_autostart.pack(anchor=tk.W, pady=(10, 0))

    def _save_bot(self) -> None:
        token = self.ent_bot_token.get().strip()
        admin_id = self.ent_admin_id.get().strip()
        storage.update_config(telegram_admin_id=admin_id)

        if not token:
            self._info(self.t("saved"))
            return

        self.lbl_bot_status.config(text="Đang kết nối bot...", foreground="#3b82f6")
        self.btn_save_bot.config(state=tk.DISABLED)

        def worker():
            try:
                res = self.app.runtime.set_bot_token(token)
                uname = res.get("username")
                self.app.post(lambda: self._on_bot_saved(uname, res.get("warning")))
            except Exception as exc:
                self.app.post(lambda: self._on_bot_error(str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_bot_saved(self, username: str, warning: str | None) -> None:
        self.btn_save_bot.config(state=tk.NORMAL)
        if username:
            self.lbl_bot_status.config(
                text=self.t("bot_running", u=username), foreground="#16a34a"
            )
        else:
            self.lbl_bot_status.config(text=self.t("saved"), foreground="#16a34a")
        if warning:
            self._warn(warning)
        else:
            self._info(self.t("saved"))

    def _on_bot_error(self, err: str) -> None:
        self.btn_save_bot.config(state=tk.NORMAL)
        self.lbl_bot_status.config(text="Lỗi kết nối", foreground="#dc2626")
        self._err(err)

    def _toggle_autostart(self) -> None:
        autostart.set_enabled(self.var_autostart.get())

    # --- TAB 2: AI MODEL ---
    def _build_tab_model(self) -> None:
        f = self.tab_model

        # Provider
        ttk.Label(f, text=self.t("provider"), font=("Segoe UI", 10, "bold")).grid(
            row=0, column=0, sticky=tk.W, pady=6
        )
        self.cb_provider = ttk.Combobox(
            f,
            values=[PROVIDERS[k][0] for k in PROVIDERS],
            state="readonly",
            width=28,
        )
        self.cb_provider.grid(row=0, column=1, sticky=tk.W, padx=10, pady=6)
        self.cb_provider.bind("<<ComboboxSelected>>", self._on_provider_change)

        # Model
        ttk.Label(f, text=self.t("model"), font=("Segoe UI", 10, "bold")).grid(
            row=1, column=0, sticky=tk.W, pady=6
        )
        self.cb_model = ttk.Combobox(f, width=28)
        self.cb_model.grid(row=1, column=1, sticky=tk.W, padx=10, pady=6)

        # API Key
        ttk.Label(f, text=self.t("api_key"), font=("Segoe UI", 10, "bold")).grid(
            row=2, column=0, sticky=tk.W, pady=6
        )
        self.ent_api_key = ttk.Entry(f, width=45, show="*")
        self.ent_api_key.grid(row=2, column=1, sticky=tk.W, padx=10, pady=6)

        # Temperature
        ttk.Label(f, text=self.t("temperature")).grid(row=3, column=0, sticky=tk.W, pady=6)
        self.ent_temp = ttk.Entry(f, width=15)
        self.ent_temp.grid(row=3, column=1, sticky=tk.W, padx=10, pady=6)

        # Timeout
        ttk.Label(f, text=self.t("timeout")).grid(row=4, column=0, sticky=tk.W, pady=6)
        self.ent_timeout = ttk.Entry(f, width=15)
        self.ent_timeout.grid(row=4, column=1, sticky=tk.W, padx=10, pady=6)

        # Save Button
        btn_save_model = ttk.Button(f, text=self.t("save"), command=self._save_model)
        btn_save_model.grid(row=5, column=1, sticky=tk.W, padx=10, pady=16)

    def _on_provider_change(self, event=None) -> None:
        sel = self.cb_provider.get()
        for k, v in PROVIDERS.items():
            if v[0] == sel:
                self.cb_model["values"] = v[1]
                if v[1]:
                    self.cb_model.set(v[1][0])
                break

    def _save_model(self) -> None:
        sel_label = self.cb_provider.get()
        provider_key = "openai"
        for k, v in PROVIDERS.items():
            if v[0] == sel_label:
                provider_key = k
                break

        fields = {
            "llm_provider": provider_key,
            "llm_model": self.cb_model.get().strip(),
            "llm_temperature": self.ent_temp.get().strip(),
            "llm_timeout": self.ent_timeout.get().strip(),
        }
        key_val = self.ent_api_key.get().strip()
        if key_val:
            fields["llm_api_key"] = key_val

        storage.update_config(**fields)
        self._info(self.t("saved"))

    # --- TAB 3: GMAIL & GOOGLE OAUTH ---
    def _build_tab_gmail(self) -> None:
        f = self.tab_gmail

        ttk.Label(f, text=self.t("gcp_hint"), font=("Segoe UI", 9), foreground="#64748b").pack(
            anchor=tk.W, pady=(0, 6)
        )

        # Paste client_secret.json
        btn_row = ttk.Frame(f)
        btn_row.pack(anchor=tk.W, pady=(0, 12))

        btn_paste_json = ttk.Button(btn_row, text=self.t("paste_json"), command=self._paste_gcp_json)
        btn_paste_json.pack(side=tk.LEFT, padx=(0, 10))

        self.lbl_gcp_info = ttk.Label(btn_row, text="", font=("Segoe UI", 9, "italic"))
        self.lbl_gcp_info.pack(side=tk.LEFT)

        ttk.Separator(f, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        # Gmail Accounts Table
        ttk.Label(f, text=self.t("accounts"), font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 6))

        acct_btn_row = ttk.Frame(f)
        acct_btn_row.pack(anchor=tk.W, pady=(0, 8))

        ttk.Button(acct_btn_row, text=self.t("add_account"), command=self._add_gmail_account).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        ttk.Button(acct_btn_row, text=self.t("set_default"), command=self._set_default_account).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        ttk.Button(acct_btn_row, text=self.t("rename"), command=self._rename_account).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        ttk.Button(acct_btn_row, text=self.t("remove"), command=self._remove_account).pack(
            side=tk.LEFT
        )

        columns = ("label", "email", "default")
        self.tree_accts = ttk.Treeview(f, columns=columns, show="headings", height=6)
        self.tree_accts.heading("label", text=self.t("col_label"))
        self.tree_accts.heading("email", text=self.t("col_email"))
        self.tree_accts.heading("default", text=self.t("col_default"))
        self.tree_accts.column("label", width=140)
        self.tree_accts.column("email", width=280)
        self.tree_accts.column("default", width=100)
        self.tree_accts.pack(fill=tk.BOTH, expand=True)

    def _paste_gcp_json(self) -> None:
        raw = simpledialog.askstring("Google OAuth", "Dán nội dung client_secret.json:")
        if not raw:
            return
        try:
            creds = gmail_client.parse_client_secret_json(raw)
            storage.update_config(
                gcp_client_id=creds["client_id"],
                gcp_client_secret=creds["client_secret"],
            )
            self._load_gcp_info()
            self._info(self.t("saved"))
        except Exception as exc:
            self._err(f"Lỗi phân tích JSON: {exc}")

    def _load_gcp_info(self) -> None:
        cfg = storage.get_config()
        cid = cfg.get("gcp_client_id")
        if cid:
            self.lbl_gcp_info.config(
                text=f"OAuth Client: ...{cid[-16:]}", foreground="#16a34a"
            )
        else:
            self.lbl_gcp_info.config(text="Chưa cấu hình", foreground="#dc2626")

    def _load_accounts(self) -> None:
        for item in self.tree_accts.get_children():
            self.tree_accts.delete(item)
        accounts = storage.list_gmail_accounts()
        for a in accounts:
            star = "⭐ Mặc định" if a["is_default"] else ""
            self.tree_accts.insert("", tk.END, iid=str(a["id"]), values=(a["label"] or "-", a["email"], star))

    def _add_gmail_account(self) -> None:
        cfg = storage.get_config()
        if not (cfg.get("gcp_client_id") and cfg.get("gcp_client_secret")):
            self._err(self.t("need_gcp"))
            return
        try:
            server, url = oauth.start_callback_flow()
            webbrowser.open(url)
            self._info(self.t("opened_browser"))
            # Poll checking for new account
            before = storage.count_gmail_accounts()

            def poll(attempts=60):
                if attempts <= 0:
                    server.stop()
                    return
                if storage.count_gmail_accounts() > before:
                    server.stop()
                    self._load_accounts()
                    self._info(self.t("saved"))
                    return
                self.root.after(2000, lambda: poll(attempts - 1))

            poll()
        except Exception as exc:
            self._err(str(exc))

    def _selected_account_id(self) -> int | None:
        sel = self.tree_accts.selection()
        if not sel:
            return None
        return int(sel[0])

    def _set_default_account(self) -> None:
        aid = self._selected_account_id()
        if aid:
            storage.set_default_gmail_account(aid)
            self._load_accounts()

    def _rename_account(self) -> None:
        aid = self._selected_account_id()
        if not aid:
            return
        new_label = simpledialog.askstring("Đổi nhãn", self.t("label_prompt"))
        if new_label is not None:
            acct = storage.get_gmail_account(aid)
            if acct:
                storage.add_gmail_account(acct["email"], acct["refresh_token"], label=new_label)
                self._load_accounts()

    def _remove_account(self) -> None:
        aid = self._selected_account_id()
        if not aid:
            return
        if messagebox.askyesno("Xác nhận", self.t("confirm_remove")):
            storage.delete_gmail_account(aid)
            self._load_accounts()

    # --- TAB 4: LOGS ---
    def _build_tab_logs(self) -> None:
        f = self.tab_logs

        top_row = ttk.Frame(f)
        top_row.pack(fill=tk.X, pady=(0, 8))

        ttk.Button(top_row, text=self.t("refresh"), command=self._refresh_logs).pack(side=tk.LEFT)
        ttk.Label(top_row, text=" " + self.t("logs_hint"), font=("Segoe UI", 9), foreground="#64748b").pack(
            side=tk.LEFT
        )

        self.txt_logs = ScrolledText(f, wrap=tk.WORD, font=("Consolas", 9), background="#1e293b", foreground="#f8fafc")
        self.txt_logs.pack(fill=tk.BOTH, expand=True)

    def _refresh_logs(self) -> None:
        log_file = config.LOG_DIR / "careermail.log"
        content = ""
        if log_file.is_file():
            try:
                with open(log_file, "r", encoding="utf-8", errors="replace") as lf:
                    lines = lf.readlines()
                    content = "".join(lines[-200:])  # last 200 lines
            except Exception as exc:
                content = f"Không đọc được file log: {exc}"
        else:
            content = "Chưa có log ghi nhận."

        self.txt_logs.delete("1.0", tk.END)
        self.txt_logs.insert(tk.END, content)
        self.txt_logs.see(tk.END)

    # --- HELPERS & DATA LOADING ---
    def _load_data(self) -> None:
        cfg = storage.get_config()
        self.ent_bot_token.insert(0, cfg.get("bot_token") or "")
        self.ent_admin_id.insert(0, cfg.get("telegram_admin_id") or "")

        uname = cfg.get("bot_username")
        if uname:
            self.lbl_bot_status.config(text=self.t("bot_running", u=uname), foreground="#16a34a")
        else:
            self.lbl_bot_status.config(text=self.t("bot_stopped"), foreground="#64748b")

        # Load LLM
        prov = cfg.get("llm_provider") or "openai"
        prov_label = PROVIDERS.get(prov, PROVIDERS["openai"])[0]
        self.cb_provider.set(prov_label)
        self._on_provider_change()
        if cfg.get("llm_model"):
            self.cb_model.set(cfg.get("llm_model"))
        self.ent_api_key.insert(0, cfg.get("llm_api_key") or "")
        self.ent_temp.insert(0, cfg.get("llm_temperature") or "0.2")
        self.ent_timeout.insert(0, cfg.get("llm_timeout") or "30")

        self._load_gcp_info()
        self._load_accounts()
        self._refresh_logs()

    def _on_language_change(self, event=None) -> None:
        new_lang = self._lang_var.get()
        storage.update_config(ui_language=new_lang)
        self._info("Vui lòng khởi động lại ứng dụng để áp dụng toàn bộ ngôn ngữ mới.")

    def _info(self, msg: str) -> None:
        messagebox.showinfo(self.t("info"), msg)

    def _warn(self, msg: str) -> None:
        messagebox.showwarning(self.t("info"), msg)

    def _err(self, msg: str) -> None:
        messagebox.showerror(self.t("error"), msg)
