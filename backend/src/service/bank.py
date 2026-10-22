from sqlalchemy.orm import Session

from backend.src.schemas import bank as bank_schemas


def get_bank_applications(db: Session) -> list[bank_schemas.BankCheckItem]:
    pass


def get_bank_application_by_id(id: int, db: Session) -> bank_schemas.BankApplicationDetailResponse:
    pass


def make_bank_decision(id: int, db: Session) -> bank_schemas.BankDecisionRequest:
    pass