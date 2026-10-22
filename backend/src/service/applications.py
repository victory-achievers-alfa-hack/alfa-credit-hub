from sqlalchemy.orm import Session


def get_applications(company_id: int, db: Session) -> list[dict]:
    pass


def set_application(company_id: int, db: Session) -> list[dict]:
    pass


def get_application_by_id(id: int, db: Session) -> dict:
    pass


def provide_application_info(id: int, db: Session) -> dict:
    pass


def accept_application(id: int, db: Session) -> dict:
    pass


def sign_application(id: int, db: Session) -> dict:
    pass


def disburse_application(id: int, db: Session) -> dict:
    pass