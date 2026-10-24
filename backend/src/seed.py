from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from backend.src.auth import hash_password
from backend.src.models import (
    Application,
    ApplicationCheck,
    ApplicationEvent,
    Company,
    CompanyDocument,
    CreditProduct,
    Notification,
    OfferDecision,
    SCORING_POLICY_VERSION,
    ScoringRule,
    User,
)
from backend.src.scoring.rules import MODEL_VERSION


_DOCUMENTS = (
    {
        "id": "registry",
        "name": "Выписка ЕГРЮЛ / ЕГРИП",
        "description": "Сведения о регистрации и видах деятельности",
        "kind": "registry",
        "status": "ready",
        "updated_at": datetime(2026, 10, 21, tzinfo=timezone.utc),
    },
    {
        "id": "statement",
        "name": "Выписка по расчётному счёту",
        "description": "Операции за последние 12 месяцев",
        "kind": "statement",
        "status": "ready",
        "updated_at": datetime(2026, 10, 21, tzinfo=timezone.utc),
    },
    {
        "id": "reporting",
        "name": "Финансовая отчётность",
        "description": "Синтетический комплект для демонстрации",
        "kind": "reporting",
        "status": "ready",
        "updated_at": datetime(2026, 10, 20, tzinfo=timezone.utc),
    },
    {
        "id": "bki",
        "name": "Сведения БКИ",
        "description": "Кредитная история компании",
        "kind": "bki",
        "status": "ready",
        "updated_at": datetime(2026, 10, 21, tzinfo=timezone.utc),
    },
)

_COMPANIES = (
    {
        "id": "city",
        "name": "Магазин «Город»",
        "legal_name": "ООО «Магазин Город»",
        "inn": "7701234567",
        "okved": "47.11 — Розничная торговля продуктами",
        "sector": "retail",
        "registration_date": date(2019, 3, 18),
        "account": "40702 •••• •••• 1842",
        "representative": "Соколов Алексей Игоревич",
        "monthly_revenue": Decimal("900000"),
        "monthly_expenses": Decimal("740000"),
        "current_monthly_debt_payment": Decimal("120000"),
        "has_overdue": False,
        "scoring_score": 75,
        "status": "active",
        "turnover": [760000, 790000, 810000, 830000, 850000, 870000, 890000, 900000, 910000, 900000, 900000, 900000],
    },
    {
        "id": "cafe",
        "name": "Кофейня «Зёрна»",
        "legal_name": "ООО «Зёрна»",
        "inn": "7702345678",
        "okved": "56.10 — Деятельность ресторанов и кафе",
        "sector": "food_service",
        "registration_date": date(2018, 7, 4),
        "account": "40702 •••• •••• 5721",
        "representative": "Орлова Марина Сергеевна",
        "monthly_revenue": Decimal("1200000"),
        "monthly_expenses": Decimal("850000"),
        "current_monthly_debt_payment": Decimal("70000"),
        "has_overdue": False,
        "scoring_score": 88,
        "status": "active",
        "turnover": [950000, 980000, 1010000, 1040000, 1080000, 1100000, 1130000, 1150000, 1180000, 1200000, 1200000, 1200000],
    },
    {
        "id": "vector",
        "name": "ООО «Вектор»",
        "legal_name": "ООО «Вектор»",
        "inn": "7703456789",
        "okved": "46.69 — Оптовая торговля оборудованием",
        "sector": "wholesale",
        "registration_date": date(2025, 5, 12),
        "account": "40702 •••• •••• 9015",
        "representative": "Векторов Дмитрий Олегович",
        "monthly_revenue": Decimal("500000"),
        "monthly_expenses": Decimal("490000"),
        "current_monthly_debt_payment": Decimal("90000"),
        "has_overdue": True,
        "scoring_score": 38,
        "status": "active",
        "turnover": [420000, 440000, 450000, 470000, 480000, 490000, 510000, 500000, 510000, 500000, 500000, 500000],
    },
)

