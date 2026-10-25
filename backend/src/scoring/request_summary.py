"""Describe exact request matches separately from changed financing conditions."""
from .actions import format_rubles


def summarize_request(checks, groups, amount, term_months):
    exact = sum(check["assessment"] == "eligible" for check in checks)
    review = sum(check["policyPasses"] and check["reviewRequired"] for check in checks)
    other_terms = reduced = 0
    for items in groups.values():
        for item in items:
            if not item["selectedEvaluation"]["policyPasses"]:
                continue
            if item["offer"]["amount"] < amount:
                reduced += 1
            elif item["offer"]["amount"] == amount and item["termChanged"]:
                other_terms += 1
    context = f"{format_rubles(amount)} на {term_months} мес."
    if exact:
        status = "exact_available"
        message = f"Для запроса {context} найдены варианты, проходящие предварительные правила. Решение принимает банк."
    elif review:
        status = "exact_review"
        message = f"Для запроса {context} есть варианты только для рассмотрения сотрудником банка. Стандартного предварительного прохождения нет."
    elif other_terms or reduced:
        status = "alternatives_available"
        message = f"Для запроса {context} проходящих вариантов нет. Найдены альтернативы с изменёнными суммой или сроком; исходный запрос не изменён."
    elif any(check["assessment"] == "need_info" for check in checks):
        status = "information_required"
        message = f"Для запроса {context} необходимо уточнить сведения. Проходящие условия пока не подтверждены."
    else:
        status = "unavailable"
        message = f"Для запроса {context} проходящих вариантов и доступных альтернатив в текущем каталоге нет. Причины указаны в проверках продуктов."
    return dict(status=status, message=message, exactMatchCount=exact,
                exactReviewCount=review, otherTermCount=other_terms,
                reducedAmountCount=reduced)
