from fastapi import HTTPException


_ALLOWED_TRANSITIONS: dict[tuple[str, str], dict[str, frozenset[str]]] = {
    ("review", "need_info"): {"bank": frozenset({"request_info"})},
    ("review", "offer"): {
        "bank": frozenset({"approve", "alternative"}),
    },
    ("review", "rejected"): {"bank": frozenset({"reject"})},
    ("need_info", "review"): {"client": frozenset({"provide_info"})},
    ("offer", "sign"): {"client": frozenset({"accept_offer"})},
    ("offer", "rejected"): {
        "client": frozenset({"decline_offer"}),
        "bank": frozenset({"reject"}),
    },
    ("sign", "ready"): {"client": frozenset({"sign"})},
    ("ready", "disbursed"): {"client": frozenset({"disburse"})},
}


def ensure_application_transition(
    current_status: str,
    new_status: str,
    role: str,
    action: str,
) -> None:
    current = getattr(current_status, "value", current_status)
    target = getattr(new_status, "value", new_status)
    role_actions = _ALLOWED_TRANSITIONS.get((current, target), {})
    if action not in role_actions.get(role, frozenset()):
        raise HTTPException(
            status_code=409,
            detail={
                "code": "INVALID_STATUS_TRANSITION",
                "message": (
                    f"Переход заявки из статуса «{current}» в «{target}» "
                    f"недопустим для действия «{action}»."
                ),
            },
        )