_PRODUCTS = (
    {
        "id": "working-capital",
        "name": "Оборотный кредит",
        "short_name": "Оборотный",
        "description": "На закупку товаров и пополнение оборотных средств",
        "purposes": ["goods", "cash_gap"],
        "min_amount": Decimal("100000"),
        "max_amount": Decimal("3000000"),
        "terms": [12, 24, 36],
        "rate": Decimal("24"),
        "accent": "red",
    },
    {
        "id": "investment",
        "name": "Инвестиционный кредит",
        "short_name": "Инвестиционный",
        "description": "На оборудование, модернизацию и развитие бизнеса",
        "purposes": ["equipment"],
        "min_amount": Decimal("300000"),
        "max_amount": Decimal("5000000"),
        "terms": [12, 24, 36, 48, 60],
        "rate": Decimal("22"),
        "accent": "purple",
    },
    {
        "id": "express",
        "name": "Экспресс-кредит",
        "short_name": "Экспресс",
        "description": "Быстрое решение для любой из бизнес-задач",
        "purposes": ["goods", "equipment", "cash_gap"],
        "min_amount": Decimal("50000"),
        "max_amount": Decimal("1000000"),
        "terms": [12, 24],
        "rate": Decimal("29"),
        "accent": "blue",
    },
)

_USERS = (
    {
        "public_id": "client-city",
        "email": "client@demo.ru",
        "role": "client",
        "contact_name": "Алексей Соколов",
        "initials": "АС",
        "company_id": "city",
    },
    {
        "public_id": "client-cafe",
        "email": "cafe@demo.ru",
        "role": "client",
        "contact_name": "Марина Орлова",
        "initials": "МО",
        "company_id": "cafe",
    },
    {
        "public_id": "client-vector",
        "email": "vector@demo.ru",
        "role": "client",
        "contact_name": "Дмитрий Векторов",
        "initials": "ДВ",
        "company_id": "vector",
    },
    {
        "public_id": "bank-underwriter",
        "email": "bank@demo.ru",
        "role": "bank",
        "contact_name": "Анна Белова",
        "initials": "АБ",
        "company_id": None,
    },
)

_APPLICATIONS = (
    {
        "id": "APP-2026-001",
        "company_id": "city",
        "product_id": "working-capital",
        "purpose": "goods",
        "amount": Decimal("800000"),
        "term_months": 24,
        "status": "offer",
        "created_at": datetime(2026, 10, 21, 9, 15, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 10, 22, 10, 25, tzinfo=timezone.utc),
        "event_ids": ("EV-001", "EV-002"),
    },
    {
        "id": "APP-2026-002",
        "company_id": "cafe",
        "product_id": "investment",
        "purpose": "equipment",
        "amount": Decimal("1000000"),
        "term_months": 36,
        "status": "review",
        "created_at": datetime(2026, 10, 22, 8, 40, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 10, 22, 8, 40, tzinfo=timezone.utc),
        "event_ids": ("EV-003",),
    },
    {
        "id": "APP-2026-003",
        "company_id": "vector",
        "product_id": "express",
        "purpose": "cash_gap",
        "amount": Decimal("500000"),
        "term_months": 12,
        "status": "review",
        "created_at": datetime(2026, 10, 22, 11, 5, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 10, 22, 11, 5, tzinfo=timezone.utc),
        "event_ids": ("EV-004",),
    },
)

_APP_EVENTS = (
    {
        "id": "EV-001",
        "application_id": "APP-2026-001",
        "old_status": None,
        "new_status": "review",
        "actor_email": "client@demo.ru",
        "actor_role": "client",
        "event_type": "submitted",
        "title": "Заявка отправлена",
        "description": "Данные переданы на рассмотрение в банк.",
        "created_at": datetime(2026, 10, 21, 9, 15, tzinfo=timezone.utc),
    },
    {
        "id": "EV-002",
        "application_id": "APP-2026-001",
        "old_status": "review",
        "new_status": "offer",
        "actor_email": "bank@demo.ru",
        "actor_role": "bank",
        "event_type": "offer_created",
        "title": "Банк предложил другие условия",
        "description": "Доступно предложение на 150 000 ₽.",
        "created_at": datetime(2026, 10, 22, 10, 25, tzinfo=timezone.utc),
    },
    {
        "id": "EV-003",
        "application_id": "APP-2026-002",
        "old_status": None,
        "new_status": "review",
        "actor_email": "cafe@demo.ru",
        "actor_role": "client",
        "event_type": "submitted",
        "title": "Заявка отправлена",
        "description": "Проверки выполнены, заявка ожидает решения.",
        "created_at": datetime(2026, 10, 22, 8, 40, tzinfo=timezone.utc),
    },
    {
        "id": "EV-004",
        "application_id": "APP-2026-003",
        "old_status": None,
        "new_status": "review",
        "actor_email": "vector@demo.ru",
        "actor_role": "client",
        "event_type": "submitted",
        "title": "Заявка отправлена",
        "description": "Обнаружены факторы, требующие ручного решения.",
        "created_at": datetime(2026, 10, 22, 11, 5, tzinfo=timezone.utc),
    },
)


