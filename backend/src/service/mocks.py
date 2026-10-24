from sqlalchemy.orm import Session

from backend.src.schemas import mocks as mocks_schemas


def get_mock_fns_check(inn: int, db: Session) -> mocks_schemas.FnsMockResponse:
    pass


def get_mock_bki_check(inn: int, db: Session) -> mocks_schemas.BkiMockResponse:
    pass
