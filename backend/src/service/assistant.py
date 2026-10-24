from backend.src.models import CreditProduct
from backend.src.schemas import assistant as assistant_schemas
from sqlalchemy import select
from sqlalchemy.orm import Session


def chat_to_assistant(
    question: assistant_schemas.AssistantChatRequest, db: Session
) -> assistant_schemas.AssistantChatResponse:
    question = question.question.strip()
    normalized = question.casefold().replace("ё", "е")

    if any(
        word in normalized
        for word in ("альтернатив", "уменьш", "снизил сумму", "другую сумму")
    ):
        answer = (
            "Альтернативную сумму предлагают, когда запрошенный платёж не проходит "
            "проверку доступной долговой нагрузки или коэффициента покрытия. Банк "
            "подбирает меньшую сумму так, чтобы платёж соответствовал денежному потоку "
            "компании и условиям продукта. Точные причины и параметры решения указаны "
            "в комментарии к предложению по заявке."
        )
    elif any(word in normalized for word in ("покрыт", "1,25", "1.25", "коэффициент")):
        answer = (
            "Коэффициент покрытия показывает, во сколько раз свободный денежный поток "
            "компании превышает ежемесячные долговые платежи с учётом нового кредита. "
            "В этой модели он рассчитывается как (выручка − расходы) / "
            "(текущие платежи по долгам + платёж по новому кредиту). Требование 1,25× "
            "означает, что на каждый рубль платежей должно приходиться не менее 1,25 ₽ "
            "свободного денежного потока."
        )
    elif any(
        word in normalized
        for word in ("статус", "этап", "review", "need_info", "offer", "disbursed")
    ):
        answer = (
            "Статусы заявки: «На рассмотрении» (review) — банк проверяет заявку; "
            "«Нужны документы» (need_info) — клиенту нужно дополнить данные; "
            "«Предложение» (offer) — банк сформировал условия; «Подписание» (sign) — "
            "клиент подписывает договор; «Готова к выдаче» (ready) — договор оформлен; "
            "«Выдана» (disbursed) — средства перечислены; «Отказ» (rejected) — заявка "
            "закрыта без выдачи."
        )
    elif any(
        word in normalized
        for word in (
            "продукт",
            "ставк",
            "услов",
            "кредит",
            "working-capital",
            "investment",
            "express",
        )
    ):
        answer = _product_answer(normalized, db)
    else:
        answer = (
            "Я могу объяснить, почему банк предложил другую сумму, как рассчитывается "
            "коэффициент покрытия 1,25×, что означают статусы заявки и какие условия "
            "есть у кредитных продуктов."
        )

    return assistant_schemas.AssistantChatResponse(answer=answer)


def _product_answer(question: str, db: Session) -> str:
    products = db.scalars(select(CreditProduct).order_by(CreditProduct.name)).all()
    if not products:
        return "Каталог кредитных продуктов пока пуст. Попробуйте обратиться позже."

    matches = [
        product
        for product in products
        if product.id.casefold() in question
        or product.name.casefold() in question
        or product.short_name.casefold() in question
    ]
    selected = matches or products
    lines = ["Условия кредитных продуктов из каталога:"]
    for product in selected:
        terms = ", ".join(f"{term} мес." for term in product.terms)
        purposes = ", ".join(_purpose_label(purpose) for purpose in product.purposes)
        lines.append(
            f"{product.name}: {product.min_amount:,.0f}–{product.max_amount:,.0f} ₽, "
            f"ставка {product.rate}% годовых, срок {terms}; {product.description}. "
            f"Цели: {purposes}."
        )
    return "\n".join(lines)


def _purpose_label(purpose: str) -> str:
    return {
        "goods": "закупка товаров",
        "equipment": "оборудование и развитие",
        "cash_gap": "пополнение оборотных средств",
    }.get(purpose, purpose)
