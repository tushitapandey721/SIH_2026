"""Formulation classification decision tree module for Ayurveda and related products:
- Classical Medicine
- Proprietary Medicine
- New Drug
- Phytopharmaceutical
- Nutraceutical
- Cosmetic
"""

from app.classification.tree import (
    classify_formulation,
    get_next_question,
    CLASSIFICATION_CITATIONS,
    QUESTIONS,
)

__all__ = [
    "classify_formulation",
    "get_next_question",
    "CLASSIFICATION_CITATIONS",
    "QUESTIONS",
]
