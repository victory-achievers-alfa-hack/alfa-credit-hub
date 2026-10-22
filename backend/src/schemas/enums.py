from enum import Enum

class UserRole(str, Enum):
    CLIENT = "client"
    BANK = "bank"

class CreditGoal(str, Enum):
    STOCK = "stock"          # Закупка товаров
    EQUIPMENT = "equipment"  # Оборудование и развитие
    GAP = "gap"              # Кассовый разрыв

class ApplicationStatus(str, Enum):
    REVIEW = "review"        # На рассмотрении
    NEED_INFO = "need_info"  # Нужны сведения
    OFFER = "offer"          # Предложение готово
    SIGN = "sign"            # Ожидает подписания
    READY = "ready"          # Готов к выдаче
    DISBURSED = "disbursed"  # Кредит выдан
    REJECTED = "rejected"    # Отказ

class BankDecisionAction(str, Enum):
    APPROVE = "approve"      # Одобрить полную сумму
    COUNTER = "counter"      # Предложить альтернативную сумму
    NEED_INFO = "need_info"  # Запросить сведения
    REJECT = "reject"        # Отказать