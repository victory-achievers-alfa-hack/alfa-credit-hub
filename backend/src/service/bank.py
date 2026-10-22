from sqlalchemy.orm import Session


def get_bank_applications(db: Session) -> list[dict]:
    pass


def get_bank_application_by_id(id: int, db: Session) -> dict:
    pass


def make_bank_decision(id: int, db: Session) -> dict:
    pass