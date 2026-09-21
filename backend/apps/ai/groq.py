import json
import os
import urllib.error
import urllib.request

from django.conf import settings

from apps.core.services.dashboard import serialize_decimal
from apps.core.services.nl import parse_natural_language


def _looks_like_add(text: str) -> bool:
    lowered = text.lower()
    return lowered.startswith("add ") or "add a" in lowered or (
        "expense" in lowered and any(ch.isdigit() for ch in lowered)
    )


def snapshot_for_prompt(user, message: str) -> dict:
    from apps.ai.engine import finance_tools

    tools = finance_tools(user)
    profile = user.profile
    payload = {
        "person": profile.display_name or user.get_full_name() or user.username,
        "currency": profile.currency,
        "currency_symbol": profile.currency_symbol,
        "this_month": serialize_decimal(tools["totals"]()),
        "subscriptions": serialize_decimal(tools["subscriptions"]()),
        "lending": serialize_decimal(tools["lending"]()),
        "bills": serialize_decimal(tools["bills"]()),
        "biggest_expenses": serialize_decimal(tools["biggest_expenses"]()),
        "spending": {
            "food": serialize_decimal(tools["spending"]("Food")),
            "transport": serialize_decimal(tools["spending"]("Transport")),
            "shopping": serialize_decimal(tools["spending"]("Shopping")),
            "all": serialize_decimal(tools["spending"](None)),
        },
    }
    if _looks_like_add(message):
        payload["transaction_draft"] = parse_natural_language(user, message)
    return payload


SYSTEM_PROMPT = """You are MONEA, a private personal finance assistant for this one user.
Answer only from the JSON snapshot. Never invent amounts, merchants, dates, or accounts.
If the snapshot does not contain the answer, say you do not have that data yet.
Do not give regulated financial advice or investment recommendations.
Keep replies concise and specific. Amounts should use the provided currency symbol.
If transaction_draft is present and ok, present it for confirmation and do not claim it is saved.
"""


def answer_with_groq(user, message: str) -> dict | None:
    api_key = (settings.AI_API_KEY or "").strip()
    if not api_key:
        return None
    snapshot = snapshot_for_prompt(user, message)
    body = {
        "model": settings.AI_MODEL,
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Snapshot:\n{json.dumps(snapshot, default=str)}\n\n"
                    f"Question:\n{message}"
                ),
            },
        ],
    }
    endpoint = settings.AI_API_BASE.rstrip("/") + "/chat/completions"
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "MONEA/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"The assistant could not reach Groq right now. ({exc.code})") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError("The assistant is offline. Please try again.") from exc

    choices = payload.get("choices") or []
    if not choices:
        return None
    reply = (choices[0].get("message") or {}).get("content") or ""
    draft = None
    parsed = snapshot.get("transaction_draft") or {}
    if parsed.get("ok") and parsed.get("draft"):
        draft = parsed["draft"]
    return {
        "reply": reply.strip(),
        "draft": draft,
        "needs_confirmation": bool(draft),
        "data": snapshot,
        "source": "groq",
    }
