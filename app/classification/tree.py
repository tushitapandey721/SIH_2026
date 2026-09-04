"""Formulation classification decision tree for Ayurvedic and related healthcare products."""

from typing import Dict, Any, Optional, List

# Legal and statutory basis for each product classification category
CLASSIFICATION_CITATIONS: Dict[str, str] = {
    "classical_medicine": "Section 3(a), D&C Act + Rule 154-A(1)(a), D&C Rules",
    "proprietary_medicine": "Section 3(h), D&C Act 1940 + Rule 154-A(1)(c), D&C Rules",
    "new_drug": "Rule 158-B, D&C Rules",
    "phytopharmaceutical": "Gazette Notification G.S.R. 918(E), 30 Nov 2015",
    "nutraceutical": "Section 22, Food Safety and Standards Act 2006 + FSSAI (Health Supplements and Nutraceuticals) Regulations 2022",
    "cosmetic": "Section 3(aaa), D&C Act 1940 + Cosmetics Rules 2020",
}

# Ordered list of questions for the conversational decision tree
QUESTIONS: List[Dict[str, Any]] = [
    {
        "id": "is_first_schedule_text",
        "question": "Is the formulation/method drawn from a First-Schedule authoritative Ayurvedic text?",
        "options": [True, False],
        "help_text": "Refers to classical texts listed in the First Schedule of the Drugs and Cosmetics Act, 1940 (e.g., Charaka Samhita, Sushruta Samhita, Ayurvedic Formulary of India).",
    },
    {
        "id": "requires_new_safety_efficacy",
        "question": "Does it require new safety/efficacy proof not previously established?",
        "options": [True, False],
        "help_text": "Involves novel indications, unapproved excipients, modified dosage forms, or clinical safety studies under Rule 158-B / CT Rules.",
    },
    {
        "id": "is_standardized_plant_extract",
        "question": "Is it a standardized plant-derived extract with defined markers?",
        "options": [True, False],
        "help_text": "Purified and standardized fraction with defined quantitative markers evaluated under Phytopharmaceutical Drugs regulations.",
    },
    {
        "id": "is_food_dietary_product",
        "question": "Is it marketed primarily as a food/dietary product?",
        "options": [True, False],
        "help_text": "Governed by FSSAI regulations for health supplements, nutraceuticals, or food for special dietary use.",
    },
    {
        "id": "is_topical_cosmetic",
        "question": "Is it applied topically for cosmetic (non-therapeutic) purposes?",
        "options": [True, False],
        "help_text": "Intended to be rubbed, poured, sprinkled or sprayed on human body for cleansing, beautifying, or altering appearance without therapeutic claims.",
    },
]


def _is_yes(val: Any) -> bool:
    """Helper to evaluate boolean / truthy responses."""
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val == 1
    if isinstance(val, str):
        return val.strip().lower() in ("yes", "y", "true", "1")
    return bool(val)


def classify_formulation(answers: Dict[str, Any]) -> str:
    """Classifies an Ayurvedic or related healthcare product formulation based on user answers.

    Args:
        answers: Dictionary containing boolean/string answers for decision keys:
            - is_first_schedule_text
            - requires_new_safety_efficacy
            - is_standardized_plant_extract
            - is_food_dietary_product
            - is_topical_cosmetic

    Returns:
        One of: 'classical_medicine', 'proprietary_medicine', 'new_drug',
                'phytopharmaceutical', 'nutraceutical', 'cosmetic'
    """
    if _is_yes(answers.get("is_first_schedule_text")):
        return "classical_medicine"
    if _is_yes(answers.get("requires_new_safety_efficacy")):
        return "new_drug"
    if _is_yes(answers.get("is_standardized_plant_extract")):
        return "phytopharmaceutical"
    if _is_yes(answers.get("is_food_dietary_product")):
        return "nutraceutical"
    if _is_yes(answers.get("is_topical_cosmetic")):
        return "cosmetic"
    return "proprietary_medicine"


def get_next_question(partial_answers: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Returns the next unanswered question in the decision tree, or None if classification is complete.

    Args:
        partial_answers: Dictionary of answers provided so far.

    Returns:
        Dictionary with question metadata if more input is needed, or None if category is determined.
    """
    # 1. Check First-Schedule authoritative Ayurvedic text
    if "is_first_schedule_text" not in partial_answers:
        return QUESTIONS[0]
    if _is_yes(partial_answers.get("is_first_schedule_text")):
        return None  # Resolved to classical_medicine

    # 2. Check safety/efficacy proof requirement
    if "requires_new_safety_efficacy" not in partial_answers:
        return QUESTIONS[1]
    if _is_yes(partial_answers.get("requires_new_safety_efficacy")):
        return None  # Resolved to new_drug

    # 3. Check standardized plant-derived extract
    if "is_standardized_plant_extract" not in partial_answers:
        return QUESTIONS[2]
    if _is_yes(partial_answers.get("is_standardized_plant_extract")):
        return None  # Resolved to phytopharmaceutical

    # 4. Check food/dietary product
    if "is_food_dietary_product" not in partial_answers:
        return QUESTIONS[3]
    if _is_yes(partial_answers.get("is_food_dietary_product")):
        return None  # Resolved to nutraceutical

    # 5. Check topical cosmetic purpose
    if "is_topical_cosmetic" not in partial_answers:
        return QUESTIONS[4]

    # All questions answered or final decision reached (cosmetic or proprietary_medicine)
    return None