def _money(value: Decimal | int | float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"))


def _monthly_payment(amount: Decimal, rate: Decimal, term: int) -> Decimal:
    monthly_rate = rate / Decimal("1200")
    payment = amount / term if monthly_rate == 0 else (
        amount * monthly_rate / (1 - (1 + monthly_rate) ** -term)
    )
    # The frontend demo calculates whole-ruble monthly payments with Math.round.
    return payment.quantize(Decimal("1"), rounding="ROUND_HALF_UP")


def _factor_data(company: Company, operating_flow: Decimal) -> list[dict]:
    tenure_positive = company.registration_date.year <= 2023
    flow_display = f"{operating_flow:,.0f}".replace(",", " ")
    return [
        {
            "label": "История платежей",
            "value": "Есть просрочки" if company.has_overdue else "Без просрочек",
            "positive": not company.has_overdue,
        },
        {
            "label": "Операционный поток",
            "value": f"{flow_display} ₽/мес.",
            "positive": operating_flow > company.current_monthly_debt_payment,
        },
        {
            "label": "Возраст бизнеса",
            "value": "Более 3 лет" if tenure_positive else "Менее 3 лет",
            "positive": tenure_positive,
        },
    ]


def _check_data(company: Company, coverage: Decimal) -> list[dict]:
    docs_ready = all(document.status == "ready" for document in company.documents)
    return [
        {
            "id": "registry",
            "label": "Реестр компаний",
            "value": "Компания действует" if company.active else "Есть ограничения",
            "description": "Статус и реквизиты сверены с синтетическим реестром",
            "state": "success" if company.active else "error",
        },
        {
            "id": "bki",
            "label": "Кредитная история",
            "value": "Есть просрочки" if company.has_overdue else "Без просрочек",
            "description": "Результат локального симулятора БКИ",
            "state": "error" if company.has_overdue else "success",
        },
        {
            "id": "documents",
            "label": "Комплект документов",
            "value": "Полный комплект" if docs_ready else "Нужно уточнение",
            "description": "Проверены синтетические документы компании",
            "state": "success" if docs_ready else "warning",
        },
        {
            "id": "coverage",
            "label": "Покрытие платежей",
            "value": f"{coverage:.2f}×",
            "description": "Порог автоматического предварительного прохождения — 1,25×",
            "state": "success" if coverage >= Decimal("1.25") else "warning",
        },
    ]


def seed_demo_data(db: Session) -> None:
    """Insert missing demo records; safe to call repeatedly."""
    if db.get(ScoringRule, SCORING_POLICY_VERSION) is None:
        db.add(
            ScoringRule(
                version=SCORING_POLICY_VERSION,
                parameters={"modelVersion": MODEL_VERSION},
            )
        )
        db.flush()

    for data in _COMPANIES:
        if db.get(Company, data["id"]) is None:
            db.add(Company(**data))
    db.flush()

    for company_id in ("city", "cafe", "vector"):
        for document in _DOCUMENTS:
            document_id = f"{document['id']}-{company_id}"
            if db.get(CompanyDocument, document_id) is not None:
                continue
            status_value = (
                "attention"
                if company_id == "vector" and document["id"] == "bki"
                else document["status"]
            )
            description = (
                "Зафиксированы просрочки в кредитной истории"
                if company_id == "vector" and document["id"] == "bki"
                else document["description"]
            )
            db.add(
                CompanyDocument(
                    id=document_id,
                    company_id=company_id,
                    name=document["name"],
                    description=description,
                    kind=document["kind"],
                    status=status_value,
                    updated_at=document["updated_at"],
                )
            )

    for data in _PRODUCTS:
        if db.get(CreditProduct, data["id"]) is None:
            db.add(CreditProduct(**data))
    db.flush()

    password_hash: str | None = None
    users_by_email: dict[str, User] = {}
    for data in _USERS:
        user = db.query(User).filter(User.email == data["email"]).one_or_none()
        if user is None:
            if password_hash is None:
                password_hash = hash_password("123456")
            user = User(password_hash=password_hash, **data)
            db.add(user)
            db.flush()
        users_by_email[data["email"]] = user

    companies = {company.id: company for company in db.query(Company).all()}
    products = {product.id: product for product in db.query(CreditProduct).all()}
    for data in _APPLICATIONS:
        application = db.get(Application, data["id"])
        company = companies[data["company_id"]]
        product = products[data["product_id"]]
        payment = _monthly_payment(data["amount"], product.rate, data["term_months"])
        operating_flow = company.monthly_revenue - company.monthly_expenses
        coverage = operating_flow / (company.current_monthly_debt_payment + payment)

        if application is None:
            application = Application(
                id=data["id"],
                company_id=company.id,
                product_id=product.id,
                created_by_user_id=users_by_email[
                    {"city": "client@demo.ru", "cafe": "cafe@demo.ru", "vector": "vector@demo.ru"}[company.id]
                ].id,
                purpose=data["purpose"],
                amount=data["amount"],
                term_months=data["term_months"],
                requested_rate=product.rate,
                status=data["status"],
                created_at=data["created_at"],
                updated_at=data["updated_at"],
            )
            db.add(application)
            db.flush()

        if not db.query(ApplicationCheck).filter_by(application_id=application.id).first():
            factors = _factor_data(company, operating_flow)
            risk = "low" if company.scoring_score >= 70 else "medium" if company.scoring_score >= 50 else "high"
            summary = (
                "Профиль устойчивый. Итог зависит от покрытия платежей по выбранной сумме."
                if risk == "low"
                else "Есть факторы риска — требуется решение сотрудника банка."
                if risk == "medium"
                else "Высокая нагрузка или просрочки требуют отказа либо ручного рассмотрения."
            )
            db.add(
                ApplicationCheck(
                    id=f"CHECK-{application.id[-3:]}",
                    application_id=application.id,
                    rules_version=SCORING_POLICY_VERSION,
                    score=company.scoring_score,
                    risk=risk,
                    rate=product.rate,
                    coverage=coverage,
                    monthly_payment=payment,
                    max_available_amount=product.max_amount,
                    eligible=not company.has_overdue and company.scoring_score >= 70 and coverage >= Decimal("1.25"),
                    explanation=summary,
                    input_data={
                        "monthlyRevenue": str(company.monthly_revenue),
                        "monthlyExpenses": str(company.monthly_expenses),
                        "existingPayments": str(company.current_monthly_debt_payment),
                        "hasOverdue": company.has_overdue,
                    },
                    factors=factors,
                    checks=_check_data(company, coverage),
                    created_at=data["updated_at"],
                )
            )

    db.flush()
    if db.get(OfferDecision, "OFF-2026-001") is None:
        db.add(
            OfferDecision(
                id="OFF-2026-001",
                application_id="APP-2026-001",
                actor_id=users_by_email["bank@demo.ru"].id,
                kind="alternative",
                amount=Decimal("150000"),
                rate=Decimal("24"),
                term_months=24,
                comment="Сумма снижена, чтобы коэффициент покрытия достиг безопасного уровня 1,25×.",
                created_at=datetime(2026, 10, 22, 10, 25, tzinfo=timezone.utc),
            )
        )

    for data in _APP_EVENTS:
        if db.get(ApplicationEvent, data["id"]) is None:
            actor = users_by_email[data["actor_email"]]
            db.add(
                ApplicationEvent(
                    **{key: value for key, value in data.items() if key != "actor_email"},
                    actor_id=actor.id,
                )
            )

    if db.get(Notification, "NOTIFICATION-2026-001") is None:
        db.add(
            Notification(
                id="NOTIFICATION-2026-001",
                user_id=users_by_email["client@demo.ru"].id,
                company_id="city",
                application_id="APP-2026-001",
                type="warning",
                title="Банк предложил новые условия",
                text="По заявке APP-2026-001 доступно предложение на 150 000 ₽.",
                created_at=datetime(2026, 10, 22, 10, 25, tzinfo=timezone.utc),
            )
        )

    db.commit()
