"""Deterministic next steps tied to observed restrictions, without score promises."""
from typing import Any, Mapping
from decimal import Decimal


def format_rubles(value) -> str:
    return f"{Decimal(str(value)):,.2f}".replace(",", " ").replace(".", ",") + " ₽"

DOCUMENT_NAMES = {
    "registry": "сведения реестра", "statement": "выписку по счёту",
    "reporting": "финансовую отчётность", "bki": "сведения БКИ",
}


def next_actions(company: Mapping[str, Any], result: Mapping[str, Any]) -> list[dict]:
    actions = []
    codes = {reason["code"] for reason in result["reasons"]}

    def add(code, title, message, **values):
        actions.append(dict(code=code, title=title, message=message, **values))

    if "INACTIVE_COMPANY" in codes:
        add("CHECK_REGISTRY", "Уточнить статус компании", "Проверьте сведения реестра с банком. Пока компания не действует, сумма и срок не снимают ограничение.")
    if "CURRENT_OVERDUE" in codes:
        add("RESOLVE_OVERDUE", "Уточнить текущую просрочку", "Урегулируйте задолженность или оспорьте ошибочные сведения через банк. После обновления источника потребуется новый расчёт.")
    if "DOCUMENTS_REQUIRED" in codes:
        ready = {d.get("kind", d["id"]) for d in (company.get("documents") or []) if d.get("status") in ("ready", "verified")}
        for kind, name in DOCUMENT_NAMES.items():
            if kind not in ready:
                add("PROVIDE_DOCUMENT", "Предоставить " + name, "Передайте документ на проверку сотруднику. Сам факт загрузки не снимает ограничение.", documentKind=kind)
    if "SCORE_TOO_LOW" in codes:
        add("VERIFY_PROFILE", "Проверить исходные данные", "По текущему профилю предложение недоступно. Проверьте корректность финансов с банком; изменение суммы не повышает балл компании.")
    if "PURPOSE_MISMATCH" in codes:
        add("CHANGE_PRODUCT", "Выбрать продукт под цель", "Вернитесь к подбору и выберите продукт, поддерживающий указанную цель финансирования.")
    if "TERM_UNSUPPORTED" in codes:
        add("CHANGE_TERM", "Выбрать срок из каталога", "Доступные сроки: " + ", ".join(map(str, result["constraints"]["allowedTerms"])) + " мес. Выберите срок и повторите расчёт.", allowedTerms=result["constraints"]["allowedTerms"])
    alternative = result.get("alternative")
    if alternative:
        add("REDUCE_AMOUNT", "Рассмотреть меньшую сумму", f"На этом сроке рассчитано {format_rubles(alternative['amount'])} вместо {format_rubles(result['amount'])}. Проверьте, покрывает ли сумма вашу потребность. Решение остаётся за банком.", amount=alternative["amount"], termMonths=alternative["termMonths"])
    elif not codes.intersection({"INACTIVE_COMPANY", "CURRENT_OVERDUE", "SCORE_TOO_LOW"}) and ("INSUFFICIENT_COVERAGE" in codes or "REVIEW_AMOUNT_LIMIT" in codes):
        add("RECALCULATE_TERMS", "Пересчитать условия", "В текущих условиях нет проходящего предложения. В подборе можно проверить другие сроки и суммы; доступность подтвердит повторный расчёт.")
    elif "AMOUNT_OUT_OF_RANGE" in codes:
        add("CHANGE_AMOUNT", "Выбрать сумму из каталога", f"Диапазон продукта: от {format_rubles(result['constraints']['productMinAmount'])} до {format_rubles(result['constraints']['productMaxAmount'])}. Вы запросили {format_rubles(result['amount'])}. Увеличивать потребность ради минимума продукта не требуется: можно выбрать другой продукт.", minimumAmount=result["constraints"]["productMinAmount"], maximumAmount=result["constraints"]["productMaxAmount"])
    if result["reviewRequired"] and result["policyPasses"]:
        add("BANK_REVIEW", "Передать на рассмотрение", "Условия проходят ограничения диапазона 50–69. Сотрудник должен проверить сведения и обосновать решение; это не предварительное одобрение.")
    if result["eligible"]:
        add("SUBMIT_APPLICATION", "Проверить и отправить заявку", "Условия проходят предварительные правила. Проверьте сумму, срок и платёж; банк рассмотрит заявку отдельно.")
    return actions
