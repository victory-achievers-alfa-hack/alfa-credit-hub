from sqlalchemy.orm import Session


def get_user_data(user_id: int, db: Session) -> dict:
    pass

def get_user_companies(user_id: int, db: Session) -> list[dict]:
    pass