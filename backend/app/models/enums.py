import enum


class UserRole(str, enum.Enum):
    CITIZEN = "CITIZEN"
    OFFICER = "OFFICER"
    ADMIN = "ADMIN"


class ProcessingStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    DONE = "DONE"
    FAILED = "FAILED"


class ClassificationSource(str, enum.Enum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    BOTH = "BOTH"


class Severity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IssueStatus(str, enum.Enum):
    NEW = "NEW"
    UNDER_REVIEW = "UNDER_REVIEW"
    CLASSIFIED = "CLASSIFIED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    VERIFIED = "VERIFIED"
    CLOSED = "CLOSED"
    DUPLICATE = "DUPLICATE"
    REJECTED = "REJECTED"
    ESCALATED = "ESCALATED"
    REOPENED = "REOPENED"


class ContactType(str, enum.Enum):
    HELPLINE = "HELPLINE"
    EMERGENCY = "EMERGENCY"
    EMAIL = "EMAIL"
    WEBSITE = "WEBSITE"
    COMPLAINT_PORTAL = "COMPLAINT_PORTAL"
    LOCAL_OFFICE = "LOCAL_OFFICE"


class VerificationStatus(str, enum.Enum):
    UNVERIFIED = "UNVERIFIED"
    VERIFIED = "VERIFIED"
    STALE = "STALE"


class SourceStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    FAILING = "FAILING"
    DISABLED = "DISABLED"
