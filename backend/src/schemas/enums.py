from enum import Enum


class UserRole(str, Enum):
    CLIENT = "client"
    BANK = "bank"


class CreditGoal(str, Enum):
    GOODS = "goods"  # Закупка товаров
    EQUIPMENT = "equipment"  # Оборудование и развитие
    GAP = "cash_gap"  # Кассовый разрыв


class ApplicationStatus(str, Enum):
    REVIEW = "review"  # На рассмотрении
    NEED_INFO = "need_info"  # Нужны сведения
    OFFER = "offer"  # Предложение готово
    SIGN = "sign"  # Ожидает подписания
    READY = "ready"  # Готов к выдаче
    DISBURSED = "disbursed"  # Кредит выдан
    REJECTED = "rejected"  # Отказ


class BankDecisionKind(str, Enum):
    APPROVE = "approve"
    ALTERNATIVE = "alternative"
    NEED_INFO = "need_info"
    REJECT = "reject"
