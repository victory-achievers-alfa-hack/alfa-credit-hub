"""Deterministic demonstration scoring, independent of storage and HTTP."""

from .rules import InputError, score_company
from .financing import assess_financing, loan_quote
from .ranking import recommend_financing

__all__ = ["InputError", "score_company", "assess_financing", "loan_quote", "recommend_financing"]
