from careermail.core import storage

PROVIDER_KEYS = {"openai", "deepseek", "anthropic", "google_genai"}

_http_client = None


def _get_http_client():
    global _http_client
    if _http_client is None:
        try:
            import httpx

            _http_client = httpx.Client(headers={"Accept-Encoding": "gzip, deflate"})
        except Exception:
            _http_client = False
    return _http_client or None


def _to_float(value, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def build_model():
    from langchain.chat_models import init_chat_model

    cfg = storage.get_config()
    api_key = cfg.get("llm_api_key")
    if not api_key:
        return None

    provider = cfg.get("llm_provider") or "openai"
    if provider not in PROVIDER_KEYS:
        provider = "openai"
    model = cfg.get("llm_model") or ""

    kwargs = {
        "api_key": api_key,
        "temperature": _to_float(cfg.get("llm_temperature"), 0.2),
        "timeout": _to_int(cfg.get("llm_timeout"), 30),
        "max_tokens": _to_int(cfg.get("llm_max_tokens"), 1500),
        "max_retries": _to_int(cfg.get("llm_max_retries"), 2),
    }

    if provider in ("openai", "deepseek"):
        client = _get_http_client()
        if client is not None:
            kwargs["http_client"] = client

    return init_chat_model(model=model, model_provider=provider, **kwargs)
