"""Domain exceptions raised by services.

They carry no HTTP knowledge; `app.core.error_handlers` maps them to status codes.
"""


class DomainError(Exception):
    code = "domain_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    code = "not_found"


class ConflictError(DomainError):
    """The request conflicts with existing state (duplicates, repeated actions)."""

    code = "conflict"


class BusinessRuleViolation(DomainError):
    """The request is well-formed but breaks a billing business rule."""

    code = "business_rule_violation"


class AppendOnlyViolation(DomainError):
    """An attempt was made to modify or delete an append-only record."""

    code = "append_only_violation"
