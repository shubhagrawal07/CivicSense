from app.models.enums import Severity

SEVERITY_WEIGHTS = {
    Severity.LOW: 1,
    Severity.MEDIUM: 2,
    Severity.HIGH: 3,
    Severity.CRITICAL: 4,
}
DEFAULT_SEVERITY_WEIGHT = 1

CELL_SIZE_DEGREES = 0.005


def recency_weight(age_days):
    if age_days <= 30:
        return 1.0
    if age_days <= 60:
        return 0.5
    return 0.25
