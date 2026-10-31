from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleViolation, NotFoundError
from app.db.session import transaction
from app.models import Plan, PlanStatus
from app.repositories import PlanRepository
from app.schemas.plan import PlanCreate, PlanUpdate


class PlanService:
    """Manages the plan catalogue: creation, updates and activation state."""

    def __init__(self, session: Session, plans: PlanRepository) -> None:
        self.session = session
        self.plans = plans

    def create_plan(self, data: PlanCreate) -> Plan:
        self._ensure_positive_price(data.price)
        plan = Plan(**data.model_dump())
        with transaction(self.session):
            self.plans.add(plan)
        return plan

    def list_plans(self, status: PlanStatus | None = None, skip: int = 0, limit: int = 50) -> list[Plan]:
        return self.plans.list(status=status, skip=skip, limit=limit)

    def get_plan(self, plan_id: int) -> Plan:
        plan = self.plans.get(plan_id)
        if plan is None:
            raise NotFoundError(f"Plan {plan_id} not found.")
        return plan

    def update_plan(self, plan_id: int, data: PlanUpdate) -> Plan:
        """Partial update; also used to activate/deactivate a plan via `status`.
        Price changes only affect invoices generated afterwards."""
        plan = self.get_plan(plan_id)
        changes = data.model_dump(exclude_unset=True)
        if "price" in changes:
            self._ensure_positive_price(changes["price"])
        with transaction(self.session):
            for field, value in changes.items():
                setattr(plan, field, value)
        return plan

    @staticmethod
    def _ensure_positive_price(price: Decimal | None) -> None:
        if price is None or price <= 0:
            raise BusinessRuleViolation("Plan price must be greater than zero.")
